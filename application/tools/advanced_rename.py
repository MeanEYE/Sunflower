import gtk


class Column:
	ICON = 0
	OLD_NAME = 1
	NEW_NAME = 2


class AdvancedRename(gtk.Window):
	
	def __init__(self, parent, application):
		super(AdvancedRename, self).__init__(type=gtk.WINDOW_TOPLEVEL)
		
		self._parent = parent
		self._provider = self._parent.get_provider()
		self._application = application
		
		# configure window
		self.set_title(_('Advanced rename'))
		self.set_default_size(640, 480)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_transient_for(application)
		self.set_border_width(7)
		self.set_wmclass('Sunflower', 'Sunflower')
		
		# create interface
		vbox = gtk.VBox(False, 7)
		
		# create modifiers notebook
		self._extensions = gtk.Notebook()
		
		# create list
		self._list = gtk.ListStore(str, str, str)
		self._names = gtk.TreeView(model=self._list)

		cell_icon = gtk.CellRendererPixbuf()
		cell_old_name = gtk.CellRendererText()
		cell_new_name = gtk.CellRendererText()
		
		col_old_name = gtk.TreeViewColumn(_('Old name'))
		col_new_name = gtk.TreeViewColumn(_('New name'))
		
		# pack renderer
		col_old_name.pack_start(cell_icon, False)
		col_old_name.pack_start(cell_old_name, True)
		col_new_name.pack_start(cell_new_name, True)
		
		# connect renderer attributes
		col_old_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_old_name.add_attribute(cell_old_name, 'text', Column.OLD_NAME)
		col_new_name.add_attribute(cell_new_name, 'text', Column.NEW_NAME)
		
		self._names.append_column(col_old_name)
		self._names.append_column(col_new_name)
		
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)
		
		# create controls
		hbox = gtk.HBox(False, 5)
		
		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
		button_cancel.connect('clicked', self._close_window)
		
		button_undo = gtk.Button(stock=gtk.STOCK_UNDO)
		button_undo.set_sensitive(False)

		image_rename = gtk.Image()
		image_rename.set_from_icon_name('edit-find-replace', gtk.ICON_SIZE_BUTTON)
		button_rename = gtk.Button(label=_('Rename'))	
		button_rename.set_image(image_rename)

		# pack interface
		hbox.pack_start(button_undo, False, False, 0)
		hbox.pack_end(button_rename, False, False, 0)
		hbox.pack_end(button_cancel, False, False, 0)

		container.add(self._names)
		
		vbox.pack_start(self._extensions, False, False, 0)
		vbox.pack_end(hbox, False, False, 0)
		vbox.pack_end(container, True, True, 0)
		
		self.add(vbox)
		
		# create extensions
		self.__create_extensions()

		# show all widgets
		self.show_all()
	
	def __create_extensions(self):
		"""Create rename extensions"""
		for ExtensionClass in self._application.rename_extension_classes.values():
			extension = ExtensionClass(self)
			title = extension.get_title()
			
			self._extensions.append_page(extension, gtk.Label(title))
		
	def _close_window(self, widget, data=None):
		"""Close window"""
		self.destroy()
