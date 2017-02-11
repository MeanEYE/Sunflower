import math

from gi.repository import Gtk, Pango, Gdk
from widgets.breadcrumbs import Breadcrumbs


class Mode:
	NORMAL = 0
	SUPER_USER = 1


class TitleBar:
	"""Tab titlebar class.

	This class provides many different features, including tab specific
	controls, menus and coloring.

	"""

	def __init__(self, application, parent):
		self._application = application
		self._parent = parent

		self._control_count = 0
		self._state = Gtk.StateType.NORMAL
		self._mode = Mode.NORMAL
		self._menu = None
		self._box_spacing = 1
		self._box_border_width = 3
		self._breadcrumbs = None

		# get options
		options = self._application.options

		self._ubuntu_coloring = options.get('ubuntu_coloring')
		self._superuser_notification = options.get('superuser_notification')
		self._button_relief = options.get('button_relief')

		# determine whether we need to show breadcrumbs
		from plugin_base.item_list import ItemList  # must be included here to avoid cyclic import
		section = options.section('item_list')
		is_list = isinstance(parent, ItemList)
		self._breadcrumb_type = section.get('breadcrumbs')
		self._show_breadcrumbs = self._breadcrumb_type != Breadcrumbs.TYPE_NONE and is_list

		# create container box
		self._hbox = Gtk.HBox.new(False, self._box_spacing)
		self._hbox.get_style_context().add_class('sunflower-title-bar')

		self._hbox_controls = Gtk.HBox.new(False, 0)
		self._hbox_controls.get_style_context().add_class('linked')

		# create container
		self._container = Gtk.EventBox()
		self._container.set_app_paintable(True)
		self._container.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)

		# connect signals
		self._container.connect('button-release-event', self.__button_release_event)

		# top folder icon as default
		self._icon = Gtk.Image.new()

		self._button_menu = Gtk.Button.new()
		self._button_menu.add(self._icon)
		self._button_menu.set_focus_on_click(False)
		self._button_menu.set_tooltip_text(_('Context menu'))
		self._button_menu.connect('clicked', self.show_menu)
		self._button_menu.get_style_context().add_class('sunflower-tab-menu')

		# create title box
		vbox = Gtk.VBox.new(False, 0)

		if self._show_breadcrumbs:
			self._breadcrumbs = Breadcrumbs(self)
			vbox.pack_start(self._breadcrumbs, True, True, 0)

		else:
			self._title_label = Gtk.Label()
			self._title_label.set_alignment(0, 0.5)
			self._title_label.set_use_markup(True)
			self._title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
			vbox.pack_start(self._title_label, True, True, 0)

		font = Pango.FontDescription('8')
		self._subtitle_label = Gtk.Label()
		self._subtitle_label.set_alignment(0, 0.5)
		self._subtitle_label.set_use_markup(False)
		self._subtitle_label.modify_font(font)

		# create spinner control if it exists
		self._spinner = Gtk.Spinner()
		self._spinner.set_property('no-show-all', True)

		# pack interface
		vbox.pack_start(self._subtitle_label, False, False, 0)

		self._hbox.pack_start(self._button_menu, False, False, 0)
		self._hbox.pack_start(vbox, True, True, 4)
		self._hbox.pack_start(self._spinner, False, False, 5)
		self._hbox.pack_start(self._hbox_controls, False, False, 0)

		self._container.add(self._hbox)
		self._spinner_counter = 0

	def __button_release_event(self, widget, event, data=None):
		"""Handle button release event"""
		if event.button == 1:
			# focus main object on left click
			self._parent.focus_main_object()

		elif event.button == 2:
			# duplicate tab on middle click
			self._parent._duplicate_tab(widget)

		return True

	def __get_menu_position(self, menu, *args):
		"""Get bookmarks position"""
		button = args[-1]
		window_x, window_y = self._application.get_position()
		button_x, button_y = button.translate_coordinates(self._application, 0, 0)
		button_h = button.get_allocation().height

		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return pos_x, pos_y, True

	def add_control(self, widget):
		"""Add button control"""
		self._control_count += 1
		self._hbox_controls.pack_end(widget, False, False, 0)

	def set_state(self, state):
		"""Set GTK control state for title bar"""
		self._state = state

		# apply style class to container
		if state == Gtk.StateType.SELECTED:
			self._hbox.get_style_context().add_class('selected')
		else:
			self._hbox.get_style_context().remove_class('selected')

		# let breadcrumbs know about new state
		if self._show_breadcrumbs:
			self._breadcrumbs.set_state(state)

	def set_mode(self, mode):
		"""Set title bar mode"""
		self._mode = mode

		if self._mode == Mode.SUPER_USER:
			self._hbox.get_style_context().add_class('superuser')

	def set_title(self, text):
		"""Set title text"""
		if self._show_breadcrumbs:
			self._breadcrumbs.refresh(text)

		else:
			self._title_label.set_markup(text.replace('&', '&amp;'))

	def set_subtitle(self, text):
		"""Set subtitle text"""
		self._subtitle_label.set_text(text.replace('&', '&amp;'))

	def set_icon_from_name(self, icon_name):
		"""Set icon from specified name"""
		self._icon.set_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)

	def set_menu(self, menu):
		"""Set title bar menu"""
		self._menu = menu

	def get_container(self):
		"""Return title bar container"""
		return self._container

	def show_menu(self, widget=None, data=None):
		"""Show title bar menu"""
		if self._menu is None:
			return

		# show menu below the button
		button = widget if widget is not None else self._button_menu

		self._menu.popup(None, None, self.__get_menu_position, button, 1, 0)

	def show_spinner(self):
		"""Show spinner widget"""
		if self._spinner is None:
			return

		# increase counter
		self._spinner_counter += 1

		# start spinner if needed
		if self._spinner_counter == 1:
			self._spinner.start()
			self._spinner.show()

	def hide_spinner(self):
		"""Hide spinner widget"""
		if self._spinner is None:
			return

		# reduce counter
		self._spinner_counter -= 1

		# stop spinner
		if self._spinner_counter <= 0:
			self._spinner_counter = 0
			self._spinner.stop()
			self._spinner.hide()

	def apply_settings(self):
		"""Method called when system applies new settings"""
		self._ubuntu_coloring = self._application.options.get('ubuntu_coloring')
		self._superuser_notification = self._application.options.get('superuser_notification')
		self._button_relief = self._application.options.get('button_relief')

		# determine whether we need to show breadcrumbs
		section = self._application.options.section('item_list')
		self._breadcrumb_type = section.get('breadcrumbs')

		if self._show_breadcrumbs:
			self._breadcrumbs.apply_settings()

		# apply button relief
		relief = (Gtk.ReliefStyle.NONE, Gtk.ReliefStyle.NORMAL)[self._button_relief]

		for control in self._hbox.get_children():
			if issubclass(control.__class__, Gtk.Button):
				control.set_relief(relief)

		# apply new colors
		self._container.queue_draw()
