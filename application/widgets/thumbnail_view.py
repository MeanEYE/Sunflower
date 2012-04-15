import os
import gtk

try:
	# try to import module
	import gnome.ui
	USE_FACTORY = True

except:
	USE_FACTORY = False


class ThumbnailView(gtk.Window):
	"""Load and display images from Gnome thumbnail factory storage.

	Idea is to create one object and then update thumbnail image as
	needed. This class *WILL* try to create thumbnails as well as load
	them cached.

	"""

	def __init__(self, parent, size=None):
		gtk.Window.__init__(self, gtk.WINDOW_POPUP)

		self.set_keep_above(True)
		self.set_resizable(False)

		# create image preview
		self._image = gtk.Image()
		self._image.show()
		self.add(self._image)

		# store parameters locally
		self._parent = parent
		self._thumbnail_size = size

		# create thumbnail factory
		if USE_FACTORY:
			# set default thumbnail size
			if self._thumbnail_size is None:
				self._thumbnail_size = gnome.ui.THUMBNAIL_SIZE_NORMAL

			# create a factory
			self._factory = gnome.ui.ThumbnailFactory(self._thumbnail_size)

		else:
			self._factory = None

	def can_have_thumbnail(self, uri):
		"""Check if specified URI can have thumbnail"""
		if not USE_FACTORY: return False  # if factory is not available, exit

		mime_type = self._parent._parent.associations_manager.get_mime_type(uri)
		return self._factory.can_thumbnail(uri, mime_type, 0)

	def get_thumbnail(self, uri):
		"""Return thumbnail pixbuf for specified URI"""
		if not USE_FACTORY: return None  # if factory is not available, exit

		result = None
		mime_type = self._parent._parent.associations_manager.get_mime_type(uri)

		# check for existing thumbnail
		thumbnail_file = self._factory.lookup(uri, 0)
		if thumbnail_file and os.path.isfile(thumbnail_file):
			result = gtk.gdk.pixbuf_new_from_file(thumbnail_file)

		# create thumbnail
		elif self.can_have_thumbnail(uri):
			result = self._factory.generate_thumbnail(uri, mime_type)

			if result is not None:
				self._factory.save_thumbnail(result, uri, 0)

		return result

	def show_thumbnail(self, uri):
		"""Show thumbnail for specified image"""
		thumbnail = self.get_thumbnail(uri)

		# set preview from pixbuf
		if thumbnail is not None:
			# determine thumbnail size
			width = thumbnail.get_width()
			height = thumbnail.get_height()

			# don't allow preview to be smaller than 32 pixels
			if width < 32: width = 32
			if height < 32: height = 32

			self.set_size_request(width, height)
			self._image.set_from_pixbuf(thumbnail)

		# no pixbuf was found, show missing image
		else:
			self._image.set_from_icon_name('gtk-missing-image', gtk.ICON_SIZE_DIALOG)

	def move(self, left, top):
		"""Move thumbnail window"""
		height = self.get_size()[1]
		screen = self.get_screen()

		if top + height > screen.get_height():
			top = screen.get_height() - height - 5

		gtk.Window.move(self, left, top)
