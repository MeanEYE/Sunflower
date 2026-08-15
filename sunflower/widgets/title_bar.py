from __future__ import absolute_import

import math

from gi.repository import Gtk, Pango, Gdk
from sunflower.widgets.breadcrumbs import Breadcrumbs
from sunflower.widgets.context_menu import ContextMenu
from sunflower.common import decode_file_name


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
		self._state = Gtk.StateFlags.NORMAL
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
		self._container = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
		self._container.get_style_context().add_class('sunflower-title-bar')

		self._container_controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
		self._container_controls.get_style_context().add_class('linked')

		# top folder icon as default
		self._icon = Gtk.Image.new()

		self._button_menu = Gtk.Button.new()
		if Gtk.get_major_version() == 3:
			self._button_menu.add(self._icon)
		else:
			self._button_menu.set_child(self._icon)

		self._button_menu.set_focus_on_click(False)
		self._button_menu.set_tooltip_text(_('Context menu'))
		self._button_menu.connect('clicked', self.show_context_menu)
		self._button_menu.get_style_context().add_class('sunflower-context-menu')

		# create context menu
		self.context_menu = ContextMenu(self, self._button_menu)

		# create spinner control if it exists
		self._spinner = Gtk.Spinner()
		if Gtk.get_major_version() == 3:
			self._spinner.set_property('no-show-all', True)
		else:
			self._spinner.hide()

		# pack interface
		if Gtk.get_major_version() == 3:
			self._container.pack_start(self._button_menu, False, False, 0)
			self._container.pack_end(self._container_controls, False, False, 0)
			self._container.pack_end(self._spinner, False, False, 0)

		else:
			# GTK 4 boxes have no end packing, controls are appended by
			# _pack_end_controls once the main control is in place
			self._container.append(self._button_menu)

		self._spinner_counter = 0

	def _pack_end_controls(self):
		"""Append spinner and controls after the main control.

		GTK 3 keeps end packed children at the right edge no matter when they
		were added, GTK 4 orders children by the time they were appended.

		"""
		if Gtk.get_major_version() == 3:
			return

		# order matches GTK 3 where end packed children are shown in reverse
		self._container.append(self._spinner)
		self._container.append(self._container_controls)

	def create_breadcrumbs(self):
		"""Create breadcrumbs as main control."""
		self._breadcrumbs = Breadcrumbs(self)
		if Gtk.get_major_version() == 3:
			self._container.pack_start(self._breadcrumbs.container, True, True, 0)

		else:
			self._breadcrumbs.container.set_hexpand(True)
			self._container.append(self._breadcrumbs.container)
			self._pack_end_controls()

	def create_title(self):
		"""Create title as main control."""
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# create main tab title
		self._title_label = Gtk.Label.new()
		self._title_label.set_xalign(0)
		self._title_label.set_yalign(0.5)
		self._title_label.set_use_markup(True)
		self._title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

		# create smaller subtitle
		font = Pango.FontDescription('8')
		self._subtitle_label = Gtk.Label.new()
		self._subtitle_label.set_xalign(0)
		self._subtitle_label.set_yalign(0.5)
		self._subtitle_label.set_use_markup(False)

		# modify_font is not available in GTK 4, attributes work in both
		attributes = Pango.AttrList.new()
		attributes.insert(Pango.AttrFontDesc.new(font))
		self._subtitle_label.set_attributes(attributes)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox.pack_start(self._title_label, True, True, 0)
			vbox.pack_start(self._subtitle_label, False, False, 0)
			self._container.pack_start(vbox, True, True, 0)

		else:
			# vexpand must not be used here, it would propagate to the title
			# bar itself and make it eat vertical space from the main object
			vbox.append(self._title_label)
			vbox.append(self._subtitle_label)
			vbox.set_hexpand(True)
			self._container.append(vbox)
			self._pack_end_controls()

	def add_control(self, widget):
		"""Add control to button bar."""
		self._control_count += 1
		if Gtk.get_major_version() == 3:
			self._container_controls.pack_end(widget, False, False, 0)

		else:
			# end packed children are shown in reverse order of addition
			self._container_controls.prepend(widget)

	def set_state(self, state):
		"""Set GTK control state for title bar."""
		self._state = state

		# apply style class to container
		if state == Gtk.StateFlags.SELECTED:
			self._container.get_style_context().add_class('selected')
		else:
			self._container.get_style_context().remove_class('selected')

	def set_mode(self, mode):
		"""Set title bar mode"""
		self._mode = mode

		if self._mode == Mode.SUPER_USER:
			self._container.get_style_context().add_class('superuser')

	def set_title(self, path):
		"""Set title text"""
		if self._breadcrumbs is not None:
			self._breadcrumbs.refresh(path)
		else:
			self._title_label.set_markup(decode_file_name(path).replace('&', '&amp;'))

	def set_subtitle(self, text):
		"""Set subtitle text"""
		self._subtitle_label.set_text(text.replace('&', '&amp;'))

	def set_icon_from_name(self, icon_name):
		"""Set icon from specified name"""
		if Gtk.get_major_version() == 3:
			self._icon.set_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)

		else:
			self._icon.set_from_icon_name(icon_name)
			self._icon.set_pixel_size(24)

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

		self._spinner_counter += 1
		if self._spinner_counter == 1:
			self._spinner.start()
			self._spinner.show()

	def hide_spinner(self):
		"""Hide spinner widget"""
		if self._spinner is None:
			return

		self._spinner_counter -= 1
		if self._spinner_counter <= 0:
			self._spinner_counter = 0
			self._spinner.stop()
			self._spinner.hide()

	def apply_settings(self):
		"""Method called when system applies new settings"""
		self._superuser_notification = self._application.options.get('superuser_notification')
		self._button_relief = self._application.options.get('button_relief') or 0

		# apply button relief
		if Gtk.get_major_version() == 3:
			relief = (Gtk.ReliefStyle.NONE, Gtk.ReliefStyle.NORMAL)[self._button_relief]
			for control in self._container.get_children():
				if issubclass(control.__class__, Gtk.Button):
					control.set_relief(relief)

		else:
			# GTK 4 dropped button relief, flat class gives the same look
			control = self._container.get_first_child()
			while control is not None:
				if isinstance(control, Gtk.Button):
					if self._button_relief == 0:
						control.get_style_context().add_class('flat')
					else:
						control.get_style_context().remove_class('flat')
				control = control.get_next_sibling()
