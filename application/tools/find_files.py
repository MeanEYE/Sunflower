import os
import gtk
import user


class FindFiles(gtk.Window):
	"""Find files tool"""

	def __init__(self, parent, application):
		super(FindFiles, self).__init__(type=gtk.WINDOW_TOPLEVEL)

		self._parent = parent
		self._provider = self._parent.get_provider()
		self._application = application
		self._extensions = []
		self._path = self._parent.path
		
		# configure window
		self.set_title(_('Find files'))
		self.set_default_size(550, 500)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_transient_for(application)
		self.set_border_width(7)
		self.set_wmclass('Sunflower', 'Sunflower')
		
		# create interface
		vbox = gtk.VBox(False, 7)

		# create modifiers notebook
		self._extension_list = gtk.Notebook()

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
		hbox_controls.pack_end(button_find, False, False, 0)
		hbox_controls.pack_end(button_stop, False, False, 0)
		hbox_controls.pack_end(button_cancel, False, False, 0)

		vbox.pack_end(self._extension_list, False, False, 0) 
		vbox.pack_end(hbox_controls, False, False, 0)

		self.add(vbox)

		# show all widgets
		self.show_all()

	def __create_extensions(self):
		"""Create rename extensions"""
		for ExtensionClass in self._application.rename_extension_classes.values():
			extension = ExtensionClass(self)
			title = extension.get_title()
		
			# add tab	
			self._extension_list.append_page(extension, gtk.Label(title))
			
			# store extension for later use
			self._extensions.append(extension)

	def _close_window(self, widget=None, data=None):
		"""Close window"""
		self.destroy()

	def stop_search(self, widget=None, data=None):
		"""Stop searching for files"""
		pass

	def find_files(self, widget=None, data=None):
		"""Start searching for files"""
		pass
