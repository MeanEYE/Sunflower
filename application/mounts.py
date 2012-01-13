import gtk

from gio import VolumeMonitor


class Column:
	ICON = 0
	NAME = 1
	CONFIGURATION = 2
	PATH = 3
	MOUNTED = 4


class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application):
		self._application = application
		self._menu = None
		self._menu_unmount = None
		self._menu_item = None
		self._volumes_iter = None

		self.window = None

		# create volume monitor
		self._volume_monitor = VolumeMonitor()
		self._volume_monitor.connect('mount-added', self._add_mount)
		self._volume_monitor.connect('mount-removed', self._remove_mount)

		# create user interface
		self.__create_interface()

	def __create_interface(self):
		"""Initialize user interface"""
		# create mount manager window
		self.window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
		
		# configure window
		self.window.set_title(_('Mount manager'))
		self.window.set_default_size(400, 240)
		self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.window.set_skip_taskbar_hint(True)
		self.window.set_modal(True)
		self.window.set_transient_for(self._application)
		self.window.set_wmclass('Sunflower', 'Sunflower')
		self.window.set_border_width(7)

		self.window.connect('delete-event', self._hide)
		
		# create user interface
		vbox = gtk.VBox(False, 5)
		
		hbox_controls = gtk.HBox(False, 5)
		
		# create a tree view
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		self._store = gtk.TreeStore(str, str, str, str, bool)
		
		self._list = gtk.TreeView(model=self._store)
		self._list.set_headers_visible(False)
		self._list.connect('key-press-event', self._handle_key_press)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_path = gtk.CellRendererText()

		col_name = gtk.TreeViewColumn(None)
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)

		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'text', Column.NAME)

		col_path = gtk.TreeViewColumn(None, cell_path, text=Column.PATH)

		self._list.append_column(col_name)
		self._list.append_column(col_path)

		# create controls
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._hide)
		
		image_add = gtk.Image()
		image_add.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
		button_add = gtk.Button()
		button_add.set_image(image_add)
		
		image_remove = gtk.Image()
		image_remove.set_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
		button_remove = gtk.Button()
		button_remove.set_image(image_remove)
		
		# pack user interface
		container.add(self._list)

		hbox_controls.pack_start(button_add, False, False, 0)
		hbox_controls.pack_start(button_remove, False, False, 0)
		hbox_controls.pack_end(button_close, False, False, 0)
		
		vbox.pack_start(container, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)
		
		self.window.add(vbox)

		# populate list
		self._populate_list()

	def _populate_list(self):
		"""Populate mount/volume list"""
		self._volumes_iter = self._store.append(None, ('computer', _('Volumes'), None, None, None))

	def _hide(self, widget=None, data=None):
		"""Hide mount manager"""
		self.window.hide()

		return True

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in mount manager list"""
		result = False

		if event.keyval == gtk.keysyms.Return:
			result = True

		elif event.keyval == gtk.keysyms.Escape:
			# hide window on escape
			self._hide()
			result = True

		return result

	def _add_mount(self, monitor, mount):
		"""Catch volume-mounted signal and update mounts menu"""
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

		# get initial list of mounted volumes
		for mount in self._volume_monitor.get_mounts():
			self._add_mount(self._volume_monitor, mount)

		self._menu_updated()

	def show(self, widget=None, data=None):
		"""Show mount manager"""
		self.window.show_all()
