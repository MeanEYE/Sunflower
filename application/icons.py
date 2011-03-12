import gtk
import mimetypes

class IconManager:
	_icon_theme = None
	_icon_cache = {}

	def __init__(self, parent):
		self._parent = parent
		self._icon_theme = gtk.icon_theme_get_default()
		self._icon_theme.connect('changed', self._theme_changed)

	def _theme_changed(self, widget, data=None):
		"""Handle icon theme change"""
		self._icon_cache.clear()
		return True

	def has_icon(self, icon_name):
		"""Check if icon with specified name exists in theme"""
		return self._icon_theme.has_icon(icon_name)

	def get_icon_from_type(self, mime_type, icon_size=gtk.ICON_SIZE_MENU):
		"""Get icon based on MIME type and size"""
		result = None
		size = gtk.icon_size_lookup(icon_size)
		key_name = "{0}_{1}".format(mime_type, size[0])  # create MIME type/size based key

		if self._icon_cache.has_key(key_name):
			# icon is cached and we return already loaded image
			result = self._icon_cache[key_name]

		else:
			# get information about the icon
			icon_info = self._icon_theme.lookup_icon(mime_type, size[0], 0)

			if icon_info is not None:
				# load icon and cache it
				result = icon_info.load_icon()
				self._icon_cache[key_name] = result

		return result

	def get_icon_for_file(self, filename, size=gtk.ICON_SIZE_MENU):
		"""Load icon for specified file type"""
		result = None
		mime_type = mimetypes.guess_type(filename, False)[0]

		if mime_type is not None:
			# get icon from file type
			mime_type = mime_type.replace('/', '-')
			result = self.get_icon_from_type(mime_type, size)

		if result is None:
			# get default icon
			result = self.get_icon_from_type('document', size)

		return result

	def get_mount_icon_name(self, icons):
		"""Return existing icon name from the specified list"""
		result = 'drive-harddisk'

		# create a list of icons and filter non-existing
		list_ = icons.split(' ')
		list_ = filter(self.has_icon, list_)

		# if list has items, grab first
		if len(list_) > 0:
			result = list_[0]

		return result
