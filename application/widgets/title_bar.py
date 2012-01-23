import gtk
import math
import pango


class TitleBar(gtk.HBox):
	"""Title bar wrapper class"""

	def __init__(self, application):
		gtk.HBox.__init__(self, False, 1)

		self._application = application
		self._radius = 3
		self._control_count = 0
		self._state = gtk.STATE_NORMAL
		self._ubuntu_coloring = self._application.options.getboolean('main', 'ubuntu_coloring')
		self._menu = None

		# configure title bar
		self.set_border_width(4)

		# connect signals
		self.connect('expose-event', self.__expose_event)

		# top folder icon as default
		self._icon = gtk.Image()

		# create plugin main menu button
		style = gtk.RcStyle()
		style.xthickness = 0
		style.ythickness = 0

		self._button_menu = gtk.Button()
		self._button_menu.add(self._icon)
		self._button_menu.set_relief(gtk.RELIEF_NONE)
		self._button_menu.modify_style(style)
		self._button_menu.set_focus_on_click(False)
		self._button_menu.connect('clicked', self.show_menu)

		# create title box
		vbox = gtk.VBox(False, 1)

		self._title_label = gtk.Label()
		self._title_label.set_alignment(0, 0.5)
		self._title_label.set_use_markup(True)
		self._title_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)

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
		vbox.pack_start(self._title_label, True, True, 0)
		vbox.pack_start(self._subtitle_label, False, False, 0)

		self.pack_start(self._button_menu, False, False, 0)
		self.pack_start(vbox, True, True, 3)

		if self._spinner is not None:
			self.pack_start(self._spinner, False, False, 5)

	def __get_colors(self, normal_style=False):
		"""Get copy of the style for current state"""
		if self._state is gtk.STATE_NORMAL or normal_style:
			# normal state
			style = self._application.left_notebook.get_style().copy()
			background = style.bg[gtk.STATE_NORMAL]
			foreground = style.fg[gtk.STATE_NORMAL]

		else:
			# selected state
			if self._ubuntu_coloring:
				# ubuntu coloring method
				style = self._application._menu_item_commands.get_style().copy()
				background = style.bg[gtk.STATE_NORMAL]
				foreground = style.fg[gtk.STATE_NORMAL]

			else:
				# normal coloring method
				style = self._application.left_notebook.get_style().copy()
				background = style.bg[gtk.STATE_SELECTED]
				foreground = style.fg[gtk.STATE_SELECTED]

		return background, foreground

	def __get_controls_width(self):
		"""Get widget of all controls together"""
		result = 0
		spacing = self.get_spacing()

		# account for control spacing
		result += spacing * (self._control_count - 1)

		# get list of controls
		controls = self.get_children()
		total_count = len(controls)

		# get width of each control
		for index in range(total_count - self._control_count, total_count):
			result += controls[index].allocation.width

		return result

	def __expose_event(self, widget=None, event=None):
		"""We use this event to paint backgrounds"""
		x, y, w, h = self.allocation
		x_offset = x + w
		y_offset = y + h
		half_pi = math.pi / 2

		context = self.window.cairo_create()

		# clear drawing area first
		normal_color = self.__get_colors(normal_style=True)[0]
		context.set_source_rgb(
							normal_color.red_float,
							normal_color.green_float,
							normal_color.blue_float
						)
		context.rectangle(x, y, w, h)
		context.fill()

		# draw focus if needed
		if self._state is not gtk.STATE_NORMAL:
			color = self.__get_colors()[0]
			context.set_source_rgb(
								color.red_float,
								color.green_float,
								color.blue_float
							)

			# draw rounded rectangle
			radius = self._radius + 1
			context.arc(x + radius, y + radius, radius, 2 * half_pi, 3 * half_pi)
			context.arc(x_offset - radius, y + radius, radius, 3 * half_pi, 4 * half_pi)
			context.arc(x_offset - radius, y_offset - radius, radius, 0 * half_pi, 1 * half_pi)
			context.arc(x + radius, y_offset - radius, radius, 1 * half_pi, 2 * half_pi)
			context.close_path()
			context.fill()

			# draw control space
			controls_width = self.__get_controls_width()
			border_mod = 1
			border = self.get_border_width() - border_mod

			# modify rectangle
			x = x_offset - border - controls_width - (border_mod * 2)
			y += border
			x_offset -= border
			y_offset -= border

			context.set_source_rgba(
								normal_color.red_float,
								normal_color.green_float,
								normal_color.blue_float,
								0.5
							)
			context.arc(x + self._radius, y + self._radius, self._radius, 2 * half_pi, 3 * half_pi)
			context.arc(x_offset - self._radius, y + self._radius, self._radius, 3 * half_pi, 4 * half_pi)
			context.arc(x_offset - self._radius, y_offset - self._radius, self._radius, 0 * half_pi, 1 * half_pi)
			context.arc(x + self._radius, y_offset - self._radius, self._radius, 1 * half_pi, 2 * half_pi)
			context.close_path()
			context.fill()


	def __apply_text_color(self):
		"""Apply text color for title and subtitle"""
		color = self.__get_colors()[1]

		# apply text color to labels
		self._title_label.modify_fg(gtk.STATE_NORMAL, color)
		self._subtitle_label.modify_fg(gtk.STATE_NORMAL, color)

		# apply spinner color
		if self._spinner is not None:
			self._spinner.modify_fg(gtk.STATE_NORMAL, color)

	def __handle_menu_hide(self, widget, data=None):
		"""Handle hiding title bar menu"""
		active_object = self._application.get_active_object()
		oposite_object = self._application.get_oposite_object(active_object)

		# prevent title bar from losing focus
		active_object._disable_object_block()
		oposite_object._disable_object_block()

	def add_control(self, widget):
		"""Add button control"""
		self._control_count += 1
		self.pack_end(widget, False, False, 0)

	def set_state(self, state):
		"""Set GTK control state for title bar"""
		self._state = state

		# apply new colors
		self.queue_draw()
		self.__apply_text_color()

	def set_style(self, style):
		"""Set drawing style"""
		self._style = style
		self.queue_draw()

	def set_title(self, text):
		"""Set title text"""
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
		self._menu.connect('hide', self.__handle_menu_hide)

	def show_menu(self, widget=None, data=None):
		"""Show title bar menu"""
		if self._menu is None:
			return

		# get objects
		active_object = self._application.get_active_object()
		oposite_object = self._application.get_oposite_object(active_object)

		# prevent title bar from losing focus
		active_object._enable_object_block()
		oposite_object._enable_object_block()

		# show menu below the button
		button = widget if widget is not None else self._button_menu

		self._menu.popup(
					None, None,
					self._application._get_bookmarks_menu_position,
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
		self._ubuntu_coloring = self._application.options.getboolean('main', 'ubuntu_coloring')

		# apply new colors
		self.queue_draw()
		self.__apply_text_color()
