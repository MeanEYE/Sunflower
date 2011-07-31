import os
import gtk
import user


class Column:
	ICON = 0
	NAME = 1
	DIRECTORY = 2


class FindFiles:
	"""Find files tool"""

	def __init__(self, parent, application):
		# store parameters
		self._parent = parent
		self._application = application
		self._extensions = []
		self._path = self._parent.path
		self._provider = None

		if hasattr(self._parent, 'get_provider'):
			self._provider = self._parent.get_provider()
		
		# configure window
		self.window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)

		self.window.set_title(_('Find files'))
		self.window.set_default_size(550, 500)
		self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.window.set_transient_for(application)
		self.window.set_border_width(7)
		self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.window.set_wmclass('Sunflower', 'Sunflower')
		
		# create interface
		vbox = gtk.VBox(False, 7)

		# create path and basic options
		table_basic = gtk.Table(3, 2, False)
		table_basic.set_col_spacings(5)
		table_basic.set_row_spacings(2)

		label_path = gtk.Label(_('Search in:'))
		label_path.set_alignment(0, 0.5)

		self._entry_path = gtk.Entry()

		if hasattr(self._parent, 'path'):
			# get path from the parent
			self._entry_path.set_text(self._parent.path)

		else:
			# parent has no path, set user home directory
			self._entry_path.set_text(os.path.expanduser(user.home))

		button_browse = gtk.Button(label=_('Browse'))

		self._checkbox_recursive = gtk.CheckButton(label=_('Search recursively'))
		self._checkbox_recursive.set_active(True)

		# create extensions notebook
		self._extension_list = gtk.Notebook()

		# create list
		self._list = gtk.ListStore(str, str, str)
		self._names = gtk.TreeView(model=self._list)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_directory = gtk.CellRendererText()
		
		col_name = gtk.TreeViewColumn(_('Name'))
		col_name.set_expand(True)
		
		col_directory = gtk.TreeViewColumn(_('Location'))
		col_directory.set_expand(True)
		
		# pack renderer
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_directory.pack_start(cell_directory, True)
		
		# connect renderer attributes
		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'text', Column.NAME)
		col_directory.add_attribute(cell_directory, 'text', Column.DIRECTORY)
		
		self._names.append_column(col_name)
		self._names.append_column(col_directory)
		
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		# create controls
		hbox_controls = gtk.HBox(False, 5)

		button_find = gtk.Button(stock=gtk.STOCK_FIND)
		button_find.connect('clicked', self.find_files)

		button_stop = gtk.Button(stock=gtk.STOCK_STOP)
		button_stop.set_sensitive(False)
		button_stop.connect('clicked', self.stop_search)

		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
		button_cancel.connect('clicked', self._close_window)
		
		# pack interface
		table_basic.attach(label_path, 0, 1, 0, 1, xoptions=gtk.SHRINK|gtk.FILL)
		table_basic.attach(self._entry_path, 1, 2, 0, 1, xoptions=gtk.EXPAND|gtk.FILL)
		table_basic.attach(button_browse, 2, 3, 0, 1, xoptions=gtk.SHRINK|gtk.FILL)
		table_basic.attach(self._checkbox_recursive, 1, 2, 1, 2)

		container.add(self._names)

		hbox_controls.pack_end(button_find, False, False, 0)
		hbox_controls.pack_end(button_stop, False, False, 0)
		hbox_controls.pack_end(button_cancel, False, False, 0)

		vbox.pack_start(table_basic, False, False, 0) 
		vbox.pack_start(self._extension_list, False, False, 0) 
		vbox.pack_end(hbox_controls, False, False, 0)
		vbox.pack_end(container, True, True, 0)

		self.window.add(vbox)

		# create extensions
		self.__create_extensions()

		# show all widgets
		self.window.show_all()

	def __create_extensions(self):
		"""Create rename extensions"""
		for ExtensionClass in self._application.find_extension_classes.values():
			extension = ExtensionClass(self)
			title = extension.get_title()
		
			# add tab	
			self._extension_list.append_page(extension.get_container(), gtk.Label(title))
			
			# store extension for later use
			self._extensions.append(extension)

	def _close_window(self, widget=None, data=None):
		"""Close window"""
		self.window.destroy()

	def stop_search(self, widget=None, data=None):
		"""Stop searching for files"""
		pass

	def find_files(self, widget=None, data=None):
		"""Start searching for files"""
		path = self._entry_path.get_text()

		# make sure we have a valid provider
		if self._provider is None:
			ProviderClass = self._application.get_provider_by_protocol('file')
			self._provider = ProviderClass(self._parent)

		# check if specified path exists
		if not self._provider.is_dir(path):
			dialog = gtk.MessageDialog(
								self.window,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_ERROR,
								gtk.BUTTONS_OK,
								_(
									'Specified path is not valid or doesn\'t '
									'exist anymore. Please check your selection '
									'and try again.'
								)
							)
			dialog.run()
			dialog.destroy()

			return
