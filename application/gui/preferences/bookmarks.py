import gtk

from widgets.settings_page import SettingsPage


class Column:
	NAME = 0
	URI = 1


class BookmarksOptions(SettingsPage):
	"""Bookmark options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'bookmarks', _('Bookmarks'))

		# mounts checkbox
		self._checkbox_show_mount_points = gtk.CheckButton(_('Show mount points in bookmarks menu'))
		self._checkbox_show_mount_points.connect('toggled', self._parent.enable_save)

		# system bookmarks checkbox
		self._checkbox_system_bookmarks = gtk.CheckButton(_('Show system bookmarks'))
		self._checkbox_system_bookmarks.connect('toggled', self._parent.enable_save)

		# bookmarks checkbox
		self._checkbox_add_home = gtk.CheckButton(_('Add home directory to bookmarks menu'))
		self._checkbox_add_home.connect('toggled', self._parent.enable_save)

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._bookmarks = gtk.ListStore(str, str)

		self._list = gtk.TreeView()
		self._list.set_model(self._bookmarks)
		self._list.set_rules_hint(True)

		cell_title = gtk.CellRendererText()
		cell_title.set_property('editable', True)
		cell_title.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_title.connect('edited', self._edited_bookmark, 0)

		cell_command = gtk.CellRendererText()
		cell_command.set_property('editable', True)
		cell_command.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_command.connect('edited', self._edited_bookmark, 1)

		col_title = gtk.TreeViewColumn(_('Title'), cell_title, text=Column.NAME)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn(_('Location'), cell_command, text=Column.URI)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)

		container.add(self._list)

		# create controls
		button_box = gtk.HBox(False, 5)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_bookmark)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_bookmark)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_move_up = gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._move_bookmark, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_move_down = gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._move_bookmark, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		# pack checkboxes
		vbox = gtk.VBox(False, 0)

		vbox.pack_start(self._checkbox_show_mount_points, False, False, 0)
		vbox.pack_start(self._checkbox_system_bookmarks, False, False, 0)
		vbox.pack_start(self._checkbox_add_home, False, False, 0)

		self.pack_start(vbox, False, False, 0)
		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_bookmark(self, widget, data=None):
		"""Add new bookmark to the store"""
		if data is None:
			data = ('New bookmark', '')

		# add new data to the store
		self._bookmarks.append(data)

		# enable save button on parent
		self._parent.enable_save()

	def _edited_bookmark(self, cell, path, text, column):
		"""Record edited text"""
		selected_iter = self._bookmarks.get_iter(path)
		self._bookmarks.set_value(selected_iter, column, text)

		# enable save button
		self._parent.enable_save()

	def _delete_bookmark(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# remove item from the store
			item_list.remove(selected_iter)

			# enable save button if item was removed
			self._parent.enable_save()

	def _move_bookmark(self, widget, direction):
		"""Move selected bookmark up or down"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# get iter index
			index = item_list.get_path(selected_iter)[0]

			# depending on direction, swap iters
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(item_list) - 1):
				item_list.swap(selected_iter, item_list[index + direction].iter)

			# enable save button if iters were swapped
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		options = self._application.bookmark_options

		# get checkbox states
		self._checkbox_show_mount_points.set_active(options.get('show_mounts'))
		self._checkbox_add_home.set_active(options.get('add_home'))
		self._checkbox_system_bookmarks.set_active(options.get('system_bookmarks'))

		# load and parse bookmars
		self._bookmarks.clear()

		bookmarks = options.get('bookmarks')
		for bookmark in bookmarks:
			self._bookmarks.append((bookmark['name'], bookmark['uri']))

	def _save_options(self):
		"""Save bookmarks to file"""
		options = self._application.bookmark_options

		# save checkbox state
		options.set('show_mounts', self._checkbox_show_mount_points.get_active())
		options.set('add_home', self._checkbox_add_home.get_active())
		options.set('system_bookmarks', self._checkbox_system_bookmarks.get_active())

		# save bookmarks
		bookmarks = []

		for data in self._bookmarks:
			bookmarks.append({
					'name': data[Column.NAME],
					'uri': data[Column.URI]
				})

		options.set('bookmarks', bookmarks)
