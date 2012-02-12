import gtk


class Column:
	ICON = 0
	NAME = 1
	PROTOCOL = 2
	CONFIGURATION = 3
	PATH = 4
	MOUNTED = 5


class MountsManagerWindow(gtk.Window):

	def __init__(self, parent):
		# create mount manager window
		gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)

		self._parent = parent
		
		# configure window
		self.set_title(_('Mount manager'))
		self.set_default_size(500, 340)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(self._parent._application)
		self.set_wmclass('Sunflower', 'Sunflower')
		self.set_border_width(7)

		self.connect('delete-event', self._hide)
		
		# create user interface
		vbox = gtk.VBox(False, 5)
		hbox_controls = gtk.HBox(False, 5)
		
		# create a tree view
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		self._list = gtk.TreeView(model=self._parent._store)
		self._list.set_show_expanders(True)
		self._list.set_search_column(Column.NAME)
		self._list.connect('key-press-event', self._handle_key_press)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_path = gtk.CellRendererText()

		col_name = gtk.TreeViewColumn(None)
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)

		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'markup', Column.NAME)

		col_path = gtk.TreeViewColumn(None, cell_path, text=Column.PATH)

		self._list.append_column(col_name)
		self._list.append_column(col_path)

		# create controls
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._hide)

		button_unmount = gtk.Button()
		button_unmount.set_label(_('Unmount'))
		button_unmount.set_sensitive(False)
		button_unmount.connect('clicked', self._parent._unmount_item)

		separator = gtk.VSeparator()

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
		button_new_tab.set_label(_('New tab'))
		button_new_tab.set_tooltip_text(_('Open selected path in new tab'))
		#button_new_tab.connect('clicked', self._open_in_new_tab)
		
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
		hbox_controls.pack_start(separator, False, False, 0)
		hbox_controls.pack_start(button_unmount, False, False, 0)

		hbox_controls.pack_end(button_close, False, False, 0)
		hbox_controls.pack_end(button_jump, False, False, 0)
		hbox_controls.pack_end(button_new_tab, False, False, 0)
		
		vbox.pack_start(container, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)
		
		self.add(vbox)

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

	def _hide(self, widget=None, data=None):
		"""Hide mount manager"""
		self.hide()
		return True
