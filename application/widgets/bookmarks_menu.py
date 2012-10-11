import gtk

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
		self._visible = False

		# options
		self._show_mounts = self._application.bookmark_options.get('show_mounts')
		self._show_home = self._application.bookmark_options.get('add_home')
		self._show_system = self._application.bookmark_options.get('system_bookmarks')

		# containers for bookmarks
		self._mounts = []
		self._bookmarks = []
		self._system_bookmarks = []
		self._menus = []

		# create window
		self._window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		# configure window
		self._window.set_title(_('Bookmarks'))
		self._window.set_size_request(200, 300)
		self._window.set_resizable(False)
		self._window.set_skip_taskbar_hint(True)
		self._window.set_skip_pager_hint(True)
		self._window.set_transient_for(application)
		self._window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_POPUP_MENU)
		self._window.set_wmclass('Sunflower', 'Sunflower')
		self._window.set_border_width(0)
		self._window.set_keep_above(True)
		self._window.set_decorated(False)
		self._window.set_has_frame(False)

		# connect signals
		self._window.connect('delete-event', self.__destroy_event)

		# create user interface
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		container.set_shadow_type(gtk.SHADOW_ETCHED_OUT)

		self._store = gtk.ListStore(int, str, str, str, object, object)
		self._list = gtk.TreeView(model=self._store)

		cell_name = gtk.CellRendererText()
		cell_icon = gtk.CellRendererPixbuf()

		col_name = gtk.TreeViewColumn(None)

		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)

		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'text', Column.NAME)

		self._list.set_row_separator_func(self.__is_row_separator)
		self._list.append_column(col_name)
		self._list.set_headers_visible(False)
		self._list.set_search_column(Column.NAME)

		# custom search function to allow searching inside of the string
		# compare = lambda model, column, key, iter_: key.lower() not in model.get_value(iter_, column).lower()
		# self._list.set_search_equal_func(compare)

		# connect list signals
		self._list.connect('focus-out-event', self.__handle_focus_lost)
		self._list.connect('key-press-event', self.__handle_key_press)
		self._list.connect('button-release-event', self.__handle_button_press)

		# pack user interface
		container.add(self._list)
		self._window.add(container)

		# show all widgets within container
		container.show_all()

	def __populate_list(self):
		"""Populate list store with objects"""
		self._store.clear()

		# add mounts
		if len(self._mounts) > 0:
			for mount in self._mounts:
				self._store.append((Type.MOUNT, mount.name, mount.icon, mount.uri, None, None))

			self._store.append((Type.SEPARATOR, None, None, None, None, None))

		# add bookmarks
		if len(self._bookmarks) > 0:
			for bookmark in self._bookmarks:
				self._store.append((Type.BOOKMARK, bookmark.name, bookmark.icon, bookmark.uri, None, None))

			self._store.append((Type.SEPARATOR, None, None, None, None, None))

		# add system bookmarks
		if len(self._system_bookmarks) > 0:
			for bookmark in self._system_bookmarks:
				self._store.append((Type.BOOKMARK, bookmark.name, bookmark.icon, bookmark.uri, None, None))

		# add menu items
		if len(self._menus) > 0:
			for menu_item in self._menus:
				self._store.append((Type.MENU_ITEM, menu_item.name, menu_item.icon, None, menu_item.callback, menu_item.data))

	def __is_row_separator(self, model, iter, data=None):
		"""Check if specified row should be treated as separator"""
		result = False

		if model.get_value(iter, Column.TYPE) == Type.SEPARATOR:
			result = True
		
		return result

	def __handle_key_press(self, widget, event, data=None):
		"""Handle key press event on list"""
		result = False

		# handle escape key
		if event.keyval == gtk.keysyms.Escape:
			self.close()
			result = True

		# handle bookmark activation
		elif event.keyval == gtk.keysyms.Return:
			new_tab = event.state & gtk.gdk.SHIFT_MASK
			self.__open_selected(new_tab)

			# close window
			self.close()
			result = True
		
		return result

	def __handle_button_press(self, widget, event):
		"""Handle mouse button press"""
		new_tab = event.state & gtk.gdk.SHIFT_MASK
		self.__open_selected(new_tab)
		self.close()

	def __handle_focus_lost(self, widget, data=None):
		"""Handle loosing focus from the list"""

		# only enable handlers here because we are loosing focus
		# when windows is closed regardles who closed it and why
		self.__enable_handlers()
		self.close()

	def __enable_handlers(self):
		"""Enable handlers on active objects"""
		assert self._object is not None

		# restore handlers
		opposite_object = self._application.get_opposite_object(self._object)
		self._object._disable_object_block()
		opposite_object._disable_object_block()

	def __destroy_event(self, widget, data=None):
		"""Handle destroy event"""
		self.close()
		return True

	def __open_selected(self, new_tab=False):
		"""Open selected item in either active, or new tab"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# we need selection
		if selected_iter is None:
			return;

		path = item_list.get_value(selected_iter, Column.URI)
		item_type = item_list.get_value(selected_iter, Column.TYPE)

		if item_type == Type.MOUNT \
		or item_type == Type.BOOKMARK:
			if new_tab:
				# create new tab
				self._application.create_tab(
								self._object._notebook,
								self._object.__class__,
								path
							)

			elif hasattr(self._object, 'change_path'):
				self._object.change_path(path)

		elif item_type == Type.MENU_ITEM:
			callback = item_list.get_value(selected_iter, Column.CALLBACK)
			data = item_list.get_value(selected_iter, Column.DATA)

			if callback is not None:
				callback(self._window, data)

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

		if self._visible:
			return

		# calculate window position
		window_x, window_y = window.window.get_position()
		button_x, button_y = invoker.translate_coordinates(window, 0, 0)
		button_alloc = invoker.get_allocation()

		pos_x = (window_x + button_x + button_alloc.width) - self._window.get_size()[0]
		pos_y = window_y + button_y + button_alloc.height

		# block enable handler block
		opposite_object = self._application.get_opposite_object(self._object)
		self._object._enable_object_block()
		opposite_object._enable_object_block()

		# repopulate list
		self.__populate_list()

		# show window
		self._window.move(0, 0)
		self._window.move(pos_x, pos_y)

		self._visible = True
		self._window.show()
		
	def close(self, widget=None, data=None):
		"""Handle window closing"""
		if self._visible:
			self._window.hide()
			self._visible = False

	def apply_settings(self):
		"""Apply new configuration"""
		self._show_mounts = self._application.bookmark_options.get('show_mounts')
		self._show_home = self._application.bookmark_options.get('add_home')
		self._show_system = self._application.bookmark_options.get('system_bookmarks')
