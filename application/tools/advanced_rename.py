import os
import gtk

from operation import RenameOperation


class Column:
	ICON = 0
	OLD_NAME = 1
	NEW_NAME = 2


class AdvancedRename(gtk.Window):
	"""Advanced rename tool"""
	
	def __init__(self, parent, application):
		super(AdvancedRename, self).__init__(type=gtk.WINDOW_TOPLEVEL)
		
		self._parent = parent
		self._provider = self._parent.get_provider()
		self._application = application
		self._extensions = []
		self._path = self._parent.path
		
		# configure window
		self.set_title(_('Advanced rename'))
		self.set_default_size(640, 600)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_transient_for(application)
		self.set_border_width(7)
		self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.set_wmclass('Sunflower', 'Sunflower')
		
		# create interface
		vbox = gtk.VBox(False, 7)
		
		# create modifiers notebook
		self._extension_list = gtk.Notebook()
		self._extension_list.connect('page-reordered', self.__handle_reorder)
		
		# create list
		self._list = gtk.ListStore(str, str, str)
		self._names = gtk.TreeView(model=self._list)

		cell_icon = gtk.CellRendererPixbuf()
		cell_old_name = gtk.CellRendererText()
		cell_new_name = gtk.CellRendererText()
		
		col_old_name = gtk.TreeViewColumn(_('Old name'))
		col_old_name.set_expand(True)
		
		col_new_name = gtk.TreeViewColumn(_('New name'))
		col_new_name.set_expand(True)
		
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
		
		# create location
		vbox_location = gtk.VBox(False, 0)
		
		label_location = gtk.Label(_('Items located in:'))
		label_location.set_alignment(0, 0.5)
		
		entry_location = gtk.Entry()
		entry_location.set_text(self._path)
		entry_location.set_editable(False)
		
		# create controls
		hbox = gtk.HBox(False, 5)
		
		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
		button_cancel.connect('clicked', self._close_window)
		
		image_rename = gtk.Image()
		image_rename.set_from_icon_name('edit-find-replace', gtk.ICON_SIZE_BUTTON)
		button_rename = gtk.Button(label=_('Rename'))	
		button_rename.set_image(image_rename)
		button_rename.connect('clicked', self.rename_files)

		# pack interface
		vbox_location.pack_start(label_location, False, False, 0)
		vbox_location.pack_start(entry_location, False, False, 0)
		
		hbox.pack_end(button_rename, False, False, 0)
		hbox.pack_end(button_cancel, False, False, 0)

		container.add(self._names)
		
		vbox.pack_start(self._extension_list, False, False, 0)
		vbox.pack_end(hbox, False, False, 0)
		vbox.pack_end(vbox_location, False, False, 0)
		vbox.pack_end(container, True, True, 0)
		
		self.add(vbox)
		
		# prepare UI
		self.__create_extensions()
		self.__populate_list()
		
		# update list initially
		self.update_list()

		# show all widgets
		self.show_all()
	
	def __create_extensions(self):
		"""Create rename extensions"""
		for ExtensionClass in self._application.rename_extension_classes.values():
			extension = ExtensionClass(self)
			title = extension.get_title()
			container = extension.get_container()
		
			# add tab	
			self._extension_list.append_page(container, gtk.Label(title))
			self._extension_list.set_tab_reorderable(container, True)
			
			# store extension for later use
			self._extensions.append(extension)
			
	def __populate_list(self):
		"""Populate list with data from parent"""
		parent_list = self._parent._get_selection_list()
		
		if parent_list is None:
			return
		
		# clear selection on source directory
		if self._path == self._parent.path:
			self._parent.unselect_all()
					
		# clear items
		self._list.clear()
		
		# add all the items from the list
		for item in parent_list:
			name = os.path.basename(item)
			icon = self._application.icon_manager.get_icon_for_file(item)
			
			self._list.append((icon, name, ''))

	def __handle_reorder(self, notebook, child, page_number, data=None):
		"""Handle extension reordering"""
		self.update_list()

	def _close_window(self, widget=None, data=None):
		"""Close window"""
		self.destroy()

	def update_list(self):
		"""Update file list"""
		active_extensions = filter(  # get only active extensions
								lambda ext: ext.is_active(), 
								self._extension_list.get_children()
							)
		
		# call reset on all extensions
		map(lambda ext: ext.reset(), active_extensions)
		
		for row in self._list:
			old_name = row[Column.OLD_NAME]
			new_name = old_name
			
			# run new name through extensions
			for extension in active_extensions:
				new_name = extension.get_new_name(old_name, new_name)
	
			# store new name to list
			row[Column.NEW_NAME] = new_name
			
	def rename_files(self, widget=None, data=None):
		"""Rename selected files"""
		dialog = gtk.MessageDialog(
								self,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_QUESTION,
								gtk.BUTTONS_YES_NO,
								ngettext(
									"You are about to rename {0} item.\n"
									"Are you sure about this?",
									"You are about to rename {0} items.\n"
									"Are you sure about this?",
									len(self._list)
								).format(len(self._list))
							)
		result = dialog.run()
		dialog.destroy()
		
		if result == gtk.RESPONSE_YES:
			# user confirmed rename
			item_list = []
			for item in self._list:
				item_list.append((item[Column.OLD_NAME], item[Column.NEW_NAME]))
			
			# create thread and start operation
			operation = RenameOperation(
									self._application, 
									self._provider, 
									self._path,
									item_list
								)
			operation.start()
			
			# destroy window
			self._close_window()
