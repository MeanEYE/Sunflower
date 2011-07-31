import gtk


class RenameExtension:
	"""Base class for extending advanced rename tool.

	Use this class to provide advanced rename tool with additional
	options. Objects are created every time tool is created!

	"""

	def __init__(self, parent):
		self._parent = parent

		# create and configure container
		self.vbox = gtk.VBox(False, 5)
		self.vbox.set_border_width(7)
		self.vbox.set_data('extension', self)

		# create activity toggle
		self._active = False
		self._checkbox_active = gtk.CheckButton(_('Use this extension'))
		self._checkbox_active.connect('toggled', self.__toggle_active)
		self._checkbox_active.show()

		self.vbox.pack_start(self._checkbox_active, False, False, 0)

	def __toggle_active(self, widget, data=None):
		"""Toggle extension active property"""
		self._active = widget.get_active()
		self._update_parent_list()

	def _update_parent_list(self, widget=None, data=None):
		"""Update parent list"""
		self._parent.update_list()

	def is_active(self):
		"""Return boolean representing extension state"""
		return self._active

	def reset(self):
		"""Method called before iterating through parents list"""
		pass

	def get_title(self):
		"""Return i18n title for extension"""
		return None

	def get_container(self):
		"""Return widget container"""
		return self.vbox

	def get_new_name(self, old_name, new_name):
		"""Generate and return new name for specified file.

		If you don't make any modifications to the name make sure
		you return new_name instead. In cases where extension needs
		to file (or file contents) you can use self._parent._provider
		object.

		Parameters:
		old_name - original (unchanged) file name
		new_name - name modified by previous extensions

		"""
		return new_name
