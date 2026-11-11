import math

from gi.repository import Gtk
from sunflower.queue import OperationQueue


class QueueIcon(Gtk.DrawingArea):
	"""Circle filled with operation queue color, crossed out outline in
	text color is drawn when no queue is specified."""

	SIZE = 16
	RADIUS = 5
	LINE_WIDTH = 1.5

	def __init__(self, queue=None):
		Gtk.DrawingArea.__init__(self)

		self._queue = queue

		self.set_size_request(self.SIZE, self.SIZE)
		self.set_halign(Gtk.Align.CENTER)
		self.set_valign(Gtk.Align.CENTER)

		if Gtk.get_major_version() == 3:
			self.connect('draw', self._handle_draw)

		else:
			self.set_can_target(False)
			self.set_draw_func(self._handle_draw_func)

	def _handle_draw(self, widget, cr):
		"""Handle GTK 3 draw signal"""
		self._draw(cr, widget.get_allocated_width(), widget.get_allocated_height())
		return False

	def _handle_draw_func(self, area, cr, width, height):
		"""Handle GTK 4 draw function"""
		self._draw(cr, width, height)

	def _draw(self, cr, width, height):
		"""Draw queue circle"""
		color = OperationQueue.get_color(self._queue)

		if color is not None:
			cr.set_source_rgb(*color)
			cr.arc(width / 2.0, height / 2.0, self.RADIUS, 0, 2 * math.pi)
			cr.fill()

		else:
			if Gtk.get_major_version() == 3:
				context = self.get_style_context()
				color = context.get_color(context.get_state())

			else:
				color = self.get_color()

			cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
			cr.set_line_width(self.LINE_WIDTH)
			radius = self.RADIUS - self.LINE_WIDTH / 2
			cr.arc(width / 2.0, height / 2.0, radius, 0, 2 * math.pi)
			cr.stroke()

			# slash through the circle, from bottom left to top right
			offset = radius * math.cos(math.pi / 4)
			cr.move_to(width / 2.0 - offset, height / 2.0 + offset)
			cr.line_to(width / 2.0 + offset, height / 2.0 - offset)
			cr.stroke()


class QueueSelector(Gtk.Box):
	"""Row of linked buttons for choosing operation queue, one for
	no queue followed by one for each available queue."""

	def __init__(self):
		Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

		self._queue = None
		self._buttons = {}
		self._updating = False

		self.get_style_context().add_class('linked')
		self.set_halign(Gtk.Align.START)
		self.set_valign(Gtk.Align.CENTER)

		for queue in (None,) + OperationQueue.QUEUES:
			button = Gtk.ToggleButton.new()
			button.connect('toggled', self._handle_toggle, queue)

			if queue is None:
				button.set_tooltip_text(_('No queue'))

			else:
				button.set_tooltip_text(_('Queue {0}').format(queue))

			if Gtk.get_major_version() == 3:
				button.add(QueueIcon(queue))
				self.pack_start(button, False, False, 0)

			else:
				button.set_child(QueueIcon(queue))
				self.append(button)

			self._buttons[queue] = button

		self.set_queue(None)

	def _handle_toggle(self, widget, queue):
		"""Select queue whose button was toggled"""
		if not self._updating:
			self.set_queue(queue)

	def set_queue(self, queue):
		"""Select specified queue, `None` for no queue"""
		self._queue = queue

		# exactly one button is active, including when active one is clicked again
		self._updating = True
		for button_queue, button in self._buttons.items():
			button.set_active(button_queue == queue)
		self._updating = False

	def get_queue(self):
		"""Return selected queue, `None` when operation is not queued"""
		return self._queue
