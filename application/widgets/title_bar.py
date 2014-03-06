import gtk
import math
import pango

from widgets.breadcrumbs import Breadcrumbs


class Mode:
	NORMAL = 0
	SUPER_USER = 1


class TitleBar:
	"""Title bar wrapper class"""

	def __init__(self, application, parent):
		self._application = application
		self._parent = parent

		self._radius = 3
		self._control_count = 0
		self._state = gtk.STATE_NORMAL
		self._mode = Mode.NORMAL
		self._menu = None
		self._style = None
		self._toolbar_style = None
		self._box_spacing = 1
		self._box_border_width = 4
		self._super_user_colors = None


		# get options
		options = self._application.options

		self._ubuntu_coloring = options.get('ubuntu_coloring')
		self._superuser_notification = options.get('superuser_notification')
		self._button_relief = options.get('button_relief')

		# determine whether we need to show breadcrumbs
		from plugin_base.item_list import ItemList
		section = options.section('item_list')
		is_list = isinstance(parent, ItemList)
		self._breadcrumb_type = section.get('breadcrumbs')
		self._show_breadcrumbs = self._breadcrumb_type != Breadcrumbs.TYPE_NONE and is_list

		# create container box
		self._hbox = gtk.HBox(homogeneous=False, spacing=self._box_spacing)

		# configure title bar
		self._hbox.set_border_width(self._box_border_width)

		self._container = gtk.EventBox()
		self._container.set_app_paintable(True)
		self._container.add_events(gtk.gdk.BUTTON_RELEASE_MASK)

		# connect signals
		self._container.connect('realize', self.__realize_event)
		self._container.connect('button-release-event', self.__button_release_event)
		self._hbox.connect('expose-event', self.__expose_event)

		# top folder icon as default
		self._icon = gtk.Image()

		# create plugin main menu button
		style = gtk.RcStyle()
		style.xthickness = 0
		style.ythickness = 0

		self._button_menu = gtk.Button()
		self._button_menu.add(self._icon)
		if not self._button_relief:
			self._button_menu.set_relief(gtk.RELIEF_NONE)
		self._button_menu.modify_style(style)
		self._button_menu.set_focus_on_click(False)
		self._button_menu.set_tooltip_text(_('Context menu'))
		self._button_menu.connect('clicked', self.show_menu)

		# create title box
		vbox = gtk.VBox(False, 1)
		if self._show_breadcrumbs:
			self._breadcrumbs = Breadcrumbs(self)
			vbox.pack_start(self._breadcrumbs, True, True, 0)

		else:
			self._title_label = gtk.Label()
			self._title_label.set_alignment(0, 0.5)
			self._title_label.set_use_markup(True)
			self._title_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
			vbox.pack_start(self._title_label, True, True, 0)

		font = pango.FontDescription('8')
		self._subtitle_label = gtk.Label()
		self._subtitle_label.set_alignment(0, 0.5)
		self._subtitle_label.set_use_markup(False)
		self._subtitle_label.modify_font(font)

		# create spinner control if it exists
		if hasattr(gtk, 'Spinner'):
			self._spinner = gtk.Spinner()
			self._spinner.set_size_request(20, 20)
			self._spinner.set_property('no-show-all', True)

		else:
			self._spinner = None

		# pack interface
		vbox.pack_start(self._subtitle_label, False, False, 0)

		self._hbox.pack_start(self._button_menu, False, False, 0)
		self._hbox.pack_start(vbox, True, True, 4)

		if self._spinner is not None:
			self._hbox.pack_start(self._spinner, False, False, 5)

		self._container.add(self._hbox)

	def __get_colors(self, normal_style=False):
		"""Get copy of the style for current state"""
		if self._style is None:
			return

		if self._state is gtk.STATE_NORMAL or normal_style:
			# normal state
			background = self._style.bg[gtk.STATE_NORMAL]
			foreground = self._style.fg[gtk.STATE_NORMAL]

		else:
			if self._mode is Mode.NORMAL \
			or self._mode is Mode.SUPER_USER and not self._superuser_notification:

				# selected state
				if self._ubuntu_coloring:
					# ubuntu coloring method
					background = self._toolbar_style.bg[gtk.STATE_NORMAL]
					foreground = self._toolbar_style.fg[gtk.STATE_NORMAL]

				else:
					# normal coloring method
					background = self._style.bg[gtk.STATE_SELECTED]
					foreground = self._style.fg[gtk.STATE_SELECTED]

			else:
				# for super user mode we use our custom colors
				background, foreground = self._super_user_colors

		return background, foreground

	def __get_controls_width(self):
		"""Get widget of all controls together"""
		result = 0
		spacing = self._box_spacing

		# account for control spacing
		result += spacing * (self._control_count - 1)

		# get list of controls
		controls = self._hbox.get_children()
		total_count = len(controls)

		# get width of each control
		for index in range(total_count - self._control_count, total_count):
			result += controls[index].allocation.width

		return result

	def __get_menu_width(self):
		"""Get width of menu button"""
		result  = self._button_menu.allocation.width
		return result

	def __button_release_event(self, widget, event, data=None):
		"""Handle button release event"""
		if event.button == 1:
			# focus main object on left click
			self._parent.focus_main_object()

		elif event.button == 2:
			# duplicate tab on middle click
			self._parent._duplicate_tab(widget)

		return True

	def __realize_event(self, widget, event=None):
		"""Handle control realize event"""
		self._style = self._application.left_notebook.get_style().copy()
		self._toolbar_style = self._application.menu_bar.get_style().copy()

		# apply colors on realize
		self.__apply_color()

	def __draw_rectangle(self, context, rectangle, radius):
		"""Draw rectangle with rounded borders"""
		half_pi = math.pi / 2

		context.arc(rectangle[0] + radius, rectangle[1] + radius, radius, 2 * half_pi, 3 * half_pi)
		context.arc(rectangle[2] - radius, rectangle[1] + radius, radius, 3 * half_pi, 4 * half_pi)
		context.arc(rectangle[2] - radius, rectangle[3] - radius, radius, 0 * half_pi, 1 * half_pi)
		context.arc(rectangle[0] + radius, rectangle[3] - radius, radius, 1 * half_pi, 2 * half_pi)
		context.close_path()
		context.fill()

	def __expose_event(self, widget=None, event=None):
		"""We use this event to paint backgrounds"""
		x, y, w, h = self._hbox.allocation
		x_offset = x + w
		y_offset = y + h
		border_offset = 1

		# calculate parameters
		hbox_rectangle = (x, y, x_offset, y_offset)
		controls_rectangle = (
						x_offset - self.__get_controls_width() - self._box_border_width - border_offset,
						y + self._box_border_width - border_offset,
						x_offset - self._box_border_width + border_offset,
						y_offset - self._box_border_width + border_offset
					)
		menu_rectangle = (
						x + self._box_border_width - border_offset, 
						y + self._box_border_width - border_offset,
						x + self._box_border_width + self.__get_menu_width() + border_offset,
						y_offset - self._box_border_width + border_offset
					)

		# create drawing context
		context = self._container.window.cairo_create()

		# get colors
		normal_color = self.__get_colors(normal_style=True)[0]
		active_color = self.__get_colors()[0]

		# clear drawing area first
		context.set_source_color(normal_color)
		context.rectangle(*hbox_rectangle)
		context.fill()

		# draw focus if needed
		if self._state is not gtk.STATE_NORMAL:
			# draw background
			context.set_source_color(active_color)
			self.__draw_rectangle(context, hbox_rectangle, self._radius + 1)

			# draw control space only if button relief is disabled
			if not self._button_relief:
				context.set_source_rgba(normal_color.red_float, normal_color.green_float, normal_color.blue_float, 0.4)
				self.__draw_rectangle(context, controls_rectangle, self._radius)

				# draw menu space
				self.__draw_rectangle(context, menu_rectangle, self._radius)

		return False

	def __apply_color(self):
		"""Apply text color for title and subtitle"""
		colors = self.__get_colors()

		# apply text color to labels
		if self._show_breadcrumbs:
			self._breadcrumbs.apply_color(colors)

		else:
			self._title_label.modify_fg(gtk.STATE_NORMAL, colors[1])

		self._subtitle_label.modify_fg(gtk.STATE_NORMAL, colors[1])

		# apply color to controls
		self._button_menu.modify_fg(gtk.STATE_NORMAL, colors[1])
		self._button_menu.modify_bg(gtk.STATE_NORMAL, colors[0])
		self._button_menu.modify_fg(gtk.STATE_PRELIGHT, colors[1])
		self._button_menu.modify_bg(gtk.STATE_PRELIGHT, colors[0])
		self._button_menu.modify_fg(gtk.STATE_ACTIVE, colors[1])
		self._button_menu.modify_bg(gtk.STATE_ACTIVE, colors[0])

		for control in self._hbox.get_children():
			control.modify_fg(gtk.STATE_NORMAL, colors[1])
			control.modify_bg(gtk.STATE_NORMAL, colors[0])
			control.modify_fg(gtk.STATE_PRELIGHT, colors[1])
			control.modify_bg(gtk.STATE_PRELIGHT, colors[0])
			control.modify_fg(gtk.STATE_ACTIVE, colors[1])
			control.modify_bg(gtk.STATE_ACTIVE, colors[0])

		# apply spinner color
		if self._spinner is not None:
			self._spinner.modify_fg(gtk.STATE_NORMAL, colors[1])

	def __get_menu_position(self, menu, button):
		"""Get bookmarks position"""
		window_x, window_y = self._application.window.get_position()
		button_x, button_y = button.translate_coordinates(self._application, 0, 0)
		button_h = button.get_allocation().height

		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def add_control(self, widget):
		"""Add button control"""
		self._control_count += 1
		self._hbox.pack_end(widget, False, False, 0)

		if issubclass(widget.__class__, gtk.Button):
			widget.set_relief((gtk.RELIEF_NONE, gtk.RELIEF_NORMAL)[self._button_relief])

	def set_state(self, state):
		"""Set GTK control state for title bar"""
		self._state = state

		# apply new colors
		self._container.queue_draw()
		self.__apply_color()

		# let breadcrumbs know about new state
		if self._show_breadcrumbs:
			self._breadcrumbs.set_state(state)

	def set_mode(self, mode):
		"""Set title bar mode"""
		self._mode = mode
		self._super_user_colors = (
						gtk.gdk.color_parse('red'),
						gtk.gdk.color_parse('white')
					)

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
		self._icon.set_from_icon_name(icon_name, gtk.ICON_SIZE_LARGE_TOOLBAR)

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

		self._menu.popup(
					None, None,
					self.__get_menu_position,
					1, 0, button
				)

	def show_spinner(self):
		"""Show spinner widget"""
		if self._spinner is not None:
			self._spinner.show()
			self._spinner.start()

	def hide_spinner(self):
		"""Hide spinner widget"""
		if self._spinner is not None:
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
		
		if self._breadcrumbs is not None:
			self._breadcrumbs.apply_settings()

		# get new color styles
		self._style = self._application.left_notebook.get_style().copy()
		self._toolbar_style = self._application.menu_bar.get_style().copy()

		# apply button relief
		relief = (gtk.RELIEF_NONE, gtk.RELIEF_NORMAL)[self._button_relief]

		for control in self._hbox.get_children():
			if issubclass(control.__class__, gtk.Button):
				control.set_relief(relief)

		# apply new colors
		self._container.queue_draw()
		self.__apply_color()
