import os
import gtk
import gio


class IconManager:
	"""Icon manager class provides easy and abstract way of dealing with icons"""

	def __init__(self, parent):
		self._parent = parent
		self._icon_theme = gtk.icon_theme_get_default()

	def has_icon(self, icon_name):
		"""Check if icon with specified name exists in theme"""
		return self._icon_theme.has_icon(icon_name)

	def get_icon_sizes(self, icon_name):
		"""Get icon sizes for specified name"""
		return self._icon_theme.get_icon_sizes(icon_name)

	def get_icon_for_file(self, filename, size=gtk.ICON_SIZE_MENU):
		"""Load icon for specified file"""
		result = 'document'
		mime_type = self._parent.associations_manager.get_mime_type(filename)
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
		icon_list = icons.split(' ')
		icon_list = filter(self.has_icon, icon_list)

		# if list has items, grab first
		if len(icon_list) > 0:
			result = icon_list[0]

		return result

	def set_window_icon(self, window):
		"""Set window icon"""
		if self.has_icon('sunflower'):
			# in case theme has its own icon, use that one
			window.set_icon(self._icon_theme.load_icon('sunflower', 256, 0))

		else:
			window.set_icon_from_file(os.path.abspath(os.path.join(
										'images',
										'sunflower.svg'
									)))

