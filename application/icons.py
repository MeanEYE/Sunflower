import os
import sys
import gtk
import gio
import user

from common import UserDirectory, get_user_directory


class IconManager:
	"""Icon manager class provides easy and abstract way of dealing with icons"""

	def __init__(self, parent):
		self._parent = parent
		self._icon_theme = gtk.icon_theme_get_default()
		self._user_directories = None
		self._default_file = None
		self._default_directory = None

		# preload information
		self._prepare_icons()

	def _prepare_icons(self):
		"""Load special user directories"""
		# set default icons for file and directory
		self._default_file = 'empty'
		if not self.has_icon(self._default_file):
			self._default_file = gtk.STOCK_FILE

		self._default_directory = 'folder'
		if not self.has_icon(self._default_directory):
			self._default_directory = gtk.STOCK_DIRECTORY

		# special user directories
		directories = []
		icon_names = {
				UserDirectory.DESKTOP: 'desktop',
				UserDirectory.DOWNLOADS: 'folder-downloads',
				UserDirectory.TEMPLATES: 'folder-templates',
				UserDirectory.PUBLIC: 'folder-publicshare',
				UserDirectory.DOCUMENTS: 'folder-documents',
				UserDirectory.MUSIC: 'folder-music',
				UserDirectory.PICTURES: 'folder-pictures',
				UserDirectory.VIDEOS: 'folder-videos'
			}

		# add all directories
		for directory in icon_names.keys():
			full_path = get_user_directory(directory)
			icon_name = icon_names[directory]

			# make sure icon exists
			if not self.has_icon(icon_name):
				icon_name = self._default_directory

			directories.append((full_path, icon_name))

		# add user home directory
		if self.has_icon('folder-home'):
			directories.append((user.home, 'folder-home'))

		# create a dictionary
		self._user_directories = dict(directories)

	def has_icon(self, icon_name):
		"""Check if icon with specified name exists in theme"""
		return self._icon_theme.has_icon(icon_name)

	def get_icon_sizes(self, icon_name):
		"""Get icon sizes for specified name"""
		return self._icon_theme.get_icon_sizes(icon_name)

	def get_icon_for_file(self, filename, size=gtk.ICON_SIZE_MENU):
		"""Load icon for specified file"""
		result = self._default_file
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

	def get_icon_for_directory(self, path, size=gtk.ICON_SIZE_MENU):
		"""Get icon for specified directory"""
		result = self._default_directory

		if path in self._user_directories:
			result = self._user_directories[path]

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
			base_path = os.path.dirname(os.path.dirname(sys.argv[0]))
			window.set_icon_from_file(os.path.abspath(os.path.join(
										base_path,
										'images',
										'sunflower.svg'
									)))

