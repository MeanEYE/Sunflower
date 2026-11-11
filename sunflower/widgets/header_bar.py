import os
import sys
import math
import cairo
import random
import zipfile

from gi.repository import Gtk, Gdk, GdkPixbuf
from sunflower import common


class HeaderBar(Gtk.HeaderBar):
	"""Header bar which shows field of sunflowers along its bottom edge."""

	FLOWER_FILE = 'sunflower-head.svg'
	FIELD_WIDTH = 280  # distance from the right edge covered with flowers
	FLOWER_SIZE_MAX = 0.68  # size of flowers near the edge, relative to header bar height
	FLOWER_SIZE_MIN = 0.15  # size of flowers closest to the center
	FLOWER_SPACING = 0.5  # distance between flowers, relative to their size
	FLOWER_ROWS = 3
	FIELD_FADE = 0.3  # part of the field, closest to the center, which fades out
	FIELD_OPACITY = 0.45
	FIELD_SEED = 64

	def __init__(self):
		Gtk.HeaderBar.__init__(self)

		self._flower_data = None
		self._field = None
		self._field_key = None

	def _load_flower(self):
		"""Read flower image from static assets."""
		result = None

		try:
			# try loading from zip file
			if os.path.isfile(sys.path[0]) and sys.path[0] != '':
				archive = zipfile.ZipFile(sys.path[0])
				with archive.open('images/{}'.format(self.FLOWER_FILE)) as raw_file:
					result = raw_file.read()
				archive.close()

			# load image from a file
			else:
				file_name = os.path.join(common.get_static_assets_directory(), 'images', self.FLOWER_FILE)
				with open(file_name, 'rb') as raw_file:
					result = raw_file.read()

		except (OSError, KeyError, zipfile.BadZipFile):
			result = None

		return result

	def _create_flower(self, size):
		"""Return surface with single flower rendered in specified size."""
		if self._flower_data is None:
			self._flower_data = self._load_flower() or b''

		if len(self._flower_data) == 0 or size <= 0:
			return None

		loader = GdkPixbuf.PixbufLoader.new()
		loader.set_size(size, size)
		loader.write(self._flower_data)
		loader.close()

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
		context = cairo.Context(surface)
		Gdk.cairo_set_source_pixbuf(context, loader.get_pixbuf(), 0, 0)
		context.paint()

		return surface

	def _get_flowers(self, height):
		"""Return list of flowers as tuples of center, size and angle.

		Horizontal position is distance from the right edge. Flowers get smaller
		the further they are from that edge and each row behind the first one is
		smaller and higher than the one in front of it.

		"""
		result = []
		generator = random.Random(self.FIELD_SEED)
		size_max = height * self.FLOWER_SIZE_MAX
		size_min = height * self.FLOWER_SIZE_MIN

		for row in reversed(range(self.FLOWER_ROWS)):
			distance = -size_max * 0.25 * generator.random()

			while distance < self.FIELD_WIDTH:
				position = max(distance, 0) / self.FIELD_WIDTH
				size = size_min + (size_max - size_min) * (1 - position) ** 1.6
				size *= (1 - row * 0.22) * generator.uniform(0.85, 1.1)

				x = distance + generator.uniform(-0.1, 0.1) * size
				y = height - size * (0.12 + row * 0.36 + generator.uniform(-0.08, 0.08))

				result.append((x, y, size, generator.uniform(0, math.pi / 6)))
				distance += size * self.FLOWER_SPACING * generator.uniform(0.9, 1.3)

		return result

	def _get_field(self, height, scale):
		"""Return surface with rendered field for specified header bar height."""
		key = (height, scale)
		if self._field_key == key:
			return self._field

		self._field_key = key
		self._field = None

		try:
			flower_size = int(math.ceil(height * self.FLOWER_SIZE_MAX * 1.1)) * scale
			flower = self._create_flower(flower_size)

			if flower is None:
				return None

			surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.FIELD_WIDTH * scale, height * scale)
			context = cairo.Context(surface)
			context.scale(scale, scale)

			for x, y, size, angle in self._get_flowers(height):
				ratio = size * scale / flower_size

				context.save()
				context.translate(self.FIELD_WIDTH - x, y)
				context.rotate(angle)
				context.scale(ratio / scale, ratio / scale)
				context.set_source_surface(flower, -flower_size / 2, -flower_size / 2)
				context.get_source().set_filter(cairo.FILTER_BEST)
				context.paint()
				context.restore()

			# fade out the end closest to the center
			gradient = cairo.LinearGradient(0, 0, self.FIELD_WIDTH * self.FIELD_FADE, 0)
			gradient.add_color_stop_rgba(0, 0, 0, 0, 0)
			gradient.add_color_stop_rgba(1, 0, 0, 0, 1)

			context.rectangle(0, 0, self.FIELD_WIDTH * self.FIELD_FADE, height)
			context.clip()
			context.set_operator(cairo.OPERATOR_DEST_IN)
			context.set_source(gradient)
			context.paint()

			self._field = surface

		except Exception:
			self._field = None

		return self._field

	def _draw_field(self, context, width, height):
		"""Draw field of flowers in the bottom right corner."""
		scale = self.get_scale_factor()
		field = self._get_field(height, scale)

		if field is None:
			return

		context.save()
		context.rectangle(0, 0, width, height)
		context.clip()

		context.translate(width - self.FIELD_WIDTH, 0)
		context.scale(1.0 / scale, 1.0 / scale)
		context.set_source_surface(field, 0, 0)
		context.paint_with_alpha(self.FIELD_OPACITY)

		context.restore()

	def do_draw(self, context):
		"""Draw background, flowers and then children on top of them."""
		style_context = self.get_style_context()
		width = self.get_allocated_width()
		height = self.get_allocated_height()

		Gtk.render_background(style_context, context, 0, 0, width, height)
		Gtk.render_frame(style_context, context, 0, 0, width, height)

		self._draw_field(context, width, height)

		self.forall(lambda child: self.propagate_draw(child, context))

		return False

	def do_snapshot(self, snapshot):
		"""Draw flowers on top of the background and then children on top of them."""
		# widget size excludes padding and border, cover those as well
		valid, bounds = self.compute_bounds(self)

		if valid:
			width = int(bounds.get_width())
			height = int(bounds.get_height())

			context = snapshot.append_cairo(bounds)
			context.translate(bounds.get_x(), bounds.get_y())
			self._draw_field(context, width, height)

		Gtk.HeaderBar.do_snapshot(self, snapshot)
