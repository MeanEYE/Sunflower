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
		self._box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		self._box.set_spacing(15)
		set_border_width(self._box, 15)

		# add page to preferences window
		if Gtk.get_major_version() == 3:
			self.add(self._box)

		else:
			self.set_child(self._box)

		self._parent.add_tab(self._page_name, self._page_title, self)

	def _create_title_label(self, title):
		"""Create label used as section title."""
		label_title = Gtk.Label.new('<big>{}</big>'.format(title))
		label_title.set_use_markup(True)
		label_title.set_xalign(0)
		label_title.set_yalign(0.5)

		return label_title

	def _create_section(self, title, container):
		"""Create widget section with title."""
		box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# create section title
		label_title = self._create_title_label(title)
		separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
		set_border_width(container, 10)

		if Gtk.get_major_version() == 3:
			box.pack_start(label_title, True, False, 0)
			box.pack_start(separator, True, False, 0)
			box.pack_start(container, True, False, 0)
			self._box.pack_start(box, False, False, 0)

		else:
			box.append(label_title)
			box.append(separator)
			box.append(container)
			self._box.append(box)

	def _create_radio_section(self, title, container, group=None):
		"""Create section which contains radio button and return radio button."""
		box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# create section title
		label_title = self._create_title_label(title)
		separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
		set_border_width(container, 10)

		if Gtk.get_major_version() == 3:
			radio_title = Gtk.RadioButton.new_from_widget(group)
			radio_title.add(label_title)

			box.pack_start(radio_title, True, False, 0)
			box.pack_start(separator, True, False, 0)
			box.pack_start(container, True, False, 0)
			self._box.pack_start(box, False, False, 0)

		else:
			# GTK 4 dropped radio buttons in favor of grouped check buttons
			radio_title = Gtk.CheckButton.new()
			radio_title.set_child(label_title)

			if group is not None:
				radio_title.set_group(group)

			box.append(radio_title)
			box.append(separator)
			box.append(container)
			self._box.append(box)

		return radio_title

	def _load_options(self):
		"""Load options and update interface"""
		pass

	def _save_options(self):
		"""Method called when save button is clicked"""
		pass

	def __apply_packing(self, child, expand, fill, padding):
		"""Translate GTK 3 packing arguments to child properties. (GTK 4)"""
		if expand:
			child.set_vexpand(True)

			# in GTK 3 expanding child which doesn't fill gets centered
			if not fill:
				child.set_valign(Gtk.Align.CENTER)

		if padding:
			child.set_margin_top(padding)
			child.set_margin_bottom(padding)

	def pack_start(self, child, expand=False, fill=False, padding=0):
		"""Pack things in container."""
		if Gtk.get_major_version() == 3:
			self._box.pack_start(child, expand, fill, padding)

		else:
			self.__apply_packing(child, expand, fill, padding)
			self._box.append(child)

	def pack_end(self, child, expand=False, fill=False, padding=0):
		"""Pack things in container."""
		if Gtk.get_major_version() == 3:
			self._box.pack_end(child, expand, fill, padding)

		else:
			self.__apply_packing(child, expand, fill, padding)
			self._box.append(child)
