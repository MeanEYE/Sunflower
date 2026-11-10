import os
import gi

from threading import Thread, Condition

from gi.repository import Gtk, Gdk, GLib, GObject, GdkPixbuf

try:
	# try to import module
	version = '4.0' if os.getenv('SUNFLOWER_GTK') == '4' else '3.0'
	gi.require_version('GnomeDesktop', version)

	from gi.repository import GnomeDesktop
	USE_FACTORY = True

except:
	USE_FACTORY = False


class ThumbnailView:
	"""Load and display images from Gnome thumbnail factory storage.

	Idea is to create one object and then update thumbnail image as
	needed. This class *WILL* try to create thumbnails as well as load
	them cached.

	Preview follows the cursor right away. Thumbnails which already exist
	are shown immediately, while creating new one can take a while and is
	done by a separate thread, with preview indicating thumbnail is being
	loaded in the meantime. Thread only works on the most recent request,
	thumbnails for items cursor has already moved away from are not created.

	"""

	def __init__(self, parent, size=None):
		self.popover = Gtk.Popover.new()

		if Gtk.get_major_version() == 3:
			self.popover.set_modal(False)

		else:
			self.popover.set_autohide(False)
		# GTK 4 popovers have no transitions to disable
		if Gtk.get_major_version() == 3:
			self.popover.set_transitions_enabled(False)
		self.popover.set_position(Gtk.PositionType.LEFT)

		# create image preview
		if Gtk.get_major_version() == 3:
			self._image = Gtk.Image()

		else:
			# GTK 4 images are drawn as squares in icon size, while
			# picture is shown in its own size and proportions
			self._image = Gtk.Picture()
			self._image.set_can_shrink(False)
		self._image.show()

		# create loading indicator, taking space similar to thumbnail
		self._spinner = Gtk.Spinner.new()
		self._spinner.set_size_request(32, 32)
		self._spinner.set_margin_start(48)
		self._spinner.set_margin_end(48)
		self._spinner.set_margin_top(32)
		self._spinner.set_margin_bottom(32)
		self._spinner.show()

		# only one of them is visible, defining the size of preview
		self._stack = Gtk.Stack.new()
		self._stack.set_hhomogeneous(False)
		self._stack.set_vhomogeneous(False)
		self._stack.add_named(self._image, 'image')
		self._stack.add_named(self._spinner, 'loading')
		self._stack.show()

		if Gtk.get_major_version() == 3:
			self.popover.add(self._stack)

		else:
			self.popover.set_child(self._stack)

		# store parameters locally
		self._parent = parent
		self._thumbnail_size = size

		# thumbnail loading
		self._request = 0
		self._pending = None
		self._condition = Condition()
		self._thread = None

		# create thumbnail factory
		if USE_FACTORY:
			# set default thumbnail size
			if self._thumbnail_size is None:
				self._thumbnail_size = GnomeDesktop.DesktopThumbnailSize.NORMAL

			# create a factory
			self._factory = GnomeDesktop.DesktopThumbnailFactory.new(self._thumbnail_size)

		else:
			self._factory = None

	def hide(self):
		"""Hide tooltip."""
		# thumbnail which is still loading is not to be shown
		self._request += 1
		self._spinner.stop()
		self.popover.hide()

	def _load_thumbnails(self):
		"""Create requested thumbnails, executed in a separate thread."""
		while True:
			with self._condition:
				while self._pending is None:
					self._condition.wait()

				# only the latest request is of interest
				request, uri = self._pending
				self._pending = None

			try:
				thumbnail = self.get_thumbnail(uri)

			except Exception as error:
				print('Error creating thumbnail: {0} - {1}'.format(uri, str(error)))
				thumbnail = None

			GLib.idle_add(self._present_thumbnail, request, thumbnail)

	def can_have_thumbnail(self, uri):
		"""Check if specified URI can have thumbnail"""
		if not USE_FACTORY:
			return False

		mime_type = self._parent._parent.associations_manager.get_mime_type(uri)
		return self._factory.can_thumbnail(uri, mime_type, 0)

	def get_cached_thumbnail(self, uri):
		"""Return pixbuf of already existing thumbnail for specified URI"""
		result = None

		if USE_FACTORY:
			thumbnail_file = self._factory.lookup(uri, 0)

			if thumbnail_file and os.path.isfile(thumbnail_file):
				result = GdkPixbuf.Pixbuf.new_from_file(thumbnail_file)

		return result

	def get_thumbnail(self, uri):
		"""Return thumbnail pixbuf for specified URI, creating it if needed"""
		if not USE_FACTORY:
			return None

		# check for existing thumbnail
		result = self.get_cached_thumbnail(uri)

		# create thumbnail
		if result is None and self.can_have_thumbnail(uri):
			mime_type = self._parent._parent.associations_manager.get_mime_type(uri)
			result = self._factory.generate_thumbnail(uri, mime_type)

			if result is not None:
				self._factory.save_thumbnail(result, uri, 0)

		return result

	def show_thumbnail(self, uri, widget, position):
		"""Show preview for specified image next to the specified position"""
		self._request += 1

		try:
			thumbnail = self.get_cached_thumbnail(uri)

		except GLib.Error:
			# damaged thumbnails are created again
			thumbnail = None

		if thumbnail is not None:
			self._set_image(thumbnail)

		else:
			# thumbnail needs to be created, which is not done in main thread
			self._stack.set_visible_child_name('loading')
			self._spinner.start()

			if self._thread is None:
				self._thread = Thread(target=self._load_thumbnails)
				self._thread.daemon = True
				self._thread.start()

			with self._condition:
				self._pending = (self._request, uri)
				self._condition.notify()

		if Gtk.get_major_version() == 3:
			self.popover.set_relative_to(widget)
			self.popover.set_pointing_to(position)

		else:
			# popover can not be hosted by a tree view or scrolled
			# window, see `PopupMenu.show` for details
			parent = widget

			while parent is not None and isinstance(parent, (Gtk.TreeView, Gtk.ScrolledWindow)):
				parent = parent.get_parent()

			if parent is None:
				parent = widget

			if self.popover.get_parent() is not parent:
				if self.popover.get_parent() is not None:
					self.popover.unparent()
				self.popover.set_parent(parent)

			rectangle = Gdk.Rectangle()
			rectangle.x, rectangle.y = widget.translate_coordinates(parent, position.x, position.y)
			rectangle.width = position.width
			rectangle.height = position.height

			# GTK 3 kept popovers inside of the window, moving them to the other
			# side when there was no room. GTK 4 doesn't, so preview for the list
			# on the left would end up outside of the window.
			self.popover.set_position(self._get_position())
			self.popover.set_pointing_to(rectangle)
		self.popover.show()

	def _present_thumbnail(self, request, thumbnail):
		"""Show created thumbnail, unless something else was requested in the meantime"""
		if request == self._request:
			self._set_image(thumbnail)

		return False

	def _set_image(self, thumbnail):
		"""Show specified thumbnail in the preview"""
		if thumbnail is not None:
			if Gtk.get_major_version() == 3:
				self._image.set_from_pixbuf(thumbnail)

			else:
				self._image.set_paintable(Gdk.Texture.new_for_pixbuf(thumbnail))
		else:
			if Gtk.get_major_version() == 3:
				self._image.set_from_icon_name('gtk-missing-image', Gtk.IconSize.DIALOG)

			else:
				icon_theme = Gtk.IconTheme.get_for_display(self._image.get_display())
				self._image.set_paintable(icon_theme.lookup_icon(
						'image-missing', None, 48, self._image.get_scale_factor(),
						self._image.get_direction(), 0
					))

		self._spinner.stop()
		self._stack.set_visible_child_name('image')

	def _get_position(self):
		"""Return side of the selected item preview is shown on (GTK 4)."""
		application = self._parent._parent
		result = Gtk.PositionType.RIGHT

		in_right_list = self._parent._notebook is application.right_notebook
		if in_right_list and not application.options.get('horizontal_split'):
			result = Gtk.PositionType.LEFT

		return result
