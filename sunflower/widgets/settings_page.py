from gi.repository import Gtk, GObject


class SettingsPage(Gtk.ScrolledWindow):
	"""Abstract class used to build pages in preferences window."""

	def __init__(self, parent, application, name, title):
		Gtk.ScrolledWindow.__init__(self)

		self._parent = parent
		self._application = application
		self._page_name = name
		self._page_title = title

		# configure main container
		self._box = Gtk.VBox.new(False, 0)
		self._box.set_spacing(15)
		self._box.set_border_width(15)

		# add page to preferences window
		self.add(self._box)
		self._parent.add_tab(self._page_name, self._page_title, self)

	def _create_section(self, title, container):
		"""Create widget section with title."""
		box = Gtk.VBox.new(False, 0)

		# create section title
		label_title = Gtk.Label.new('<big>{}</big>'.format(title))
		label_title.set_alignment(0, 0.5)
		label_title.set_use_markup(True)
		box.pack_start(label_title, True, False, 0)
		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), True, False, 0)

		# pack container
		box.pack_start(container, True, False, 0)
		container.set_border_width(10)
		self._box.pack_start(box, False, False, 0)

	def _create_radio_section(self, title, container, group=None):
		"""Create section which contains radio button and return radio button."""
		box = Gtk.VBox.new(False, 0)

		# create section title
		label_title = Gtk.Label.new('<big>{}</big>'.format(title))
		label_title.set_alignment(0, 0.5)
		label_title.set_use_markup(True)
		radio_title = Gtk.RadioButton.new_from_widget(group)
		radio_title.add(label_title)
		box.pack_start(radio_title, True, False, 0)
		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), True, False, 0)

		# pack container
		box.pack_start(container, True, False, 0)
		container.set_border_width(10)
		self._box.pack_start(box, False, False, 0)

		return radio_title

	def _load_options(self):
		"""Load options and update interface"""
		pass

	def _save_options(self):
		"""Method called when save button is clicked"""
		pass

	def pack_start(self, *args, **kwargs):
		"""Pack things in container."""
		self._box.pack_start(*args, **kwargs)

	def pack_end(self, *args, **kwargs):
		"""Pack things in container."""
		self._box.pack_end(*args, **kwargs)
