import gtk


class FindExtension:
	"""Base class for extending find files tool.

	Use this class to provide find files tool with additional
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

	def is_active(self):
		"""Return boolean representing extension state"""
		return self._active

	def get_title(self):
		"""Return i18n title for extension"""
		return None

	def get_container(self):
		"""Return widget container"""
		return self.vbox

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria

		You can access provider using self._parent._provider object.
		Result needs to be boolean type.

		"""
		return True
