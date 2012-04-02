import gtk

from plugin_base.mount_manager_extension import MountManagerExtension


class MountsColumn:
	ICON = 0
	NAME = 1
	URI = 2


class VolumesColumn:
	ICON = 0
	NAME = 1
	UUID = 2
	URI = 3
	MOUNTED = 4


class PagesColumn:
	ICON = 0
	NAME = 1
	COUNT = 2
	TAB_NUMBER = 3


class MountsManagerWindow(gtk.Window):

	def __init__(self, parent):
		# create mount manager window
		gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)

		self._parent = parent
		self._application = self._parent._application
		self._mounts = None
		self._volumes = None
		
		# configure window
		self.set_title(_('Mount manager'))
		self.set_default_size(600, 400)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(self._application)
		self.set_wmclass('Sunflower', 'Sunflower')
		self.set_border_width(7)

		self.connect('delete-event', self._hide)
		self.connect('key-press-event', self._handle_key_press)

		# create store for window list
		self._pages_store = gtk.ListStore(str, str, int, int)
		
		# create user interface
		hbox = gtk.HBox(False, 5)
		hbox_controls = gtk.HBox(False, 5)

		self._tabs = gtk.Notebook()
		self._tabs.set_show_tabs(False)
		self._tabs.set_show_border(False)
		self._tabs.connect('switch-page', self._handle_page_switch)

		# create page list
		label_container = gtk.ScrolledWindow()
		label_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		label_container.set_shadow_type(gtk.SHADOW_IN)
		label_container.set_size_request(130, -1)

		self._tab_labels = gtk.TreeView(model=self._pages_store)

		cell_icon = gtk.CellRendererPixbuf()
		cell_label = gtk.CellRendererText()
		cell_count = gtk.CellRendererText()

		col_label = gtk.TreeViewColumn(None)

		col_label.pack_start(cell_icon, False)
		col_label.pack_start(cell_label, True)
		col_label.pack_start(cell_count, False)

		col_label.add_attribute(cell_icon, 'icon-name', PagesColumn.ICON)
		col_label.add_attribute(cell_label, 'text', PagesColumn.NAME)

		self._tab_labels.append_column(col_label)
		self._tab_labels.set_headers_visible(False)
		self._tab_labels.connect('cursor-changed', self._handle_cursor_change)
		
		# create notebook pages
		self._mounts = MountsExtension(self._parent, self)
		self._volumes = VolumesExtension(self._parent, self)
		
		# pack user interface
		label_container.add(self._tab_labels)

		hbox.pack_start(label_container, False, False, 0)
		hbox.pack_start(self._tabs, True, True, 0)
		
		self.add(hbox)

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in mount manager list"""
		result = False

		if gtk.keysyms._1 <= event.keyval <= gtk.keysyms._9:
			# handle switching to page number
			page_index = event.keyval - int(gtk.keysyms._1)
			self._tabs.set_current_page(page_index)
			result = True

		elif event.keyval == gtk.keysyms.Return:
			# handle pressing return
			result = True

		elif event.keyval == gtk.keysyms.Escape:
			# hide window on escape
			self._hide()
			result = True

		return result

	def _handle_cursor_change(self, widget, data=None):
		"""Change active tab when cursor is changed"""
		selection = self._tab_labels.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			new_tab = item_list.get_value(selected_iter, PagesColumn.TAB_NUMBER)

			self._tabs.handler_block_by_func(self._handle_page_switch)
			self._tabs.set_current_page(new_tab)
			self._tabs.handler_unblock_by_func(self._handle_page_switch)

	def _handle_page_switch(self, widget, page, page_num, data=None):
		"""Handle changing page without user interaction"""
		self._tab_labels.handler_block_by_func(self._handle_cursor_change)
		self._tab_labels.set_cursor((page_num,))
		self._tab_labels.handler_unblock_by_func(self._handle_cursor_change)

	def _hide(self, widget=None, data=None):
		"""Hide mount manager"""
		self.hide()
		return True

	def _add_volume(self, volume):
		"""Add volume entry"""
		self._volumes.add_volume(volume)

	def _remove_volume(self, uuid):
		"""Remove volume entry"""
		self._volumes.remove_volume(uuid)

	def _volume_mounted(self, uuid, path):
		"""Mark volume as mounted"""
		self._volumes.volume_mounted(uuid, path)

	def _volume_unmounted(self, uuid):
		"""Mark volume as unmounted"""
		self._volumes.volume_unmounted(uuid)

	def add_page(self, icon_name, title, container, extension):
		"""Create new page in mounts manager with specified parameters.
		
		This method provides easy way to extend mounts manager by adding container
		of your choice to notebook presented to users. Extension parameter must be class
		descendant of MountManagerExtension.

		"""
		# add tab to store
		tab_number = self._tabs.get_n_pages()
		self._pages_store.append((icon_name, title, 0, tab_number))

		# assign extension to container
		container.set_data('extension', extension)

		# append new page
		self._tabs.append_page(container)

	def add_mount(self, icon, name, uri):
		"""Add mount entry"""
		self._mounts.add_mount(icon, name, uri)

	def remove_mount(self, uri):
		"""Remove mount entry"""
		self._mounts.remove_mount(uri)


class MountsExtension(MountManagerExtension):
	"""Extension that provides list of all mounted resources"""
	
	def __init__(self, parent, window):
		MountManagerExtension.__init__(self, parent, window)

		# create store for mounts
		self._store = gtk.ListStore(str, str, str)

		# create interface
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		self._list = gtk.TreeView(model=self._store)
		self._list.set_show_expanders(True)
		self._list.set_search_column(MountsColumn.NAME)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_path = gtk.CellRendererText()

		col_name = gtk.TreeViewColumn(_('Name'))
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.set_expand(True)

		col_name.add_attribute(cell_icon, 'icon-name', MountsColumn.ICON)
		col_name.add_attribute(cell_name, 'markup', MountsColumn.NAME)

		col_path = gtk.TreeViewColumn(_('Path'), cell_path, text=MountsColumn.URI)

		self._list.append_column(col_name)
		self._list.append_column(col_path)

		# create controls
		image_jump = gtk.Image()
		image_jump.set_from_icon_name(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
		button_jump = gtk.Button()
		button_jump.set_image(image_jump)
		button_jump.set_label(_('Open'))
		button_jump.set_can_default(True)
		#button_jump.connect('clicked', self._change_path)

		image_new_tab = gtk.Image()
		image_new_tab.set_from_icon_name('tab-new', gtk.ICON_SIZE_BUTTON)
		button_new_tab = gtk.Button()
		button_new_tab.set_image(image_new_tab)
		button_new_tab.set_label(_('Open in tab'))
		button_new_tab.set_tooltip_text(_('Open selected path in new tab'))
		#button_new_tab.connect('clicked', self._open_in_new_tab)

		button_unmount = gtk.Button()
		button_unmount.set_label(_('Unmount'))

		# pack interface
		container.add(self._list)

		self._controls.pack_end(button_jump, False, False, 0)
		self._controls.pack_end(button_new_tab, False, False, 0)
		self._controls.pack_start(button_unmount, False, False, 0)
		
		self._container.pack_start(container, True, True, 0)

		# add page to mount manager window
		self._window.add_page('harddrive', _('Mounts'), self._container, self)

	def _get_iter_by_uri(self, uri):
		"""Get mount list iter by path"""
		result = None
		
		# find iter by uuid
		for mount_row in self._store:
			if self._store.get_value(mount_row.iter, MountsColumn.URI) == path:
				result = mount_row.iter
				break

		return result

	def add_mount(self, icon, name, uri):
		"""Add mount to the list"""
		self._store.append((icon, name, uri))

	def remove_mount(self, uri):
		"""Remove mount from the list"""
		mount_iter = self._get_iter_by_uri(uri)

		# remove mount if exists
		if mount_iter is not None:
			self._store.remove(mount_iter)


class VolumesExtension(MountManagerExtension):
	"""Extension that provides access to volumes"""
	
	def __init__(self, parent, window):
		MountManagerExtension.__init__(self, parent, window)
		self._store = gtk.ListStore(str, str, str, str, bool)

		# create interface
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		self._list = gtk.TreeView(model=self._store)
		self._list.set_show_expanders(True)
		self._list.set_search_column(MountsColumn.NAME)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_mounted = gtk.CellRendererToggle()

		col_name = gtk.TreeViewColumn(_('Name'))
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.set_expand(True)

		col_name.add_attribute(cell_icon, 'icon-name', VolumesColumn.ICON)
		col_name.add_attribute(cell_name, 'markup', VolumesColumn.NAME)

		col_mounted = gtk.TreeViewColumn(_('Mounted'), cell_mounted, text=VolumesColumn.MOUNTED)

		self._list.append_column(col_name)
		self._list.append_column(col_mounted)

		# pack interface
		container.add(self._list)
		self._container.pack_start(container, True, True, 0)

		# add page to mount manager
		self._window.add_page('computer', _('Volumes'), self._container, self)

	def _get_iter_by_uuid(self, uuid):
		"""Get volume list iter by UUID"""
		result = None
		
		# find iter by uuid
		for volume_row in self._store:
			if self._store.get_value(volume_row.iter, VolumesColumn.UUID) == uuid:
				result = volume_row.iter
				break

		return result

	def add_volume(self, volume):
		"""Add volume to the list"""
		icon_names = volume.get_icon().to_string()
		icon = self._application.icon_manager.get_mount_icon_name(icon_names)
		name = volume.get_name()
		uuid = volume.get_uuid()
		mounted = False
		mount_path = None

		# get mount if possible
		mount = volume.get_mount()
		if mount is not None:
			mounted = True
			mount_path = mount.get_root().get_path()

		# add new entry to store
		self._store.append((icon, name, uuid, mount_path, mounted))

	def remove_volume(self, uuid):
		"""Remove volume from the list"""
		volume_iter = self._get_iter_by_uuid(uuid)

		# remove if volume exists
		if volume_iter is not None:
			self._store.remove(volume_iter)

	def volume_mounted(self, uuid, path):
		"""Mark volume with specified UUID as mounted"""
		volume_iter = self._get_iter_by_uuid(uuid)

		# set data if volume exists
		if volume_iter is not None:
			self._store.set_value(volume_iter, VolumesColumn.URI, path)
			self._store.set_value(volume_iter, VolumesColumn.MOUNTED, True)

	def volume_unmounted(self, uuid):
		"""Mark volume with specified UUID as unmounted"""
		volume_iter = self._get_iter_by_uuid(uuid)

		# set data if volume exists
		if volume_iter is not None:
			self._store.set_value(volume_iter, VolumesColumn.URI, None)
			self._store.set_value(volume_iter, VolumesColumn.MOUNTED, False)
