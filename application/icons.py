#!/usr/bin/env python

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

	def get_icon_from_type(self, mime_type, size=gtk.ICON_SIZE_MENU):
		"""Get icon based on mime type and size"""

		result = None
		key_name = "{0}_{1}".format(mime_type, size)  # create mimetype/size based key

		if self._icon_cache.has_key(key_name):
			# icon is cached and we return already loaded image
			result = self._icon_cache[key_name]

		else:
			# icon is not cached, load it and cache it
			sizes = {
					gtk.ICON_SIZE_MENU: 16,
					gtk.ICON_SIZE_LARGE_TOOLBAR: 24,
				}

			icon_info = self._icon_theme.lookup_icon(mime_type, sizes[size], 0)

			if icon_info is not None:
				result = icon_info.load_icon()
				self._icon_cache[key_name] = result
			else:
				# in case icon does not exist we provide stock icons
				stock_ids = {
							'up': gtk.STOCK_GO_UP,
							'folder': gtk.STOCK_DIRECTORY,
							'document': gtk.STOCK_FILE,
						}

				stock_id = stock_ids[mime_type] if mime_type in stock_ids.keys() else stock_ids['document']

				result = self._parent.render_icon(stock_id, size, detail=None)
				self._icon_cache[key_name] = result

		return result

	def get_icon_for_file(self, filename, size=gtk.ICON_SIZE_MENU):
		"""Load icon for specified filetype"""
		mime_type = mimetypes.guess_type(filename, False)[0]

		result = None

		if mime_type is not None:
			mime_type = mime_type.replace('/', '-')
			result = self.get_icon_from_type(mime_type, size)
		else:
			result = self.get_icon_from_type('document', size)

		if result is None:
			result = self.get_icon_from_type('document', size)

		return result
