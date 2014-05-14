import gtk
import cairo
import gobject


class CellRendererEmblems(gtk.CellRenderer):
	"""Cell renderer that accepts list of icon names."""
	__gproperties__ = {
				'emblems': (
						gobject.TYPE_PYOBJECT,
						'Emblem list',
						'List of icon names to display',
						gobject.PARAM_READWRITE
					)
			}

	def __init__(self):
		gtk.CellRenderer.__init__(self)
		self.emblems = None
		self.icon_size = 16
		self.spacing = 2
		self.padding = 1

	def do_set_property(self, prop, value):
		"""Set renderer property."""
		if prop.name == 'emblems':
			self.emblems = value

		else:
			setattr(self, prop.name, value)

	def do_get_property(self, prop):
		"""Get renderer property."""
		if prop.name == 'emblems':
			result = self.emblems

		else:
			result = getattr(self, prop.name)

		return result

	def do_render(self, window, widget, background_area, cell_area, expose_area, flags):
		"""Render emblems on tree view."""
		if self.emblems is None or len(self.emblems) == 0:
			return

		# cache constants locally
		icon_size = self.icon_size
		spacing = self.spacing
		emblems = self.emblems
		icon_theme = gtk.icon_theme_get_default()
		context = window.cairo_create()

		# position of next icon
		pos_x = cell_area[0] + cell_area[2]
		pos_y = cell_area[1] + ((cell_area[3] - icon_size) / 2)

		# draw all the icons
		for emblem in emblems:
			# load icon from the theme
			pixbuf = icon_theme.load_icon(emblem, 16, 0)

			# move position of next icon
			pos_x -= icon_size + spacing

			# draw icon
			context.set_source_pixbuf(pixbuf, pos_x, pos_y)
			context.paint()

	def do_get_size(self, widget, cell_area=None):
		"""Calculate size taken by emblems."""
		count = 5  # optimum size, we can still render more or less emblems

		width = self.icon_size * count + (self.spacing * (count - 1))
		height = self.icon_size

		result = (
				0,
				0,
				width + 2 * self.padding,
				height + 2 * self.padding
			)

		return result
