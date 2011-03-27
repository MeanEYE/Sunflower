import gtk

from urlparse import urlparse
from gio import VolumeMonitor

COL_DEVICE		= 0
COL_MOUNT_POINT = 1
COL_FILESYSTEM	= 2

class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application, menu_item):
		self._application = application
		self._menu_item = menu_item

		self._menu = gtk.Menu()
		self._menu_item.set_submenu(self._menu)

		# gnome volume monitor
		self._volume_monitor = VolumeMonitor()
		self._volume_monitor.connect('mount-added', self._add_mount)
		self._volume_monitor.connect('mount-removed', self._remove_mount)

		# get initial list of mounted volumes
		for mount in self._volume_monitor.get_mounts():
			self._add_mount(self._volume_monitor, mount)

	def _add_mount(self, monitor, mount):
		"""Catch volume-mounted singnal and update mounts menu"""
		icon_names = mount.get_icon().to_string()
		mount_icon = self._application.icon_manager.get_mount_icon_name(icon_names)

		self._add_item(
	            mount.get_name(),
	            mount.get_root().get_path(),
	            mount_icon
	        )

	def _remove_mount(self, monitor, mount):
		"""Remove volume menu item from the mounts menu"""
		self._remove_item(mount.get_root().get_path())

	def _add_item(self, text, path, icon):
		"""Add new menu item to the list"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_data('path', path)
		menu_item.connect('activate', self._application._handle_bookmarks_click)
		menu_item.show()

		self._menu.append(menu_item)

	def _remove_item(self, mount_point):
		"""Remove item based on device name"""
		for item in self._menu.get_children():
			if item.get_data('path') == mount_point: self._menu.remove(item)
