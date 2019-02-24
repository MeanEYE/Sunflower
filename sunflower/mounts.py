from __future__ import absolute_import

from gi.repository import Gtk, Gio, GLib, Pango
from sunflower.widgets.location_menu import Location, GenericHeader


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application):
		self._application = application
		self._mounts = {}
		self._location_menu = None

		# create volume monitor
		self._volume_monitor = Gio.VolumeMonitor.get()
		self._volume_monitor.connect('volume-added', self._handle_add_volume)

	def attach_location_menu(self, location_menu):
		"""Use notification from location menu to populate list with mounts and volumes."""
		self._location_menu = location_menu
		self._location_menu.add_header(Volume, GenericHeader(_('Mounts')))

		for volume in self._volume_monitor.get_volumes():
			self._location_menu.add_location(Volume(self, volume))

		# get list of volumes
		# volumes = self._volume_monitor.get_volumes()
		# volumes = map(lambda volume: volume.get_activation_root(), volumes)
		# volumes = [uri for uri in volumes if uri is not None]
		# mounts_added.extend(volumes)

		# # get list of mounted volumes
		# mounts = self._volume_monitor.get_mounts()
		# mounts = map(lambda mount: mount.get_root().get_uri(), mounts)
		# mounts = [uri for uri in mounts if uri is not None and uri not in mounts_added]
		# mounts_added.extend(mounts)

	def _handle_add_volume(self, monitor, volume):
		"""Event called when new volume is connected."""
		self._location_menu.add_location(Volume(self, volume))

	def _handle_remove_volume(self, widget, volume):
		"""Event called when volume is removed."""
		self._location_menu.remove_location(widget)

	def __handle_unmount_finish(self, mount, result, user_data=None):
		"""Callback for unmount events"""
		mount.unmount_finish(result)

	def unmount(self, mount):
		"""Perform unmounting"""
		if mount.can_unmount():
			# we can safely unmount
			mount.unmount(Gio.MountUnmountFlags.FORCE, None, self.__handle_unmount_finish, None)

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

	def create_extensions(self):
		"""Create mounts manager extensions"""
		pass

	def is_mounted(self, path):
		"""Check if specified path is mounted"""
		pass

	def mount_path(self, path):
		"""Mount specified path if extensions know how"""
		pass


class Volume(Location):
	"""Generic volume handling class."""

	def __init__(self, manager, volume):
		Location.__init__(self)
		self._manager = manager
		self._volume = volume

		# interface elements
		self._icon = None
		self._title = None
		self._unmount = None

		# create user interface
		self._create_interface()
		self.show_all()

		# connect events
		self._volume.connect('removed', self.__handle_remove)

	def __handle_remove(self, volume):
		"""Handle volume remove event."""
		self._manager._handle_remove_volume(self, volume)

	def _create_interface(self):
		"""Create interface for the widget to display."""
		container = Gtk.HBox.new(False, 5)
		container.set_border_width(5)

		# create volume icon
		self._icon = Gtk.Image.new_from_gicon(
					self._volume.get_icon(),
					Gtk.IconSize.LARGE_TOOLBAR
				)

		# create volume name label
		self._title = Gtk.Label.new(self._volume.get_name())
		self._title.set_alignment(0, 0.5)
		self._title.set_ellipsize(Pango.EllipsizeMode.END)

		# pack interface
		container.pack_start(self._icon, False, False, 0)
		container.pack_start(self._title, True, True, 0)

		# create unmount button
		if self._volume.can_eject():
			self._unmount = Gtk.Button.new_from_icon_name('media-eject-symbolic', Gtk.IconSize.BUTTON)
			container.pack_start(self._unmount, False, False, 0)

		self.add(container)

	def get_location(self):
		"""Return location path."""
		result = None
		mount = self._volume.get_mount()

		if mount:
			root = mount.get_root()
			result = root.get_uri()
			root.unref()

		return result

