from gi.repository import Gtk


class LocationMenu:
	"""Interface which shows list of paths to jump to."""

	def __init__(self, parent, relative_to):
		self._parent = parent

		# create popover interface
		self._popover = Gtk.Popover.new()
		self._popover.set_relative_to(relative_to)
		self._popover.set_position(Gtk.PositionType.BOTTOM)

		# create widget container
		container = Gtk.VBox.new(False, 5)
		container.set_border_width(5)

		# create search field
		self._search_field = Gtk.SearchEntry.new()

		# create notebook for different lists
		self._notebook = Gtk.Notebook.new()

		# create button box and commonly used buttons
		hbox_buttons = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
		hbox_buttons.get_style_context().add_class('linked')

		button_open = Gtk.Button.new_from_icon_name('document-open', Gtk.IconSize.BUTTON)
		button_open.connect('clicked', self.__handle_open_click)
		button_open.set_tooltip_text(_('Open'))
		hbox_buttons.pack_start(button_open, False, False, 0)

		button_open_tab = Gtk.Button.new_from_icon_name('tab-new', Gtk.IconSize.BUTTON)
		button_open_tab.connect('clicked', self.__handle_open_tab_click)
		button_open_tab.set_tooltip_text(_('Open selected path in new tab'))
		hbox_buttons.pack_start(button_open_tab, False, False, 0)

		self._button_open_opposite = Gtk.Button.new_from_icon_name('go-right', Gtk.IconSize.BUTTON)
		self._button_open_opposite.connect('clicked', self.__handle_open_opposite_click)
		self._button_open_opposite.set_tooltip_text(_('Open selected path in opposite list'))
		hbox_buttons.pack_start(self._button_open_opposite, False, False, 0)

		button_open_terminal = Gtk.Button.new_from_icon_name('terminal', Gtk.IconSize.BUTTON)
		button_open_terminal.connect('clicked', self.__handle_open_opposite_click)
		button_open_terminal.set_tooltip_text(_('Open terminal at selected path'))
		hbox_buttons.pack_start(button_open_terminal, False, False, 0)

		# pack interface
		container.pack_start(self._search_field, True, False, 0)
		container.pack_start(self._notebook, True, True, 5)
		container.pack_start(hbox_buttons, True, False, 0)

		container.show_all()
		self._popover.add(container)

	def __handle_page_change(self):
		"""Handle changing of active page in notebook."""
		pass

	def __handle_open_click(self, widget, data=None):
		"""Handle clicking on open button."""
		pass

	def __handle_open_tab_click(self, widget, data=None):
		"""Handle clicking on open in new tab button."""
		pass

	def __handle_open_opposite_click(self, widget, data=None):
		"""Handle slicking on open in opposite panel button."""
		pass

	def __handle_open_terminal_click(self, widget, data=None):
		"""Handle clicking on open in terminal button."""
		pass

	def add_list(self, control):
		"""Add list control with specified name to the notebook."""
		pass

	def show(self):
		"""Show location menu."""
		application = self._parent._parent

		if application.get_left_object() == self._parent:
			self._button_open_opposite.get_image().set_from_icon_name('go-right', Gtk.IconSize.BUTTON)
		else:
			self._button_open_opposite.get_image().set_from_icon_name('go-left', Gtk.IconSize.BUTTON)

		self._popover.popup()
