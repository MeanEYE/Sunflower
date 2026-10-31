import math

from gi.repository import Gtk, GLib


class ProgressRing(Gtk.DrawingArea):
	"""Ring drawn around a widget showing either operation progress or
	indeterminate activity.

	In progress mode the ring fills clockwise from the top according to the
	fraction. In pulse mode a short arc rotates around the ring, animated by
	the frame clock so it stays smooth regardless of how often the caller
	pulses. A paused ring shows two static arcs on opposite sides of the
	circle, whatever mode it was in. Colors are taken from the widget's
	style context so the ring matches the icon it surrounds and follows the
	theme.

	"""

	SIZE = 24  # widget size in pixels, largest that fits a header bar button without growing it
	ICON_SIZE = 12  # pixel size for an icon placed inside the ring
	LINE_WIDTH = 2
	TRACK_ALPHA = 0.2
	ACCENT_COLORS = ('accent_bg_color', 'theme_selected_bg_color')  # GTK 4.18+, then older themes
	PULSE_ARC = math.pi / 2  # length of rotating arc
	PULSE_PERIOD = 2 * 1000000  # one full rotation, in microseconds
	PAUSE_ARCS = 2  # arcs shown while paused, evenly spaced with gaps of equal length

	def __init__(self):
		Gtk.DrawingArea.__init__(self)

		self._fraction = 0.0
		self._pulsing = False
		self._paused = False
		self._angle = 0.0
		self._tick_id = None

		self.set_size_request(self.SIZE, self.SIZE)
		self.set_halign(Gtk.Align.CENTER)
		self.set_valign(Gtk.Align.CENTER)

		# ring is purely decorative, make sure it never takes pointer events
		# away from the widget it is placed in
		if Gtk.get_major_version() == 3:
			self.set_has_window(False)
			self.connect('draw', self._handle_draw)

		else:
			self.set_can_target(False)
			self.set_draw_func(self._handle_draw_func)

	def set_fraction(self, fraction):
		"""Set progress fraction, shown once pulse mode is switched off.

		Pulse mode is left only through `set_pulsing`, totals can change
		while activity is still indeterminate and must not interrupt it.

		"""
		self._fraction = min(max(fraction, 0.0), 1.0)

		if not self._pulsing:
			self.queue_draw()

	def get_fraction(self):
		"""Return current progress fraction"""
		return self._fraction

	def set_pulsing(self, pulsing):
		"""Switch between indeterminate activity and progress display"""
		if pulsing == self._pulsing:
			return

		self._pulsing = pulsing
		self._update_tick()
		self.queue_draw()

	def set_paused(self, paused):
		"""Show paused state, animation is suspended until resumed"""
		if paused == self._paused:
			return

		self._paused = paused
		self._update_tick()
		self.queue_draw()

	def _update_tick(self):
		"""Run frame clock callback only while pulsing and not paused"""
		animate = self._pulsing and not self._paused

		if animate and self._tick_id is None:
			self._tick_id = self.add_tick_callback(self._handle_tick)

		elif not animate and self._tick_id is not None:
			self.remove_tick_callback(self._tick_id)
			self._tick_id = None

	def pulse(self):
		"""Enter pulse mode, rotation itself is driven by the frame clock"""
		self.set_pulsing(True)

	def _handle_tick(self, widget, frame_clock, data=None):
		"""Rotate arc based on frame time, once per frame"""
		elapsed = frame_clock.get_frame_time() % self.PULSE_PERIOD
		self._angle = 2 * math.pi * elapsed / self.PULSE_PERIOD
		self.queue_draw()
		return GLib.SOURCE_CONTINUE

	def _get_color(self):
		"""Return foreground color for current widget state"""
		if Gtk.get_major_version() == 3:
			context = self.get_style_context()
			return context.get_color(context.get_state())

		else:
			return self.get_color()

	def _get_accent_color(self):
		"""Return theme accent color, falling back to foreground color"""
		context = self.get_style_context()

		for name in self.ACCENT_COLORS:
			found, color = context.lookup_color(name)
			if found:
				return color

		return self._get_color()

	def _handle_draw(self, widget, cr):
		"""Handle GTK 3 draw signal"""
		self._draw(cr, widget.get_allocated_width(), widget.get_allocated_height())
		return False

	def _handle_draw_func(self, area, cr, width, height):
		"""Handle GTK 4 draw function"""
		self._draw(cr, width, height)

	def _draw(self, cr, width, height):
		"""Draw ring track and progress or activity arc"""
		color = self._get_color()
		center_x = width / 2.0
		center_y = height / 2.0
		radius = (min(width, height) - self.LINE_WIDTH) / 2.0 - 1
		start = -math.pi / 2  # arcs begin at the top

		cr.set_line_width(self.LINE_WIDTH)

		# track
		cr.set_source_rgba(color.red, color.green, color.blue, color.alpha * self.TRACK_ALPHA)
		cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
		cr.stroke()

		# paused, progress or activity arc
		accent = self._get_accent_color()
		cr.set_source_rgba(accent.red, accent.green, accent.blue, accent.alpha)

		if self._paused:
			# arcs and gaps between them share the circle equally, first arc
			# is centered on the right side so two arcs oppose horizontally
			arc = math.pi / self.PAUSE_ARCS
			for index in range(self.PAUSE_ARCS):
				middle = index * 2 * arc
				cr.arc(center_x, center_y, radius, middle - arc / 2, middle + arc / 2)
				cr.stroke()

		elif self._pulsing:
			cr.arc(center_x, center_y, radius, start + self._angle, start + self._angle + self.PULSE_ARC)
			cr.stroke()

		elif self._fraction > 0:
			cr.arc(center_x, center_y, radius, start, start + 2 * math.pi * self._fraction)
			cr.stroke()
