import gtk


class RenameExtension(gtk.VBox):
	"""Base class for extending advanced rename tool.
	
	Use this class to provide advanced rename tool with additional
	options. Objects are created every time tool is created!
	
	"""
	
	def __init__(self, parent):
		super(RenameExtension, self).__init__(False, 5)
		
		self._parent = parent
		
		self.set_border_width(5)
		
		# create activity toggle
		self._active = False
		self._checkbox_active = gtk.CheckButton(_('Use this extension'))
		self._checkbox_active.connect('toggle', self.__toggle_active)
		self._checkbox_active.show()
		
		self.pack_start(self._checkbox_active, False, False, 0)
		
	def __toggle_active(self, widget, data=None):
		"""Toggle extension active property"""
		self._active = widget.get_active()
		
	def get_new_name(self, file_name, old_name):
		"""Generate and return new name for specified file.
		
		If you don't make any modifications to the name make sure
		you return old_name instead. In cases where extension needs
		to file (or file contents) you can use self._parent._provider
		object.
		
		Parameters:
		file_name - original (unchanged) file name
		old_name - name modified by previous extensions
		
		"""
		return old_name