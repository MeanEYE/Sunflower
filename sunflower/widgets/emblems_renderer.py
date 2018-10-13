import cairo

from gi.repository import Gtk, Gdk, GObject


class CellRendererEmblems(Gtk.CellRenderer):
	"""Cell renderer that accepts list of icon names."""
	__gproperties__ = {
				'emblems': (
						GObject.TYPE_PYOBJECT,
						'Emblem list',
						'List of icon names to display',
						GObject.PARAM_READWRITE
					),
				'is-link': (
						GObject.TYPE_BOOLEAN,
						'Link indicator',
						'Denotes if item is a link or regular file',
						False,
						GObject.PARAM_READWRITE
					)
			}

	def __init__(self):
		Gtk.CellRenderer.__init__(self)

		self.emblems = None
		self.is_link = None
		self.icon_size = 16
		self.spacing = 2
		self.padding = 1

	def do_set_property(self, prop, value):
		"""Set renderer property."""
		if prop.name == 'emblems':
			self.emblems = value

		elif prop.name == 'is-link':
			self.is_link = value

		else:
			setattr(self, prop.name, value)

	def do_get_property(self, prop):
		"""Get renderer property."""
		if prop.name == 'emblems':
			result = self.emblems

		elif prop.name == 'is-link':
			result = self.is_link

		else:
			result = getattr(self, prop.name)

		return result

	def do_render(self, context, widget, background_area, cell_area, flags):
		"""Render emblems on tree view."""
		return
		if not self.is_link and (self.emblems is None or len(self.emblems) == 0):
			return

		# cache constants locally
		icon_size = self.icon_size
		spacing = self.spacing
		emblems = self.emblems or ()
		icon_theme = Gtk.IconTheme.get_default()

		# add symbolic link emblem if needed
		if self.is_link:
			emblems = ('emblem-symbolic-link',) + emblems

		# position of next icon
		pos_x = cell_area.x + cell_area.width
		pos_y = cell_area.y + ((cell_area.height - icon_size) / 2)

		# draw all the icons
		for emblem in emblems:
			# load icon from the theme
			pixbuf = icon_theme.load_icon(emblem, 16, 0)

			# move position of next icon
			pos_x -= icon_size + spacing

			# draw icon
			Gdk.cairo_set_source_pixbuf(context, pixbuf, pos_x, pos_y)
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
