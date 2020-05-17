from gi.repository import Gtk


class FindExtension:
	"""Base class for extending find files tool.

	Use this class to provide find files tool with additional
	options. Objects are created every time tool is created!

	"""

	def __init__(self, parent, always_on=False):
		self._parent = parent
		self._active = always_on

		# create and configure title widget
		self.title = TitleRow(self, always_on)
		self.title.check.connect('state-set', self.__handle_state_set)

		# create and configure container
		self.container = Gtk.VBox.new(False, 5)
		self.container.set_border_width(10)
		self.container.extension = self

	def __handle_state_set(self, widget, state):
		"""Update extension active."""
		self._active = state
		print('came')

	def __get_active(self):
		"""Get state of the extension."""
		return self._active

	def __set_active(self, value):
		"""Set state of the extension."""
		self._active = value
		self.title.set_active(value)

	def get_title(self):
		"""Return name of the extension."""
		return None

	def get_title_widget(self):
		"""Return title widget for extension."""
		return self.title

	def get_container(self):
		"""Return widget container."""
		return self.container

	def is_path_ok(self, provider, path):
		"""Check is specified path fits the cirteria."""
		return True

	active = property(__get_active, __set_active)


class TitleRow(Gtk.ListBoxRow):
	"""List box row representing extension."""

	def __init__(self, extension, always_on):
		Gtk.ListBoxRow.__init__(self)

		self._extension = extension

		self.set_selectable(True)
		self.set_activatable(True)
		self.set_focus_on_click(True)

		# create interface
		hbox = Gtk.HBox.new(False, 10)
		hbox.set_border_width(5)
		self.add(hbox)

		label = Gtk.Label.new(extension.get_title())
		label.set_alignment(0, 0.5)
		hbox.pack_start(label, True, True, 0)

		self.check = Gtk.Switch.new()
		self.check.set_sensitive(not always_on)
		hbox.pack_start(self.check, False, False, 0)

	def get_extension(self):
		"""Return parent extension."""
		return self._extension

	def set_active(self, value):
		"""Set state of the extension."""
		self.check.set_active(value)
