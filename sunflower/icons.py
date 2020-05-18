from __future__ import absolute_import
from builtins import filter

import os
import sys
import zipfile

from gi.repository import Gtk, Gio, GdkPixbuf, GLib
from sunflower.common import UserDirectory, get_user_directory, get_base_directory


class IconManager:
	"""Icon manager class provides easy and abstract way of dealing with icons"""

	def __init__(self, parent):
		self._parent = parent
		self._icon_theme = Gtk.IconTheme.get_default()
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
			self._default_file = Gtk.STOCK_FILE

		self._default_directory = 'folder'
		if not self.has_icon(self._default_directory):
			self._default_directory = Gtk.STOCK_DIRECTORY

		# special user directories
		directories = []
		icon_names = {
				UserDirectory.DESKTOP: 'user-desktop',
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
			directories.append((os.path.expanduser('~'), 'folder-home'))

		# create a dictionary
		self._user_directories = dict(directories)

	def has_icon(self, icon_name):
		"""Check if icon with specified name exists in theme"""
		return self._icon_theme.has_icon(icon_name)

	def get_icon_sizes(self, icon_name):
		"""Get icon sizes for specified name"""
		return self._icon_theme.get_icon_sizes(icon_name)

	def get_icon_for_file(self, filename, size=Gtk.IconSize.MENU):
		"""Load icon for specified file"""
		result = self._default_file
		mime_type = self._parent.associations_manager.get_mime_type(filename)
		themed_icon = None

		# get icon names
		if mime_type is not None:
			themed_icon = Gio.content_type_get_icon(mime_type)

		# get only valid icon names
		if themed_icon is not None:
			icon_list = themed_icon.get_names()
			icon_list = list(filter(self.has_icon, icon_list))

			if len(icon_list) > 0:
				result = icon_list[0]

		return result

	def get_icon_for_directory(self, path, size=Gtk.IconSize.MENU):
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
		icon_list = list(filter(self.has_icon, icon_list))

		# if list has items, grab first
		if len(icon_list) > 0:
			result = icon_list[0]

		return result

	def set_window_icon(self, window):
		"""Set window icon"""
		# check system for icon
		if self.has_icon('sunflower'):
			window.set_icon(self._icon_theme.load_icon('sunflower', 256, 0))

		# try loading from zip file
		elif os.path.isfile(sys.path[0]) and sys.path[0] != '':
			archive = zipfile.ZipFile(sys.path[0])
			with archive.open('images/sunflower.svg') as raw_file:
				buff = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(raw_file.read()))
				icon = GdkPixbuf.Pixbuf.new_from_stream(buff, None)
				window.set_icon(icon)
			archive.close()

		# load from local path
		else:
			base_path = os.path.dirname(get_base_directory())
			window.set_icon_from_file(os.path.join(base_path, 'images', 'sunflower.svg'))

