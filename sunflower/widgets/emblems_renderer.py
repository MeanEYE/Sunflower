import cairo

from gi.repository import Gtk, Gdk, GObject
from sunflower.emblems import get_emblem_icon, get_icon_theme

if Gtk.get_major_version() != 3:
	# GTK 4 renders through snapshots which are positioned with graphene points
	from gi.repository import Graphene


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
		if not self.is_link and (self.emblems is None or len(self.emblems) == 0):
			return

		# cache constants locally
		icon_size = self.icon_size
		spacing = self.spacing
		emblems = self.emblems or ()
		icon_theme = get_icon_theme()

		# add symbolic link emblem if needed
		if self.is_link:
			emblems = ('emblem-symbolic-link',) + emblems

		# position of next icon
		pos_x = cell_area.x + cell_area.width
		pos_y = cell_area.y + ((cell_area.height - icon_size) / 2)

		# draw all the icons
		for emblem in emblems:
			# load icon from the theme
			icon_name = get_emblem_icon(emblem)

			if icon_name is None:
				continue

			icon_info = icon_theme.lookup_icon(icon_name, icon_size, 0)

			if icon_info is None:
				continue

			# symbolic icons are recolored to match item text
			if icon_info.is_symbolic():
				pixbuf, symbolic = icon_info.load_symbolic_for_context(widget.get_style_context())

			else:
				pixbuf = icon_info.load_icon()

			# move position of next icon
			pos_x -= icon_size + spacing

			# draw icon
			Gdk.cairo_set_source_pixbuf(context, pixbuf, pos_x, pos_y)
			context.paint()

	def do_snapshot(self, snapshot, widget, background_area, cell_area, flags):
		"""Render emblems on tree view (GTK 4)."""
		if not self.is_link and (self.emblems is None or len(self.emblems) == 0):
			return

		# cache constants locally
		icon_size = self.icon_size
		spacing = self.spacing
		emblems = self.emblems or ()
		icon_theme = get_icon_theme()

		# add symbolic link emblem if needed
		if self.is_link:
			emblems = ('emblem-symbolic-link',) + emblems

		# position of next icon
		pos_x = cell_area.x + cell_area.width
		pos_y = cell_area.y + ((cell_area.height - icon_size) / 2)

		# draw all the icons
		for emblem in emblems:
			icon_name = get_emblem_icon(emblem)

			if icon_name is None:
				continue

			icon = icon_theme.lookup_icon(
						icon_name, None, icon_size, widget.get_scale_factor(),
						Gtk.TextDirection.NONE, 0
					)

			if icon is None:
				continue

			# move position of next icon
			pos_x -= icon_size + spacing

			# draw icon, symbolic ones are recolored to match item text
			snapshot.save()
			snapshot.translate(Graphene.Point().init(pos_x, pos_y))

			if icon.is_symbolic():
				color = widget.get_style_context().get_color()
				icon.snapshot_symbolic(snapshot, icon_size, icon_size, (color,))

			else:
				icon.snapshot(snapshot, icon_size, icon_size)

			snapshot.restore()

	def do_get_size(self, widget, cell_area=None):
		"""Calculate size taken by emblems."""
		count = 5  # optimum size, we can still render more or less emblems

		width = self.icon_size * count + (self.spacing * (count - 1))
		height = self.icon_size
		result = (0, 0, width + 2 * self.padding, height + 2 * self.padding)

		return result

	# GTK 4 dropped the size method, without these the cell gets no room
	# and emblems are never drawn
	if Gtk.get_major_version() != 3:
		def do_get_preferred_width(self, widget):
			"""Calculate width taken by emblems."""
			count = 5  # optimum size, we can still render more or less emblems
			width = self.icon_size * count + (self.spacing * (count - 1)) + 2 * self.padding

			return (width, width)

		def do_get_preferred_height(self, widget):
			"""Calculate height taken by emblems."""
			height = self.icon_size + 2 * self.padding

			return (height, height)
