from gi.repository import Gtk, Gio, GLib
from gui.mounts_manager_window import MountsManagerWindow


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application):
		self._application = application
		self._mounts = {}

		# create user interface
		self.window = MountsManagerWindow(self)

		# create volume monitor
		self._volume_monitor = Gio.VolumeMonitor.get()
		self._volume_monitor.connect('mount-added', self._add_mount)
		self._volume_monitor.connect('mount-removed', self._remove_mount)
		self._volume_monitor.connect('volume-added', self._add_volume)
		self._volume_monitor.connect('volume-removed', self._remove_volume)

	def _populate_list(self):
		"""Populate mount/volume list"""

		mounts_added = []

		# get list of volumes
		for volume in self._volume_monitor.get_volumes():
			self.window._add_volume(volume, startup=True)
			if volume.get_activation_root() is not None:
				mounts_added.append(volume.get_activation_root().get_uri())

		# get list of mounted volumes
		for mount in self._volume_monitor.get_mounts():
			if mount.get_root().get_uri() not in mounts_added:
				self._add_mount(self._volume_monitor, mount)
				mounts_added.append(mount.get_root().get_uri())

		# update menus
		self.window._menu_updated()

	def _add_mount(self, monitor, mount):
		"""Catch volume-mounted signal and update mounts menu"""
		icon_names = mount.get_icon().to_string()
		mount_icon = self._application.icon_manager.get_mount_icon_name(icon_names)
		mount_uri = mount.get_root().get_uri()
		volume = mount.get_volume()

		# if mount has volume, set mounted flag
		if volume is not None:
			self.window._volume_mounted(volume)

		# this gets called twice on the back of some 'mount-added' events
		if mount_uri in self._mounts:
			return

		# add mount to the list in Mount Manager window
		self.window._notify_mount_add(mount_icon, mount.get_name(), mount_uri)

		# add bookmark menu item
		self.window._add_item(
				mount.get_name(),
				mount_uri,
				mount_icon
			)

		# add unmount menu item
		self.window._add_unmount_item(
				mount.get_name(),
				mount_uri,
				mount_icon
			)

		# add mount object to local cache list
		self._mounts[mount_uri] = mount

	def _remove_mount(self, monitor, mount):
		"""Remove volume menu item from the mounts menu"""
		volume = mount.get_volume()
		mount_uri = mount.get_root().get_uri()

		# update volume list if possible
		if volume is not None:
			self.window._volume_unmounted(volume)

		# remove mount from list
		self.window._notify_mount_remove(mount_uri)

		# remove item from menus
		self.window._remove_item(mount_uri)

		# remove mount object from cache list
		if mount_uri in self._mounts:
			self._mounts.pop(mount_uri)

	def _add_volume(self, monitor, volume):
		"""Event called when new volume is connected"""
		self.window._add_volume(volume)

	def _remove_volume(self, monitor, volume):
		"""Event called when volume is removed/unmounted"""
		self.window._remove_volume(volume)

	def _unmount_item_menu_callback(self, widget, data=None):
		"""Event called by the unmount menu item or unmount button from manager"""
		uri = widget.uri

		if uri is not None:
			self._unmount(self._mounts[uri])

	def _unmount_by_uri(self, uri):
		"""Perform unmount by URI"""
		if uri in self._mounts:
			self._unmount(self._mounts[uri])

	def _unmount(self, mount):
		"""Perform unmounting"""
		if mount.can_unmount():
			# notify volume manager extension if mount is part of volume
			volume = mount.get_volume()

			if volume is not None:
				self.window._volume_unmounted(volume)

			# we can safely unmount
			mount.unmount(Gio.MountUnmountFlags.FORCE, None, self._unmount_finish, None)

		else:
			# print error
			dialog = Gtk.MessageDialog(
									self,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Specified item can not be unmounted.')
								)
			dialog.run()
			dialog.destroy()

	def _unmount_finish(self, mount, result, user_data=None):
		"""Callback for unmount events"""
		mount.unmount_finish(result)

	def _attach_menus(self):
		"""Attach mounts to menus"""
		self.window._attach_menus()

	def show(self, widget=None, data=None):
		"""Show mounts manager window"""
		self.window.show_all()
		return True

	def create_extensions(self):
		"""Create mounts manager extensions"""
		self.window.create_extensions()

	def is_mounted(self, path):
		"""Check if specified path is mounted"""
		pass

	def mount_path(self, path):
		"""Mount specified path if extensions know how"""
		pass
