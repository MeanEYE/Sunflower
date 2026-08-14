import os
import gi

from gi.repository import Gtk, Gdk, GObject, GdkPixbuf

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
		self._image = Gtk.Image()
		self._image.show()
		if Gtk.get_major_version() == 3:
			self.popover.add(self._image)

		else:
			self.popover.set_child(self._image)

		# store parameters locally
		self._parent = parent
		self._thumbnail_size = size

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
		self.popover.hide()

	def can_have_thumbnail(self, uri):
		"""Check if specified URI can have thumbnail"""
		if not USE_FACTORY:
			return False

		mime_type = self._parent._parent.associations_manager.get_mime_type(uri)
		return self._factory.can_thumbnail(uri, mime_type, 0)

	def get_thumbnail(self, uri):
		"""Return thumbnail pixbuf for specified URI"""
		if not USE_FACTORY:
			return None

		result = None
		mime_type = self._parent._parent.associations_manager.get_mime_type(uri)

		# check for existing thumbnail
		thumbnail_file = self._factory.lookup(uri, 0)
		if thumbnail_file and os.path.isfile(thumbnail_file):
			result = GdkPixbuf.Pixbuf.new_from_file(thumbnail_file)

		# create thumbnail
		elif self.can_have_thumbnail(uri):
			result = self._factory.generate_thumbnail(uri, mime_type)

			if result is not None:
				self._factory.save_thumbnail(result, uri, 0)

		return result

	def show_thumbnail(self, uri, widget, position):
		"""Show thumbnail for specified image"""
		thumbnail = self.get_thumbnail(uri)

		if thumbnail is not None:
			self._image.set_from_pixbuf(thumbnail)
		else:
			if Gtk.get_major_version() == 3:
				self._image.set_from_icon_name('gtk-missing-image', Gtk.IconSize.DIALOG)

			else:
				self._image.set_from_icon_name('gtk-missing-image')

		if Gtk.get_major_version() == 3:
			self.popover.set_relative_to(widget)

		else:
			self.popover.set_parent(widget)
		self.popover.set_pointing_to(position)
		self.popover.show()
