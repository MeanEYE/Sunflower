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

	def get_icon_from_type(self, mime_type, icon_size=gtk.ICON_SIZE_MENU):
		"""Get icon based on MIME type and size"""

		result = None
		size = gtk.icon_size_lookup(icon_size)
		key_name = "{0}_{1}".format(mime_type, size[0])  # create MIME type/size based key

		if self._icon_cache.has_key(key_name):
			# icon is cached and we return already loaded image
			result = self._icon_cache[key_name]

		else:
			# icon is not cached, load it and cache it
			icon_info = self._icon_theme.lookup_icon(mime_type, size[0], 0)

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

				if mime_type in stock_ids.keys():
					stock_id = stock_ids[mime_type] 
				else: 
					stock_id = stock_ids['document']

				result = self._parent.render_icon(stock_id, icon_size, detail=None)
				self._icon_cache[key_name] = result

		return result

	def get_icon_for_file(self, filename, size=gtk.ICON_SIZE_MENU):
		"""Load icon for specified file type"""
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
