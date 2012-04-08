import gtk

from gio import VolumeMonitor
from gui.mounts_manager_window import MountsManagerWindow


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application):
		self._application = application
		self._menu = None
		self._menu_unmount = None
		self._menu_item = None

		# create user interface
		self.window = MountsManagerWindow(self)

		# create volume monitor
		self._volume_monitor = VolumeMonitor()
		self._volume_monitor.connect('mount-added', self._add_mount)
		self._volume_monitor.connect('mount-removed', self._remove_mount)
		self._volume_monitor.connect('volume-added', self._add_volume)
		self._volume_monitor.connect('volume-removed', self._remove_volume)

	def _populate_list(self):
		"""Populate mount/volume list"""
		# get list of volumes
		for volume in self._volume_monitor.get_volumes():
			self.window._add_volume(volume)

		# get list of mounted volumes
		for mount in self._volume_monitor.get_mounts():
			self._add_mount(self._volume_monitor, mount)

		# update menu item visibility based on mount count
		self._menu_updated()

	def _get_extension_for_selected_item(self):
		"""Get extension for selected item in list, if possible"""
		pass

	def _add_mount(self, monitor, mount):
		"""Catch volume-mounted signal and update mounts menu"""
		icon_names = mount.get_icon().to_string()
		mount_icon = self._application.icon_manager.get_mount_icon_name(icon_names)
		mount_uri = mount.get_root().get_uri()
		volume = mount.get_volume()

		# if mount has volume, set mounted flag
		if volume is not None:
			uuid = volume.get_uuid()
			self.window._volume_mounted(volume)

		# add mount to the list
		self.window.add_mount(mount_icon, mount.get_name(), mount_uri)

		# add bookmark menu item
		self._add_item(
				mount.get_name(),
				mount_uri,
				mount_icon
			)

		# add unmount menu item
		self._add_unmount_item(
				mount.get_name(),
				mount_uri,
				mount_icon
			)

		# notify system about menu update
		self._menu_updated()

	def _remove_mount(self, monitor, mount):
		"""Remove volume menu item from the mounts menu"""
		volume = mount.get_volume()
		mount_uri = mount.get_root().get_uri()

		# update volume list if possible
		if volume is not None:
			self.window._volume_unmounted(volume)

		# remove mount from list
		self.window.remove_mount(mount_uri)

		# remove item from menus
		self._remove_item(mount_uri)

		# notify system about menu update
		self._menu_updated()

	def _add_volume(self, monitor, volume):
		"""Event called when new volume is connected"""
		self.window._add_volume(volume)

	def _remove_volume(self, monitor, volume):
		"""Event called when volume is removed/unmounted"""
		self.window._remove_volume(volume)

	def _menu_updated(self):
		"""Method called whenever menu is updated"""
		has_mounts = len(self._menu.get_children()) > 1
		self._menu_item_no_mounts.set_visible(not has_mounts)
		self._menu_item_no_mounts2.set_visible(not has_mounts)

	def _add_item(self, text, uri, icon):
		"""Add new menu item to the list"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_always_show_image(True)
		menu_item.set_data('path', uri)
		menu_item.connect('activate', self._application._handle_bookmarks_click)
		menu_item.show()

		self._menu.append(menu_item)

	def _add_unmount_item(self, text, uri, icon):
		"""Add new menu item used for unmounting"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_always_show_image(True)
		menu_item.set_data('uri', uri)
		menu_item.connect('activate', self._unmount_item)
		menu_item.show()

		self._menu_unmount.append(menu_item)

	def _remove_item(self, mount_point):
		"""Remove item based on device name"""
		for item in self._menu.get_children():
			if item.get_data('uri') == mount_point: self._menu.remove(item)

		for item in self._menu_unmount.get_children():
			if item.get_data('uri') == mount_point: self._menu_unmount.remove(item)

	def _unmount_item(self, widget, data=None):
		"""Event called by the unmount menu item or unmount button from manager"""
		uri = widget.get_data('uri')

		if uri is None:
			# unmount was called by button
			pass

		else:
			# unmount was called by menu item
			for mount in self._volume_monitor.get_mounts():
				# check if this is the right mount
				if mount.get_root().get_uri() == uri:
					self._unmount(mount)
					break

	def _unmount(self, mount):
		"""Perform unmounting"""
		if mount.can_unmount():
			# we can safely unmount
			mount.unmount(self._unmount_finish)

		else:
			# print error
			dialog = gtk.MessageDialog(
									self,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_WARNING,
									gtk.BUTTONS_OK,
									_('Specified item can not be unmounted.')
								)
			dialog.run()
			dialog.destroy()

	def _unmount_finish(self, mount, result):
		"""Callback for unmount events"""
		# try to finish async unmount
		mount.unmount_finish(result)
		mount_uri = mount.get_root().get_uri()

	def _attach_menus(self):
		"""Attach mounts to menus"""
		menu_manager = self._application.menu_manager

		# get mounts menu item
		self._menu_item = self._application._menu_item_mounts

		# create mounts menu
		self._menu = gtk.Menu()
		self._menu_item.set_submenu(self._menu)

		self._menu_unmount = menu_manager.get_item_by_name('unmount_menu').get_submenu()

		# create item for usage when there are no mounts
		self._menu_item_no_mounts = gtk.MenuItem(label=_('Mount list is empty'))
		self._menu_item_no_mounts.set_sensitive(False)
		self._menu_item_no_mounts.set_property('no-show-all', True)
		self._menu.append(self._menu_item_no_mounts)

		self._menu_item_no_mounts2 = menu_manager.get_item_by_name('mount_list_empty')
		self._menu_item_no_mounts2.set_property('no-show-all', True)

		self._populate_list()

	def show(self, widget=None, data=None):
		"""Show mounts manager window"""
		self.window.show_all()
