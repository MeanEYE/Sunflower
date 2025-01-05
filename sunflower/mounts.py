from __future__ import absolute_import

from gi.repository import Gtk, Gio, GLib, Pango
from sunflower.widgets.location_menu import Location, GenericHeader
from sunflower.gui.mounts_manager_window import MountsManagerWindow


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application):
		self._application = application
		self._mounts = {}
		self._location_menu = None
		self._window = MountsManagerWindow(self)

		# create volume monitor
		self._volume_monitor = Gio.VolumeMonitor.get()
		self._volume_monitor.connect('mount-added', self._handle_add_mount)
		self._volume_monitor.connect('volume-added', self._handle_add_volume)

	def show(self, widget, data=None):
		self._window.show_all()

	def attach_location_menu(self, location_menu):
		"""Use notification from location menu to populate list with mounts and volumes."""
		self._location_menu = location_menu
		self._location_menu.add_header(Volume, GenericHeader(_('Mounts')))

		# populate location list with volumes on this machine
		automount = self._application.options.section('operations').get('automount_start')
		for volume in self._volume_monitor.get_volumes():
			self._location_menu.add_location(widget := Volume(self, volume))

			if (mount := volume.get_mount()) is not None:
				# volume is already mounted, map it locally
				root_path = mount.get_root().get_path()
				self._mounts[root_path] = widget

			elif automount and volume.can_mount():
				volume.mount(Gio.MountMountFlags.NONE, None, None, self._handle_mount_finish, None)

		# populate location list with remaining mounts without volume
		for mount in self._volume_monitor.get_mounts():
			if (root_path := mount.get_root().get_path()) in self._mounts:
				continue
			self._location_menu.add_location(widget := Mount(self, mount))
			self._mounts[root_path] = widget

	def _handle_add_volume(self, monitor, volume):
		"""Event called when new volume is connected."""
		self._location_menu.add_location(widget := Volume(self, volume))
		self._mounts[widget.get_location()] = widget

		# automount volume if needed
		automount_insert = self._application.options.section('operations').get('automount_insert')
		if automount_insert and volume.can_mount() and volume.get_mount() is None:
			volume.mount(Gio.MountMountFlags.NONE, None, None, self._handle_mount_finish, None)

	def _handle_remove_volume(self, widget, volume):
		"""Event called when volume is removed."""
		root_path = widget.get_location()
		del self._mounts[root_path]
		self._location_menu.remove_location(widget)

	def _handle_add_mount(self, monitor, mount):
		"""Handle mount added to the system."""
		root_path = mount.get_root().get_path()
		if root_path in self._mounts:
			return

		self._location_menu.add_location(widget := Mount(self, mount))
		self._mounts[root_path] = widget

	def _handle_unmount_mount(self, widget, mount):
		"""Event called when mount without volume has been unmounted."""
		root_path = widget.get_location()
		del self._mounts[root_path]
		self._location_menu.remove_location(widget)

	def _handle_mount_finish(self, mount, result, data=None):
		"""Callback for mount events."""
		try:
			mount.mount_finish(result)

		except GLib.Error as error:
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Unable to finish mounting:\n{}'.format(error.message))
								)
			dialog.run()
			dialog.destroy()

	def _handle_unmount_finish(self, mount, result, data=None):
		"""Callback for unmount events."""
		try:
			mount.unmount_finish(result)

		except GLib.Error as error:
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Unable to finish unmounting:\n{}'.format(error.message))
								)
			dialog.run()
			dialog.destroy()

	def _handle_eject_finish(self, volume, result, data=None):
		"""Callback for eject event."""
		try:
			volume.eject_finish(result)

		except GLib.Error as error:
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Unable to finish ejecting:\n{}'.format(error.message))
								)
			dialog.run()
			dialog.destroy()

	def mount(self, volume):
		"""Perform volume mount."""
		if volume.can_mount() and volume.get_mount() is None:
			volume.mount(Gio.MountMountFlags.NONE, None, None, self._handle_mount_finish, None)

		else:
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Selected volume can not be mounted.')
								)
			dialog.run()
			dialog.destroy()

	def unmount(self, mount):
		"""Perform unmounting."""
		if mount.can_unmount():
			mount.unmount(Gio.MountUnmountFlags.FORCE, None, self._handle_unmount_finish, None)

		else:
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Selected mount can not be unmounted.')
								)
			dialog.run()
			dialog.destroy()

	def eject(self, volume):
		"""Perform volume ejection."""
		if volume.can_eject():
			volume.eject(Gio.MountUnmountFlags.FORCE, None, self._handle_eject_finish, None)

		else:
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Selected volume can not be ejected.')
								)
			dialog.run()
			dialog.destroy()

	def create_extensions(self):
		"""Create mounts manager extensions"""
		self._window.create_extensions()

	def is_mounted(self, path):
		"""Check if specified path is mounted"""
		pass

	def mount_path(self, path):
		"""Mount specified path if extensions know how"""
		pass


