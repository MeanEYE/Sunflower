import os
import gtk
import pango


class Breadcrumbs(gtk.HBox):
	TYPE_NORMAL = 1
	TYPE_SMART = 2
	TYPE_COMPRESS = 3

	def __init__(self, parent):
		gtk.HBox.__init__(self)

		self._parent = parent
		self._type = Breadcrumbs.TYPE_SMART
	
		self._path = None
		self._previous_path = None
		self._colors = None
		self._state = gtk.STATE_NORMAL
		self._smart_color = None
		self._elements_size = None
		self._elements_width = None
		self._allocation = None
		self._highlight_index = None

		# create user interface
		self._path_object = gtk.DrawingArea()

		self._path_object.add_events(gtk.gdk.POINTER_MOTION_MASK)
		self._path_object.add_events(gtk.gdk.LEAVE_NOTIFY_MASK)
		self._path_object.add_events(gtk.gdk.BUTTON_PRESS_MASK)

		self._path_object.connect('expose-event', self.__expose_event)
		self._path_object.connect('motion-notify-event', self.__motion_event)
		self._path_object.connect('leave-notify-event', self.__leave_event)
		self._path_object.connect('button-press-event', self.__button_press_event)
		self._path_object.connect('realize', self.__realize_event)

		self.connect('size_allocate', self._update_visibility)

		# pack interface
		self.pack_start(self._path_object, True, True)
		self.show_all()
	
	def __get_color(self, color):
		"""Calculate color for the part history part of the path"""
		value = color.value
		saturation = color.saturation

		if saturation > 0.3:
			saturation = saturation / 2.0
			value = value * 1.5

		else:
			value = value / 1.5 if value > 0.5 else value * 2.5

		return gtk.gdk.color_from_hsv(color.hue, saturation, value)

	def __realize_event(self, widget, data=None):
		"""Resize drawing area when object is realized"""
		layout = widget.create_pango_layout('')

		height = layout.get_size()[1] / pango.SCALE
		self._path_object.set_size_request(-1, height)

	def __leave_event(self, widget, event):
		"""Handle mouse leaving the widget"""
		# remove highlight
		self._highlight_index = None

		# prepare refresh region
		region = self._allocation.copy()
		region.x = 0

		# request redraw
		self._path_object.queue_draw_area(*region)

		return True

	def __button_press_event(self, widget, event):
		"""Handle button press"""
		path = self._path
		if self._previous_path is not None and self._previous_path.startswith(self._path):
			path = self._previous_path

		# handle single left mouse click
		if event.button is 1 and event.type is gtk.gdk.BUTTON_PRESS:
			width = self._elements_size[self._highlight_index]
			new_path = path[0:width]
			file_list = self._parent._parent

			# change path
			if hasattr(file_list, 'change_path'):
				file_list.change_path(new_path)

		return True

	def __motion_event(self, widget, event):
		"""Handle mouse movement over widget"""
		elements = filter(lambda width: width <= event.x, self._elements_width)
		index = len(elements)

		# make sure we redraw only on index change
		if index != self._highlight_index:
			self._highlight_index = index

			# make sure we don't have index higher than needed
			if self._highlight_index >= len(self._elements_width):
				self._highlight_index = len(self._elements_width) - 1

			# prepare refresh region
			region = self._allocation.copy()
			region.x = 0

			# request redraw
			self._path_object.queue_draw_area(*region)

		return True

	def __expose_event(self, widget, event=None):
		"""Handle drawing bread crumbs"""
		foreground_context = widget.get_style().fg_gc[self._state]
		background_context = widget.get_style().bg_gc[self._state]
		layout = widget.create_pango_layout('')

		text_to_draw = self._path
		path_length = len(self._path)

		# make sure we have allocation
		if self._allocation is None:
			self._allocation = widget.get_allocation()

		# create attributes
		attributes = pango.AttrList()

		# check if path is part of previous one
		if self._previous_path is not None and self._previous_path.startswith(self._path):
			smart_color = (self._smart_color.red, self._smart_color.green, self._smart_color.blue)
			attributes.insert(pango.AttrForeground(
											*smart_color,
											start_index=path_length,
											end_index=len(self._previous_path)
										))
			text_to_draw = self._previous_path

		# calculate width of path elements
		if self._elements_width is None:
			path = None
			self._elements_size = []
			self._elements_width = []
			elements = text_to_draw.split(os.path.sep)
			elements[0] = os.path.sep

			for element in elements:
				# get path size
				path = os.path.join(path, element) if path is not None else element
				layout.set_text(path)

				# add width to the list
				width = layout.get_size()[0] / pango.SCALE
				self._elements_size.append(len(path))
				self._elements_width.append(width)

		# underline hovered path if specified
		if None not in (self._highlight_index, self._elements_size):
			width = self._elements_size[self._highlight_index]
			attributes.insert(pango.AttrUnderline(pango.UNDERLINE_SINGLE, 0, width))

		# prepare text for drawing
		layout.set_text(text_to_draw)
		layout.set_attributes(attributes)

		# fill background for drawing area
		widget.window.draw_rectangle(
							background_context,
							True,
							0,
							0,
							self._allocation[2],
							self._allocation[3]
						)

		# draw text
		widget.window.draw_layout(foreground_context, 0, 0, layout)

		return True

	def _update_visibility(self, sender=None, data=None):
		"""Handle path container resize"""
		self._allocation = self._path_object.get_allocation()
		
	def apply_color(self, colors):
		"""Apply colors to all bread crumbs"""
		self._colors = colors
		self._smart_color = self.__get_color(colors[0])

	def set_state(self, state):
		"""Set widget state"""
		self._state = state

	def refresh(self, path=None):
		"""Update label on directory change"""
		if self._previous_path is None or not self._previous_path.startswith(self._path):
			self._previous_path = self._path

		# split path
		self._path = path

		# clear cache
		self._elements_size = None
		self._elements_width = None
		self._highlight_index = None

		# force widget to be redrawn
		self._path_object.queue_draw()
