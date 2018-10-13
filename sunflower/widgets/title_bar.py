import math

from gi.repository import Gtk, Pango, Gdk
from .breadcrumbs import Breadcrumbs
from .context_menu import ContextMenu


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
		self.context_menu = None
		self._breadcrumbs = None
		self._title_label = None
		self._subtitle_label = None

		# get options
		options = self._application.options

		self._superuser_notification = options.get('superuser_notification')
		self._button_relief = options.get('button_relief') or 0

		# create container box
		self._container = Gtk.HBox.new(False, 7)
		self._container.get_style_context().add_class('sunflower-title-bar')

		self._container_controls = Gtk.HBox.new(False, 0)
		self._container_controls.get_style_context().add_class('linked')

		# top folder icon as default
		self._icon = Gtk.Image.new()

		self._button_menu = Gtk.Button.new()
		self._button_menu.add(self._icon)
		self._button_menu.set_focus_on_click(False)
		self._button_menu.set_tooltip_text(_('Context menu'))
		self._button_menu.connect('clicked', self.show_context_menu)
		self._button_menu.get_style_context().add_class('sunflower-context-menu')

		# create context menu
		self.context_menu = ContextMenu(self, self._button_menu)

		# create spinner control if it exists
		self._spinner = Gtk.Spinner()
		self._spinner.set_property('no-show-all', True)

		# pack interface
		self._container.pack_start(self._button_menu, False, False, 0)
		self._container.pack_end(self._container_controls, False, False, 0)
		self._container.pack_end(self._spinner, False, False, 0)

		self._spinner_counter = 0

	def create_breadcrumbs(self):
		"""Create breadcrumbs as main control."""
		self._breadcrumbs = Breadcrumbs(self)
		self._container.pack_start(self._breadcrumbs, True, True, 0)

	def create_title(self):
		"""Create title as main control."""
		vbox = Gtk.VBox.new(False, 0)

		# create main tab title
		self._title_label = Gtk.Label.new()
		self._title_label.set_alignment(0, 0.5)
		self._title_label.set_use_markup(True)
		self._title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

		# create smaller subtitle
		font = Pango.FontDescription('8')
		self._subtitle_label = Gtk.Label.new()
		self._subtitle_label.set_alignment(0, 0.5)
		self._subtitle_label.set_use_markup(False)
		self._subtitle_label.modify_font(font)

		# pack interface
		vbox.pack_start(self._title_label, True, True, 0)
		vbox.pack_start(self._subtitle_label, False, False, 0)
		self._container.pack_start(vbox, True, True, 0)

	def add_control(self, widget):
		"""Add control to button bar."""
		self._control_count += 1
		self._container_controls.pack_end(widget, False, False, 0)

	def set_state(self, state):
		"""Set GTK control state for title bar."""
		self._state = state

		# apply style class to container
		if state == Gtk.StateType.SELECTED:
			self._container.get_style_context().add_class('selected')
		else:
			self._container.get_style_context().remove_class('selected')

	def set_mode(self, mode):
		"""Set title bar mode"""
		self._mode = mode

		if self._mode == Mode.SUPER_USER:
			self._container.get_style_context().add_class('superuser')

	def set_title(self, text):
		"""Set title text"""
		if self._breadcrumbs is not None:
			self._breadcrumbs.refresh(text)
		else:
			self._title_label.set_markup(text.replace('&', '&amp;'))

	def set_subtitle(self, text):
		"""Set subtitle text"""
		self._subtitle_label.set_text(text.replace('&', '&amp;'))

	def set_icon_from_name(self, icon_name):
		"""Set icon from specified name"""
		self._icon.set_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)

	def get_container(self):
		"""Return title bar container"""
		return self._container

	def show_context_menu(self, widget=None, data=None):
		"""Show title bar menu"""
		self.context_menu.show()
		return True

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
		self._superuser_notification = self._application.options.get('superuser_notification')
		self._button_relief = self._application.options.get('button_relief')

		# apply button relief
		relief = (Gtk.ReliefStyle.NONE, Gtk.ReliefStyle.NORMAL)[self._button_relief]

		for control in self._container.get_children():
			if issubclass(control.__class__, Gtk.Button):
				control.set_relief(relief)
