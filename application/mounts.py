import gtk

from gio import VolumeMonitor

COL_DEVICE		= 0
COL_MOUNT_POINT = 1
COL_FILESYSTEM	= 2


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application, menu_item):
		self._application = application
		self._menu_item = menu_item

		menu_manager = self._application.menu_manager

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

		# gnome volume monitor
		self._volume_monitor = VolumeMonitor()
		self._volume_monitor.connect('mount-added', self._add_mount)
		self._volume_monitor.connect('mount-removed', self._remove_mount)

		# get initial list of mounted volumes
		for mount in self._volume_monitor.get_mounts():
			self._add_mount(self._volume_monitor, mount)

		self._menu_updated()

	def _add_mount(self, monitor, mount):
		"""Catch volume-mounted singnal and update mounts menu"""
		icon_names = mount.get_icon().to_string()
		mount_icon = self._application.icon_manager.get_mount_icon_name(icon_names)

		# add bookmark menu item
		self._add_item(
				mount.get_name(),
				mount.get_root().get_path(),
				mount_icon
			)

		# add unmount menu item
		self._add_unmount_item(
				mount.get_name(),
				mount.get_root().get_path(),
				mount_icon
			)

		# notify system about menu update
		self._menu_updated()

	def _remove_mount(self, monitor, mount):
		"""Remove volume menu item from the mounts menu"""
		self._remove_item(mount.get_root().get_path())

		# notify system about menu update
		self._menu_updated()

	def _menu_updated(self):
		"""Method called whenever menu is updated"""
		has_mounts = len(self._menu.get_children()) > 1
		self._menu_item_no_mounts.set_visible(not has_mounts)
		self._menu_item_no_mounts2.set_visible(not has_mounts)

	def _add_item(self, text, path, icon):
		"""Add new menu item to the list"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_always_show_image(True)
		menu_item.set_data('path', path)
		menu_item.connect('activate', self._application._handle_bookmarks_click)
		menu_item.show()

		self._menu.append(menu_item)

	def _add_unmount_item(self, text, path, icon):
		"""Add new menu item used for unmounting"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_always_show_image(True)
		menu_item.set_data('path', path)
		menu_item.connect('activate', self._unmount_item)
		menu_item.show()

		self._menu_unmount.append(menu_item)

	def _remove_item(self, mount_point):
		"""Remove item based on device name"""
		for item in self._menu.get_children():
			if item.get_data('path') == mount_point: self._menu.remove(item)

		for item in self._menu_unmount.get_children():
			if item.get_data('path') == mount_point: self._menu_unmount.remove(item)

	def _unmount_item(self, widget, data=None):
		"""Unmount item"""
		path = widget.get_data('path')

		for mount in self._volume_monitor.get_mounts():
			# check if this is the right mount
			if mount.get_root().get_path() == path:
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
									_("Specified item can not be unmounted.")
								)
			dialog.run()
			dialog.destroy()

	def _unmount_finish(self, mount, result):
		"""Callback for unmount events"""
		try:
			# try to finish async unmount
			mount.unmount_finish(result)

		except:
			pass
