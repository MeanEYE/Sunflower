import gtk
import time
import urllib

from parameters import Parameters
from collections import namedtuple


class Type:
	SEPARATOR = 0
	MOUNT = 1
	BOOKMARK = 2
	MENU_ITEM = 3


class Column:
	TYPE = 0
	NAME = 1
	ICON = 2
	URI = 3
	CALLBACK = 4
	DATA = 5


Bookmark = namedtuple(
			'Bookmark',
			[
				'name',
				'icon',
				'uri'
			])


MenuItem = namedtuple(
			'MenuItem',
			[
				'name',
				'icon',
				'callback',
				'data'
			])


class BookmarksMenu:
	"""Bookmarks menu widget is designed to replace standard popup menu
	when presenting bookmarks and mounts to user. Before showing this 
	menu, make sure you call set_object as this object will be used to 
	navigate to places in this menu.

	"""

	def __init__(self, application):
		self._application = application
		self._object = None
		self._open_in_new_tab = False

		# options
		self._show_mounts = self._application.bookmark_options.get('show_mounts')
		self._show_home = self._application.bookmark_options.get('add_home')
		self._show_system = self._application.bookmark_options.get('system_bookmarks')

		# containers for bookmarks
		self._mounts = []
		self._bookmarks = []
		self._system_bookmarks = []
		self._menus = []

		# create interface
		self._menu = gtk.Menu()
		self._menu.connect('key-press-event', self.__handle_key_press)
		self._menu.connect('key-release-event', self.__handle_key_press)

	def __handle_key_press(self, widget, event, data=None):
		"""Handle key presses on menu"""
		if event.keyval == gtk.keysyms.Shift_L:
			self._open_in_new_tab = True

		return False

	def __handle_key_release(self, widget, event, data=None):
		"""Handle key releases on menu"""
		if event.keyval == gtk.keysyms.Shift_L:
			self._open_in_new_tab = False

		return False

	def __create_menu_item(self, label, icon, callback, data):
		"""Create menu item"""
		if icon is not None:
			menu_item = gtk.ImageMenuItem()

			image = gtk.Image()
			image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)
			menu_item.set_image(image)

		else:
			menu_item = gtk.MenuItem()

		menu_item.set_label(label)
		menu_item.connect('activate', callback, data)

		self._menu.append(menu_item)

	def __populate_list(self):
		"""Populate list store with objects"""
		# remove all items in menu
		for child in self._menu.get_children():
			self._menu.remove(child)

		# add mounts
		if len(self._mounts) > 0:
			for mount in self._mounts:
				self.__create_menu_item(
								mount.name, 
								mount.icon, 
								self.__open_selected, 
								mount.uri
							)

			separator = gtk.SeparatorMenuItem()
			self._menu.append(separator)

		# add bookmarks
		if len(self._bookmarks) > 0:
			for bookmark in self._bookmarks:
				self.__create_menu_item(
								bookmark.name,
								bookmark.icon,
								self.__open_selected,
								bookmark.uri
							)

			separator = gtk.SeparatorMenuItem()
			self._menu.append(separator)

		# add system bookmarks
		if len(self._system_bookmarks) > 0:
			for bookmark in self._system_bookmarks:
				self.__create_menu_item(
								bookmark.name,
								bookmark.icon,
								self.__open_selected,
								bookmark.uri
							)

			separator = gtk.SeparatorMenuItem()
			self._menu.append(separator)

		# add menu items
		if len(self._menus) > 0:
			for menu_item in self._menus:
				self.__create_menu_item(
								menu_item.name,
								menu_item.icon,
								menu_item.callback,
								menu_item.data
							)

		self._menu.show_all()

	def __open_selected(self, widget, path):
		"""Open selected item in either active, or new tab"""
		# unquote path before giving it to handler
		if path is not None and '://' in path:
			data = path.split('://', 1)
			data[1] = urllib.unquote(data[1])
			path = '://'.join(data)

		# open selected item
		if self._open_in_new_tab:
			# create new tab
			options = Parameters()
			options.set('path', path)

			self._application.create_tab(
							self._object._notebook,
							self._object.__class__,
							options
						)

		elif hasattr(self._object, 'change_path'):
			self._object.change_path(path)

		# reset values
		self._open_in_new_tab = False

		return True

	def set_object(self, active_object):
		"""Set object to operate on when navigating to places"""
		self._object = active_object

	def add_mount(self, name, icon, uri):
		"""Add entry to mounts list"""
		mount = Bookmark(
					name = name,
					icon = icon,
					uri = uri
				)
		self._mounts.append(mount)

	def remove_mount(self, uri):
		"""Remove entry from mounts list"""
		self._mounts = filter(lambda mount: mount.uri != uri, self._mounts)

	def get_mount_count(self):
		"""Return number of mounts in the menu"""
		return len(self._mounts)

	def add_bookmark(self, name, icon, uri, system=False):
		"""Add entry to bookmarks list"""
		bookmark = Bookmark(
					name = name,
					icon = icon,
					uri = uri,
				)

		if not system:
			# add local bookmark
			self._bookmarks.append(bookmark)

		else:
			# add system bookmark
			self._system_bookmarks.append(bookmark)

	def remove_bookmark(self, uri):
		"""Remove entry from bookmarks list"""
		self._bookmarks = filter(lambda bookmark: bookmark.uri != uri, self._bookmarks)
		self._system_bookmarks = filter(lambda bookmark: bookmark.uri != uri, self._system_bookmarks)

	def clear_bookmarks(self):
		"""Clear all bookmarks"""
		del self._bookmarks[:]
		del self._system_bookmarks[:]

	def add_menu_item(self, name, icon, callback, data=None):
		"""Add menu item to the list"""
		menu_item = MenuItem(
					name = name,
					icon = icon,
					callback = callback,
					data = data
				)

		self._menus.append(menu_item)

	def remove_menu_item(self, name):
		"""Remove menu item from the list"""
		self._menus = filter(lambda menu_item: menu_item.name != name, self._menus)
	
	def get_menu_item_count(self):
		"""Return number of menu items"""
		return len(self._menus)

	def show(self, window, invoker):
		"""Show bookmarks menu"""
		assert self._object is not None

		# calculate window position
		window_x, window_y = window.window.get_position()
		button_x, button_y = invoker.translate_coordinates(window, 0, 0)
		button_alloc = invoker.get_allocation()

		pos_x = window_x + button_x + button_alloc.width - invoker.get_allocation()[2]
		pos_y = window_y + button_y + button_alloc.height

		# repopulate list
		self.__populate_list()

		# show menu
		self._menu.popup(None, None, lambda menu: (pos_x, pos_y, True), 1, 0)
		
	def apply_settings(self):
		"""Apply new configuration"""
		self._show_mounts = self._application.bookmark_options.get('show_mounts')
		self._show_home = self._application.bookmark_options.get('add_home')
		self._show_system = self._application.bookmark_options.get('system_bookmarks')
