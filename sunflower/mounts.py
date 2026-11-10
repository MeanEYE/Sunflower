from __future__ import absolute_import

from gi.repository import Gtk, Gio, GLib, Pango
from sunflower.widgets.location_menu import Location, GenericHeader
from sunflower.gui.mounts_manager_window import MountsManagerWindow


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application):
		self._application = application
		self._volumes = []
		self._mounts = []
		self._location_menu = None
		self._window = MountsManagerWindow(self)

		# create volume monitor
		self._volume_monitor = Gio.VolumeMonitor.get()
		self._volume_monitor.connect('mount-added', self._handle_add_mount)
		self._volume_monitor.connect('volume-added', self._handle_add_volume)

	def show(self, widget, data=None):
		if Gtk.get_major_version() == 3:
			self._window.show_all()

		else:
			self._window.show()

	def attach_location_menu(self, location_menu):
		"""Use notification from location menu to populate list with mounts and volumes."""
		self._location_menu = location_menu
		self._location_menu.add_header(Volume, GenericHeader(_('Mounts')))

		# populate location list with volumes on this machine
		automount = self._application.options.section('operations').get('automount_start')
		for volume in self._volume_monitor.get_volumes():
			self._add_volume(volume)

			if automount and volume.can_mount() and volume.get_mount() is None:
				volume.mount(Gio.MountMountFlags.NONE, None, None, self._handle_mount_finish, None)

		# populate location list with remaining mounts without volume
		for mount in self._volume_monitor.get_mounts():
			self._add_mount(mount)

	def _add_volume(self, volume):
		"""Add volume to location list, unless it's already there."""
		if any(widget.get_volume() == volume for widget in self._volumes):
			return

		self._location_menu.add_location(widget := Volume(self, volume))
		self._volumes.append(widget)

	def _add_mount(self, mount):
		"""Add mount to location list, unless it's already represented.

		Volumes and mounts are tracked by their objects and not paths, as
		path is not known for unmounted volumes and some remote mounts.

		"""
		# mounts of known volumes are represented by volume itself
		if (volume := mount.get_volume()) is not None \
		and any(widget.get_volume() == volume for widget in self._volumes):
			return

		# shadowed mounts are not supposed to be visible to the user
		if mount.is_shadowed():
			return

		uri = mount.get_root().get_uri()
		if any(widget.get_mount() == mount or widget.get_uri() == uri for widget in self._mounts):
			return

		self._location_menu.add_location(widget := Mount(self, mount))
		self._mounts.append(widget)

	def _handle_add_volume(self, monitor, volume):
		"""Event called when new volume is connected."""
		self._add_volume(volume)

		# volume can show up after its mount, which is now redundant
		if (mount := volume.get_mount()) is not None:
			for widget in [widget for widget in self._mounts if widget.get_mount() == mount]:
				self._handle_unmount_mount(widget, mount)

		# automount volume if needed
		automount_insert = self._application.options.section('operations').get('automount_insert')
		if automount_insert and volume.can_mount() and volume.get_mount() is None:
			volume.mount(Gio.MountMountFlags.NONE, None, None, self._handle_mount_finish, None)

	def _handle_remove_volume(self, widget, volume):
		"""Event called when volume is removed."""
		if widget not in self._volumes:
			return

		self._volumes.remove(widget)
		self._location_menu.remove_location(widget)

	def _handle_add_mount(self, monitor, mount):
		"""Handle mount added to the system."""
		self._add_mount(mount)

	def _handle_unmount_mount(self, widget, mount):
		"""Event called when mount without volume has been unmounted."""
		if widget not in self._mounts:
			return

		self._mounts.remove(widget)
		self._location_menu.remove_location(widget)

	def _handle_mount_finish(self, mount, result, data=None):
		"""Callback for mount events."""
		try:
			mount.mount_finish(result)

		except GLib.Error as error:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.WARNING,
									buttons=Gtk.ButtonsType.OK,
									text=_('Unable to finish mounting:\n{}'.format(error.message))
								)
			run_dialog(dialog)
			dialog.destroy()

	def _handle_unmount_finish(self, mount, result, data=None):
		"""Callback for unmount events."""
		try:
			mount.unmount_finish(result)

		except GLib.Error as error:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.WARNING,
									buttons=Gtk.ButtonsType.OK,
									text=_('Unable to finish unmounting:\n{}'.format(error.message))
								)
			run_dialog(dialog)
			dialog.destroy()

	def _handle_eject_finish(self, volume, result, data=None):
		"""Callback for eject event."""
		try:
			volume.eject_finish(result)

		except GLib.Error as error:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.WARNING,
									buttons=Gtk.ButtonsType.OK,
									text=_('Unable to finish ejecting:\n{}'.format(error.message))
								)
			run_dialog(dialog)
			dialog.destroy()

	def mount(self, volume):
		"""Perform volume mount."""
		if volume.can_mount() and volume.get_mount() is None:
			volume.mount(Gio.MountMountFlags.NONE, None, None, self._handle_mount_finish, None)

		else:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.WARNING,
									buttons=Gtk.ButtonsType.OK,
									text=_('Selected volume can not be mounted.')
								)
			run_dialog(dialog)
			dialog.destroy()

	def unmount(self, mount):
		"""Perform unmounting."""
		if mount.can_unmount():
			mount.unmount(Gio.MountUnmountFlags.FORCE, None, self._handle_unmount_finish, None)

		else:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.WARNING,
									buttons=Gtk.ButtonsType.OK,
									text=_('Selected mount can not be unmounted.')
								)
			run_dialog(dialog)
			dialog.destroy()

	def eject(self, volume):
		"""Perform volume ejection."""
		if volume.can_eject():
			volume.eject(Gio.MountUnmountFlags.FORCE, None, self._handle_eject_finish, None)

		else:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.WARNING,
									buttons=Gtk.ButtonsType.OK,
									text=_('Selected volume can not be ejected.')
								)
			run_dialog(dialog)
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
		if Gtk.get_major_version() == 3:
			self.show_all()

		else:
			self.show()

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
		container = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
		set_border_width(container, 5)

		# create volume icon
		if Gtk.get_major_version() == 3:
			self._icon = Gtk.Image.new_from_gicon(
					self._mount.get_icon(),
					Gtk.IconSize.LARGE_TOOLBAR
					)

		else:
			# GTK 4 images take no size, icon scales through its pixel size
			self._icon = Gtk.Image.new_from_gicon(self._mount.get_icon())
			self._icon.set_pixel_size(24)

		# create volume name label
		self._title = Gtk.Label.new(self._mount.get_name())
		self._title.set_xalign(0)
		self._title.set_yalign(0.5)
		self._title.set_ellipsize(Pango.EllipsizeMode.END)

		# pack interface
		if Gtk.get_major_version() == 3:
			container.pack_start(self._icon, False, False, 0)
			container.pack_start(self._title, True, True, 0)

		else:
			container.append(self._icon)
			self._title.set_hexpand(True)
			container.append(self._title)

		# create buttons
		if Gtk.get_major_version() == 3:
			self._unmount_button = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic', Gtk.IconSize.BUTTON)

		else:
			self._unmount_button = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic')
		self._unmount_button.connect('clicked', self.__handle_unmount_click)
		self._unmount_button.set_tooltip_text(_('Unmount'))
		if Gtk.get_major_version() == 3:
			self._unmount_button.set_property('no-show-all', True)

			container.pack_start(self._unmount_button, False, False, 0)

			self._eject_button = Gtk.Button.new_from_icon_name('media-eject-symbolic', Gtk.IconSize.BUTTON)

		else:
			self._unmount_button.hide()

			container.append(self._unmount_button)

			self._eject_button = Gtk.Button.new_from_icon_name('media-eject-symbolic')
		self._eject_button.connect('clicked', self.__handle_eject_click)
		self._eject_button.set_tooltip_text(_('Eject'))
		if Gtk.get_major_version() == 3:
			self._eject_button.set_property('no-show-all', True)

			container.pack_start(self._eject_button, False, False, 0)

		else:
			self._eject_button.hide()

			container.append(self._eject_button)

		# apply button visibility
		self.__handle_change(self._mount)

		if Gtk.get_major_version() == 3:
			self.add(container)

		else:
			self.set_child(container)

	def get_location(self):
		"""Return location path."""
		return self._mount.get_root().get_path()

	def get_mount(self):
		"""Return mount object represented by this location."""
		return self._mount

	def get_uri(self):
		"""Return URI of the mount root."""
		return self._mount.get_root().get_uri()


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
		if Gtk.get_major_version() == 3:
			self.show_all()

		else:
			self.show()

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
		container = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
		set_border_width(container, 5)

		# create volume icon
		if Gtk.get_major_version() == 3:
			self._icon = Gtk.Image.new_from_gicon(
					self._volume.get_icon(),
					Gtk.IconSize.LARGE_TOOLBAR
					)

		else:
			# GTK 4 images take no size, icon scales through its pixel size
			self._icon = Gtk.Image.new_from_gicon(self._volume.get_icon())
			self._icon.set_pixel_size(24)

		# create volume name label
		self._title = Gtk.Label.new(self._volume.get_name())
		self._title.set_xalign(0)
		self._title.set_yalign(0.5)
		self._title.set_ellipsize(Pango.EllipsizeMode.END)

		# pack interface
		if Gtk.get_major_version() == 3:
			container.pack_start(self._icon, False, False, 0)
			container.pack_start(self._title, True, True, 0)

		else:
			container.append(self._icon)
			self._title.set_hexpand(True)
			container.append(self._title)

		# create buttons
		if Gtk.get_major_version() == 3:
			self._unmount_button = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic', Gtk.IconSize.BUTTON)

		else:
			self._unmount_button = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic')
		self._unmount_button.connect('clicked', self.__handle_unmount_click)
		self._unmount_button.set_tooltip_text(_('Unmount'))
		if Gtk.get_major_version() == 3:
			self._unmount_button.set_property('no-show-all', True)

			container.pack_start(self._unmount_button, False, False, 0)

			self._mount_button = Gtk.Button.new_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.BUTTON)

		else:
			self._unmount_button.hide()

			container.append(self._unmount_button)

			self._mount_button = Gtk.Button.new_from_icon_name('media-playback-start-symbolic')
		self._mount_button.connect('clicked', self.__handle_mount_click)
		self._mount_button.set_tooltip_text(_('Mount'))
		if Gtk.get_major_version() == 3:
			self._mount_button.set_property('no-show-all', True)

			container.pack_start(self._mount_button, False, False, 0)

			self._eject_button = Gtk.Button.new_from_icon_name('media-eject-symbolic', Gtk.IconSize.BUTTON)

		else:
			self._mount_button.hide()

			container.append(self._mount_button)

			self._eject_button = Gtk.Button.new_from_icon_name('media-eject-symbolic')
		self._eject_button.connect('clicked', self.__handle_eject_click)
		self._eject_button.set_tooltip_text(_('Eject'))
		if Gtk.get_major_version() == 3:
			self._eject_button.set_property('no-show-all', True)

			container.pack_start(self._eject_button, False, False, 0)

		else:
			self._eject_button.hide()

			container.append(self._eject_button)

		# apply button visibility
		self.__handle_change(self._volume)

		if Gtk.get_major_version() == 3:
			self.add(container)

		else:
			self.set_child(container)

	def get_location(self):
		"""Return location path."""
		result = None
		mount = self._volume.get_mount()

		if mount:
			root = mount.get_root()
			result = root.get_path()

		return result

	def get_volume(self):
		"""Return volume object represented by this location."""
		return self._volume