class Mount(Location):
	"""Generic mount handling class used with mounts without
	associated volumes. These are usually remote mounts and
	locations."""

	def __init__(self, manager, mount):
		Location.__init__(self)
		self._manager = manager
		self._mount = mount

		# interface elements
		self._icon = None
		self._title = None
		self._unmount = None

		# create user interface
		self._create_interface()
		self.show_all()

		# connect events
		self._mount.connect('changed', self.__handle_change)
		self._mount.connect('unmounted', self.__handle_unmount)

	def __handle_change(self, mount):
		"""Handle mount change."""
		self._unmount_button.set_visible(mount is not None and mount.can_unmount())
		self._eject_button.set_visible(mount.can_eject())

	def __handle_unmount(self, mount):
		"""Handle mount remove event."""
		self._manager._handle_unmount_mount(self, mount)

	def __handle_unmount_click(self, widget, data=None):
		"""Handle clicking on unmount button."""
		if self._mount:
			self._manager.unmount(self._mount)

	def __handle_eject_click(self, widget, data=None):
		"""Handle clicking on eject button."""
		self._manager.eject(self._mount)

	def _create_interface(self):
		"""Create interface for the widget to display."""
		container = Gtk.HBox.new(False, 5)
		container.set_border_width(5)

		# create volume icon
		self._icon = Gtk.Image.new_from_gicon(
				self._mount.get_icon(),
				Gtk.IconSize.LARGE_TOOLBAR
				)

		# create volume name label
		self._title = Gtk.Label.new(self._mount.get_name())
		self._title.set_alignment(0, 0.5)
		self._title.set_ellipsize(Pango.EllipsizeMode.END)

		# pack interface
		container.pack_start(self._icon, False, False, 0)
		container.pack_start(self._title, True, True, 0)

		# create buttons
		self._unmount_button = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic', Gtk.IconSize.BUTTON)
		self._unmount_button.connect('clicked', self.__handle_unmount_click)
		self._unmount_button.set_tooltip_text(_('Unmount'))
		self._unmount_button.set_property('no-show-all', True)
		container.pack_start(self._unmount_button, False, False, 0)

		self._eject_button = Gtk.Button.new_from_icon_name('media-eject-symbolic', Gtk.IconSize.BUTTON)
		self._eject_button.connect('clicked', self.__handle_eject_click)
		self._eject_button.set_tooltip_text(_('Eject'))
		self._eject_button.set_property('no-show-all', True)
		container.pack_start(self._eject_button, False, False, 0)

		# apply button visibility
		self.__handle_change(self._mount)

		self.add(container)

	def get_location(self):
		"""Return location path."""
		return self._mount.get_root().get_path()


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
		self._volume.connect('changed', self.__handle_change)
		self._volume.connect('removed', self.__handle_remove)

	def __handle_change(self, volume):
		"""Handle volume change."""
		mount = self._volume.get_mount()
		self._unmount_button.set_visible(mount is not None and mount.can_unmount())
		self._mount_button.set_visible(mount is None and self._volume.can_mount())
		self._eject_button.set_visible(self._volume.can_eject())

	def __handle_remove(self, volume):
		"""Handle volume remove event."""
		self._manager._handle_remove_volume(self, volume)

	def __handle_mount_click(self, widget, data=None):
		"""Handle clicking on mount button."""
		self._manager.mount(self._volume)

	def __handle_unmount_click(self, widget, data=None):
		"""Handle clicking on unmount button."""
		mount = self._volume.get_mount()
		if mount:
			self._manager.unmount(mount)

	def __handle_eject_click(self, widget, data=None):
		"""Handle clicking on eject button."""
		self._manager.eject(self._volume)

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

		# create buttons
		self._unmount_button = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic', Gtk.IconSize.BUTTON)
		self._unmount_button.connect('clicked', self.__handle_unmount_click)
		self._unmount_button.set_tooltip_text(_('Unmount'))
		self._unmount_button.set_property('no-show-all', True)
		container.pack_start(self._unmount_button, False, False, 0)

		self._mount_button = Gtk.Button.new_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.BUTTON)
		self._mount_button.connect('clicked', self.__handle_mount_click)
		self._mount_button.set_tooltip_text(_('Mount'))
		self._mount_button.set_property('no-show-all', True)
		container.pack_start(self._mount_button, False, False, 0)

		self._eject_button = Gtk.Button.new_from_icon_name('media-eject-symbolic', Gtk.IconSize.BUTTON)
		self._eject_button.connect('clicked', self.__handle_eject_click)
		self._eject_button.set_tooltip_text(_('Eject'))
		self._eject_button.set_property('no-show-all', True)
		container.pack_start(self._eject_button, False, False, 0)

		# apply button visibility
		self.__handle_change(self._volume)

		self.add(container)

	def get_location(self):
		"""Return location path."""
		result = None
		mount = self._volume.get_mount()

		if mount:
			root = mount.get_root()
			result = root.get_path()

		return result
