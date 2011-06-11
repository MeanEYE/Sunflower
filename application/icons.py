import os
import sys
import gtk
import gio
import mimetypes

class IconManager:
	_icon_theme = None

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

	def get_icon_for_file(self, filename, size=gtk.ICON_SIZE_MENU):
		"""Load icon for specified file"""
		result = 'document'
		mime_type = mimetypes.guess_type(filename, False)[0]
		themed_icon = None

		# get icon names
		if mime_type is not None:
			themed_icon = gio.content_type_get_icon(mime_type)

		# get only valid icon names
		if themed_icon is not None:
			icon_list = themed_icon.get_names()
			icon_list = filter(self.has_icon, icon_list)

			if len(icon_list) > 0:
				result = icon_list[0]

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

	def set_window_icon(self, window):
		"""Set window icon"""
		if self.has_icon('sunflower'):
			# in case theme has its own icon, use that one
			window.set_icon_name('sunflower')

		else:
			window.set_icon_from_file(os.path.abspath(os.path.join(
										'images',
										'sunflower_hi-def_64x64.png'
									)))

