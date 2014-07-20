import gtk

from common import AccessModeFormat
from gui.input_dialog import InputDialog
from widgets.breadcrumbs import Breadcrumbs
from widgets.settings_page import SettingsPage


class Column:
	NAME = 0
	SIZE = 1
	VISIBLE = 2
	FONT_SIZE = 3


class ExtensionColumn:
	NAME = 0
	CLASS_NAME = 1


class DirectoryColumn:
	PATH = 0
	LEFT_LIST = 1
	RIGHT_LIST = 2


class Source:
	LEFT = 0
	RIGHT = 1
	CUSTOM = 2


class ItemListOptions(SettingsPage):
	"""Options related to item lists"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'item_list', _('Item List'))

		notebook = gtk.Notebook()

		# create frames
		label_look_and_feel = gtk.Label(_('Look & feel'))
		label_operation = gtk.Label(_('Operation'))
		label_directories = gtk.Label(_('Directories'))
		label_columns = gtk.Label(_('Columns'))

		# vertical boxes
		vbox_look_and_feel = gtk.VBox(False, 0)
		vbox_operation = gtk.VBox(False, 0)
		vbox_directory = gtk.VBox(False, 0)
		vbox_columns = gtk.VBox(False, 0)

		vbox_look_and_feel.set_border_width(5)
		vbox_operation.set_border_width(5)
		vbox_directory.set_border_width(5)
		vbox_directory.set_spacing(5)
		vbox_columns.set_border_width(5)

		# file list options
		self._checkbox_row_hinting = gtk.CheckButton(_('Row hinting'))
		self._checkbox_show_hidden = gtk.CheckButton(_('Show hidden files'))
		self._checkbox_case_sensitive = gtk.CheckButton(_('Case sensitive item sorting'))
		self._checkbox_number_sensitive = gtk.CheckButton(_('Number sensitive item sorting'))
		self._checkbox_single_click = gtk.CheckButton(_('Single click navigation'))
		self._checkbox_right_click = gtk.CheckButton(_('Right click selects items'))
		self._checkbox_show_headers = gtk.CheckButton(_('Show list headers'))
		self._checkbox_media_preview = gtk.CheckButton(_('Fast media preview'))
		self._checkbox_show_expanders = gtk.CheckButton(_('Show tree expanders'))
		self._checkbox_hide_scrollbar = gtk.CheckButton(_('Hide horizontal scrollbar'))

		self._checkbox_row_hinting.connect('toggled', self._parent.enable_save)
		self._checkbox_show_hidden.connect('toggled', self._parent.enable_save)
		self._checkbox_case_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_number_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_single_click.connect('toggled', self._parent.enable_save)
		self._checkbox_right_click.connect('toggled', self._parent.enable_save)
		self._checkbox_show_headers.connect('toggled', self._parent.enable_save)
		self._checkbox_media_preview.connect('toggled', self._parent.enable_save)
		self._checkbox_show_expanders.connect('toggled', self._parent.enable_save)
		self._checkbox_hide_scrollbar.connect('toggled', self._parent.enable_save)

		# bread crumbs type
		hbox_breadcrumbs = gtk.HBox(False, 5)
		label_breadcrumbs = gtk.Label(_('Breadcrumbs:'))
		label_breadcrumbs.set_alignment(0, 0.5)
		
		list_breadcrumbs = gtk.ListStore(str, int)
		list_breadcrumbs.append((_('None'), Breadcrumbs.TYPE_NONE))
		list_breadcrumbs.append((_('Normal'), Breadcrumbs.TYPE_NORMAL))
		list_breadcrumbs.append((_('Smart'), Breadcrumbs.TYPE_SMART))

		cell_breadcrumbs = gtk.CellRendererText()

		self._combobox_breadcrumbs = gtk.ComboBox(list_breadcrumbs)
		self._combobox_breadcrumbs.connect('changed', self._parent.enable_save)
		self._combobox_breadcrumbs.pack_start(cell_breadcrumbs)
		self._combobox_breadcrumbs.add_attribute(cell_breadcrumbs, 'text', 0)

		# file access mode format
		hbox_mode_format = gtk.HBox(False, 5)
		label_mode_format = gtk.Label(_('Access mode format:'))
		label_mode_format.set_alignment(0, 0.5)

		list_mode_format = gtk.ListStore(str, int)
		list_mode_format.append((_('Octal'), AccessModeFormat.OCTAL))
		list_mode_format.append((_('Textual'), AccessModeFormat.TEXTUAL))

		cell_mode_format = gtk.CellRendererText()

		self._combobox_mode_format = gtk.ComboBox(list_mode_format)
		self._combobox_mode_format.connect('changed', self._parent.enable_save)
		self._combobox_mode_format.pack_start(cell_mode_format)
		self._combobox_mode_format.add_attribute(cell_mode_format, 'text', 0)

		# grid lines
		hbox_grid_lines = gtk.HBox(False, 5)
		label_grid_lines = gtk.Label(_('Show grid lines:'))
		label_grid_lines.set_alignment(0, 0.5)

		list_grid_lines = gtk.ListStore(str, int)
		list_grid_lines.append((_('None'), gtk.TREE_VIEW_GRID_LINES_NONE))
		list_grid_lines.append((_('Horizontal'), gtk.TREE_VIEW_GRID_LINES_HORIZONTAL))
		list_grid_lines.append((_('Vertical'), gtk.TREE_VIEW_GRID_LINES_VERTICAL))
		list_grid_lines.append((_('Both'), gtk.TREE_VIEW_GRID_LINES_BOTH))

		cell_grid_lines = gtk.CellRendererText()

		self._combobox_grid_lines = gtk.ComboBox(list_grid_lines)
		self._combobox_grid_lines.connect('changed', self._parent.enable_save)
		self._combobox_grid_lines.pack_start(cell_grid_lines)
		self._combobox_grid_lines.add_attribute(cell_grid_lines, 'text', 0)

		# selection color
		hbox_selection_color = gtk.HBox(False, 5)

		label_selection_color = gtk.Label(_('Selection color:'))
		label_selection_color.set_alignment(0, 0.5)

		self._button_selection_color = gtk.ColorButton()
		self._button_selection_color.set_use_alpha(False)
		self._button_selection_color.connect('color-set', self._parent.enable_save)

		# selection indicator
		hbox_indicator = gtk.HBox(False, 5)

		label_indicator = gtk.Label(_('Selection indicator:'))
		label_indicator.set_alignment(0, 0.5)

		list_indicator = gtk.ListStore(str)
		list_indicator.append((u'\u25b6',))
		list_indicator.append((u'\u25e2',))
		list_indicator.append((u'\u25c8',))
		list_indicator.append((u'\u263b',))
		list_indicator.append((u'\u2771',))
		list_indicator.append((u'\u2738',))
		list_indicator.append((u'\u2731',))

		self._combobox_indicator = gtk.ComboBoxEntry(list_indicator, 0)
		self._combobox_indicator.connect('changed', self._parent.enable_save)
		self._combobox_indicator.set_size_request(100, -1)

		# quick search
		label_quick_search = gtk.Label(_('Quick search combination:'))
		label_quick_search.set_alignment(0, 0.5)
		label_quick_search.set_use_markup(True)
		self._checkbox_control = gtk.CheckButton(_('Control'))
		self._checkbox_alt = gtk.CheckButton(_('Alt'))
		self._checkbox_shift = gtk.CheckButton(_('Shift'))

		self._checkbox_control.connect('toggled', self._parent.enable_save)
		self._checkbox_alt.connect('toggled', self._parent.enable_save)
		self._checkbox_shift.connect('toggled', self._parent.enable_save)

		hbox_quick_search = gtk.HBox(False, 5)

		vbox_time_format = gtk.VBox(False, 0)
		label_time_format = gtk.Label(_('Date format:'))
		label_time_format.set_alignment(0, 0.5)
		self._entry_time_format = gtk.Entry()
		self._entry_time_format.set_tooltip_markup(
								'<b>' + _('Time is formed using the format located at:') + '</b>\n'
								'http://docs.python.org/library/time.html#time.strftime'
							)
		self._entry_time_format.connect('changed', self._parent.enable_save)

		# create list of directories
		container_directory = gtk.ScrolledWindow()
		container_directory.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container_directory.set_shadow_type(gtk.SHADOW_IN)

		self._checkbox_load_directories = gtk.CheckButton(_('Load specified tabs instead of saved'))
		self._checkbox_load_directories.connect('toggled', self._parent.enable_save)

		self._directory_store = gtk.ListStore(str, bool, bool)
		self._directory_list = gtk.TreeView(model=self._directory_store)

		cell_directory = gtk.CellRendererText()
		cell_left_list = gtk.CellRendererToggle()
		cell_right_list = gtk.CellRendererToggle()

		cell_left_list.connect('toggled', self._toggle_path, Source.LEFT)
		cell_right_list.connect('toggled', self._toggle_path, Source.RIGHT)

		col_directory = gtk.TreeViewColumn(_('Directory'), cell_directory, text=DirectoryColumn.PATH)
		col_directory.set_min_width(200)
		col_directory.set_resizable(True)
		col_directory.set_expand(True)

		col_left_list = gtk.TreeViewColumn(_('Left list'), cell_left_list, active=DirectoryColumn.LEFT_LIST)
		col_right_list = gtk.TreeViewColumn(_('Right list'), cell_right_list, active=DirectoryColumn.RIGHT_LIST)

		self._directory_list.append_column(col_directory)
		self._directory_list.append_column(col_left_list)
		self._directory_list.append_column(col_right_list)

		hbox_directory = gtk.HBox(False, 5)

		button_add_directory = gtk.Button(stock=gtk.STOCK_ADD)
		button_add_directory.connect('clicked', self.__button_add_clicked)

		button_delete_directory = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete_directory.connect('clicked', self._delete_path)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_directory_move_up = gtk.Button(label=None)
		button_directory_move_up.add(image_up)
		button_directory_move_up.set_tooltip_text(_('Move Up'))
		button_directory_move_up.connect('clicked', self._move_path, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_directory_move_down = gtk.Button(label=None)
		button_directory_move_down.add(image_down)
		button_directory_move_down.set_tooltip_text(_('Move Down'))
		button_directory_move_down.connect('clicked', self._move_path, 1)

		self._menu_add_directory = gtk.Menu()

		menu_item_custom = gtk.MenuItem(_('Custom directory'))
		menu_item_separator = gtk.SeparatorMenuItem()
		menu_item_left_directory = gtk.MenuItem(_('Left directory'))
		menu_item_right_directory = gtk.MenuItem(_('Right directory'))

		menu_item_custom.connect('activate', self._add_path, Source.CUSTOM)
		menu_item_left_directory.connect('activate', self._add_path, Source.LEFT)
		menu_item_right_directory.connect('activate', self._add_path, Source.RIGHT)

		self._menu_add_directory.append(menu_item_custom)
		self._menu_add_directory.append(menu_item_separator)
		self._menu_add_directory.append(menu_item_left_directory)
		self._menu_add_directory.append(menu_item_right_directory)

		self._menu_add_directory.show_all()

		# create columns editor
		hbox_columns = gtk.HBox(False, 5)

		container_columns = gtk.ScrolledWindow()
		container_columns.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container_columns.set_shadow_type(gtk.SHADOW_IN)

		container_plugin = gtk.ScrolledWindow()
		container_plugin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		container_plugin.set_shadow_type(gtk.SHADOW_IN)

		# create variable to store active extension to
		self._extensions = {}
		self._active_extension = None

		# create column list
		self._columns_store = gtk.ListStore(str, int, bool, str)
		self._columns_list = gtk.TreeView()

		self._columns_list.set_model(self._columns_store)
		self._columns_list.set_rules_hint(True)
		self._columns_list.set_enable_search(True)
		self._columns_list.set_search_column(Column.NAME)

		cell_name = gtk.CellRendererText()
		cell_size = gtk.CellRendererText()
		cell_visible = gtk.CellRendererToggle()
		cell_font_size = gtk.CellRendererSpin()

		cell_size.set_property('editable', True)
		cell_size.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_size.connect('edited', self._edited_column_size)

		cell_font_size.set_property('editable', True)
		cell_font_size.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		adjustment = gtk.Adjustment(0, 0, 100, 1, 10, 0)
		cell_font_size.set_property('adjustment', adjustment)
		cell_font_size.connect('edited', self._edited_column_font_size)

		cell_visible.connect('toggled', self._toggle_column_visible)

		col_name = gtk.TreeViewColumn(_('Column'), cell_name, text=Column.NAME)
		col_name.set_min_width(150)
		col_name.set_resizable(True)
		col_name.set_expand(True)

		col_size = gtk.TreeViewColumn(_('Size'), cell_size, text=Column.SIZE)
		col_size.set_min_width(50)

		col_visible = gtk.TreeViewColumn(_('Visible'), cell_visible, active=Column.VISIBLE)
		col_visible.set_min_width(50)

		col_font_size = gtk.TreeViewColumn(_('Font'), cell_font_size, text=Column.FONT_SIZE)
		col_font_size.set_min_width(50)

		self._columns_list.append_column(col_name)
		self._columns_list.append_column(col_size)
		self._columns_list.append_column(col_font_size)
		self._columns_list.append_column(col_visible)

		# create plugin list
		self._extension_store = gtk.ListStore(str, str)
		self._extension_list = gtk.TreeView()

		self._extension_list.set_model(self._extension_store)
		self._extension_list.set_size_request(130, -1)
		self._extension_list.set_headers_visible(False)

		self._extension_list.connect('cursor-changed', self._handle_cursor_change)

		cell_name = gtk.CellRendererText()
		col_name = gtk.TreeViewColumn(None, cell_name, text=ExtensionColumn.NAME)

		self._extension_list.append_column(col_name)

		# pack interface
		container_directory.add(self._directory_list)
		container_columns.add(self._columns_list)
		container_plugin.add(self._extension_list)

		hbox_directory.pack_start(button_add_directory, False, False, 0)
		hbox_directory.pack_start(button_delete_directory, False, False, 0)
		hbox_directory.pack_end(button_directory_move_down, False, False, 0)
		hbox_directory.pack_end(button_directory_move_up, False, False, 0)

		hbox_columns.pack_start(container_plugin, False, False, 0)
		hbox_columns.pack_start(container_columns, True, True, 0)

		hbox_indicator.pack_start(label_indicator, False, False, 0)
		hbox_indicator.pack_start(self._combobox_indicator, False, False, 0)

		hbox_selection_color.pack_start(label_selection_color, False, False, 0)
		hbox_selection_color.pack_start(self._button_selection_color, False, False, 0)

		hbox_quick_search.pack_start(label_quick_search, False, False, 0)
		hbox_quick_search.pack_start(self._checkbox_control, False, False, 0)
		hbox_quick_search.pack_start(self._checkbox_alt, False, False, 0)
		hbox_quick_search.pack_start(self._checkbox_shift, False, False, 0)

		hbox_breadcrumbs.pack_start(label_breadcrumbs, False, False, 0)
		hbox_breadcrumbs.pack_start(self._combobox_breadcrumbs, False, False, 0)

		hbox_mode_format.pack_start(label_mode_format, False, False, 0)
		hbox_mode_format.pack_start(self._combobox_mode_format, False, False, 0)

		hbox_grid_lines.pack_start(label_grid_lines, False, False, 0)
		hbox_grid_lines.pack_start(self._combobox_grid_lines, False, False, 0)

		vbox_time_format.pack_start(label_time_format, False, False, 0)
		vbox_time_format.pack_start(self._entry_time_format, False, False, 0)

		vbox_look_and_feel.pack_start(self._checkbox_row_hinting, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_headers, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_media_preview, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_hidden, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_expanders, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_hide_scrollbar, False, False, 0)
		vbox_look_and_feel.pack_start(hbox_breadcrumbs, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_mode_format, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_grid_lines, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_selection_color, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_indicator, False, False, 5)

		vbox_operation.pack_start(self._checkbox_case_sensitive, False, False, 0)
		vbox_operation.pack_start(self._checkbox_number_sensitive, False, False, 0)
		vbox_operation.pack_start(self._checkbox_single_click, False, False, 0)
		vbox_operation.pack_start(self._checkbox_right_click, False, False, 0)
		vbox_operation.pack_start(hbox_quick_search, False, False, 5)
		vbox_operation.pack_start(vbox_time_format, False, False, 5)

		vbox_directory.pack_start(self._checkbox_load_directories, False, False, 0)
		vbox_directory.pack_start(container_directory, True, True, 0)
		vbox_directory.pack_start(hbox_directory, False, False, 0)

		vbox_columns.pack_start(hbox_columns, True, True, 0)

		notebook.append_page(vbox_look_and_feel, label_look_and_feel)
		notebook.append_page(vbox_operation, label_operation)
		notebook.append_page(vbox_directory, label_directories)
		notebook.append_page(vbox_columns, label_columns)

		self.pack_start(notebook, True, True, 0)

	def __button_add_clicked(self, widget, data=None):
		"""Handle clicking on add button"""
		self._menu_add_directory.popup(
						None, None,
						self.__get_menu_position,
						1, 0, widget
					)

	def __get_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def _add_path(self, widget, source):
		"""Add path to the list from specified source"""
		if source == Source.CUSTOM:
			# show dialog for custom path entry
			dialog = InputDialog(self._application)
			dialog.set_title(_('Add custom directory'))
			dialog.set_label(_('Full path:'))
			
			response = dialog.get_response()

			if response[0] == gtk.RESPONSE_OK:
				self._directory_store.append((response[1], False, False))

		else:
			# add path from notebook
			list_object = {
					Source.LEFT: self._application.get_left_object(),
					Source.RIGHT: self._application.get_right_object()
				}[source]

			path = list_object._options.get('path')

			if path is not None:
				self._directory_store.append((path, False, False))

		# enable save button
		self._parent.enable_save()

		return True

	def _delete_path(self, widget, data=None):
		"""Remove path from the list"""
		selection = self._directory_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# remove item from the store
			item_list.remove(selected_iter)

			# enable save button if item was removed
			self._parent.enable_save()

	def _move_path(self, widget, direction):
		"""Move selected path up or down"""
		selection = self._directory_list.get_selection()
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

	def _toggle_path(self, cell, path, target_list):
		"""Handle toggling path entry for specific list"""
		if target_list == Source.LEFT:
			# toggle for left list
			state = self._directory_store[path][DirectoryColumn.LEFT_LIST]
			self._directory_store[path][DirectoryColumn.LEFT_LIST] = not state

		else:
			# toggle for right list
			state = self._directory_store[path][DirectoryColumn.RIGHT_LIST]
			self._directory_store[path][DirectoryColumn.RIGHT_LIST] = not state

		# enable save button
		self._parent.enable_save()
	
		return True

	def _vim_bindings_toggled(self, widget, data=None):
		"""Handle toggling VIM bindings on or off"""
		if widget.get_active() \
		and self._application.options.section('item_list').get('search_modifier') == '000':
			# user can't have this quick search combination with VIM bindings
			dialog = gtk.MessageDialog(
									self._application,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_WARNING,
									gtk.BUTTONS_OK,
									_(
										'Quick search settings are in conflict with VIM '
										'navigation style. To resolve this issue your '
										'quick search settings were restored to default.'
									)
								)

			dialog.run()
			dialog.destroy()

			# restore default search modifiers
			self._checkbox_control.set_active(False)
			self._checkbox_alt.set_active(True)
			self._checkbox_shift.set_active(False)

		# enable save button
		self._parent.enable_save(show_restart=True)

	def _populate_column_editor_extensions(self):
		"""Populate list with column editor extensions"""
		extension_list = self._application.column_editor_extensions

		# clear existing lists
		self._extension_store.clear()
		self._columns_store.clear()

		self._active_extension = None

		# add all the extensions
		for extension in extension_list:
			name, class_name = extension.get_name()

			self._extensions[class_name] = extension
			self._extension_store.append((name, class_name))

		# select first extension
		if len(self._extension_store) > 0:
			path = self._extension_store.get_path(self._extension_store.get_iter_first())
			self._extension_list.set_cursor(path)
			self._extension_list.scroll_to_cell(path)

	def _handle_cursor_change(self, widget, data=None):
		"""Handle selecting column editor extension"""
		selection = self._extension_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# get selected extension
			class_name = item_list.get_value(selected_iter, ExtensionColumn.CLASS_NAME)
			extension = self._extensions[class_name]

			# set selection as active extension
			self._active_extension = extension

			# clear existing list
			self._columns_store.clear()

			# populate columns list
			for column in extension.get_columns():
				size = extension.get_size(column)
				is_visible = extension.get_visible(column)
				font_size = extension.get_font_size(column)

				self._columns_store.append((column, size, is_visible, font_size))

	def _edited_column_size(self, cell, path, text, data=None):
		"""Handle editing column size"""
		selected_iter = self._columns_store.get_iter(path)

		if selected_iter is not None:
			old_size = self._columns_store.get_value(selected_iter, Column.SIZE)
			column_name = self._columns_store.get_value(selected_iter, Column.NAME)

			try:
				# make sure entered value is integer
				new_size = int(text)
			
			except ValueError:
				# if entered value is not integer, exception
				# will be raised and we just skip updating storage
				pass

			else:
				if new_size != old_size:
					self._columns_store.set_value(selected_iter, Column.SIZE, new_size)
					self._active_extension.set_size(column_name, new_size)
					self._parent.enable_save()

		return True

	def _edited_column_font_size(self, cell, path, text, data=None):
		"""Handle editing column size"""
		selected_iter = self._columns_store.get_iter(path)

		if selected_iter is not None:
			old_size = self._columns_store.get_value(selected_iter, Column.FONT_SIZE)
			column_name = self._columns_store.get_value(selected_iter, Column.NAME)

			try:
				# make sure entered value is integer
				new_size = None if int(text) == 0 else int(text)

			except ValueError:
				# if entered value is not integer, exception
				# will be raised and we just skip updating storage
				pass

			else:
				if new_size != old_size:
					self._columns_store.set_value(selected_iter, Column.FONT_SIZE, new_size)
					self._active_extension.set_font_size(column_name, new_size)
					self._parent.enable_save()

		return True

	def _toggle_column_visible(self, cell, path):
		"""Handle toggling column visibility"""
		selected_iter = self._columns_store.get_iter(path)

		if selected_iter is not None:
			is_visible = not self._columns_store.get_value(selected_iter, Column.VISIBLE)
			column_name = self._columns_store.get_value(selected_iter, Column.NAME)

			self._columns_store.set_value(selected_iter, Column.VISIBLE, is_visible)
			self._active_extension.set_visible(column_name, is_visible)

			self._parent.enable_save()

		return True

	def _load_options(self):
		"""Load item list options"""
		options = self._application.options
		section = options.section('item_list')

		# load options
		self._checkbox_row_hinting.set_active(section.get('row_hinting'))
		self._checkbox_show_hidden.set_active(section.get('show_hidden'))
		self._checkbox_case_sensitive.set_active(section.get('case_sensitive_sort'))
		self._checkbox_number_sensitive.set_active(section.get('number_sensitive_sort'))
		self._checkbox_single_click.set_active(section.get('single_click_navigation'))
		self._checkbox_right_click.set_active(section.get('right_click_select'))
		self._checkbox_show_headers.set_active(section.get('headers_visible'))
		self._checkbox_media_preview.set_active(options.get('media_preview'))
		self._combobox_breadcrumbs.set_active(section.get('breadcrumbs'))
		self._combobox_mode_format.set_active(section.get('mode_format'))
		self._combobox_grid_lines.set_active(section.get('grid_lines'))
		self._combobox_indicator.child.set_text(section.get('selection_indicator'))
		self._entry_time_format.set_text(section.get('time_format'))
		self._button_selection_color.set_color(gtk.gdk.color_parse(section.get('selection_color')))
		self._checkbox_load_directories.set_active(section.get('force_directories'))
		self._checkbox_show_expanders.set_active(section.get('show_expanders'))
		self._checkbox_hide_scrollbar.set_active(section.get('hide_horizontal_scrollbar'))

		search_modifier = section.get('search_modifier')
		self._checkbox_control.set_active(search_modifier[0] == '1')
		self._checkbox_alt.set_active(search_modifier[1] == '1')
		self._checkbox_shift.set_active(search_modifier[2] == '1')

		# load column settings
		map(lambda extension: extension._load_settings(), self._application.column_editor_extensions)

		# populate editor
		self._populate_column_editor_extensions()

		# load directories
		self._directory_store.clear()

		left_list = section.get('left_directories')
		right_list = section.get('right_directories')

		for path in set(left_list + right_list):
			self._directory_store.append((path, path in left_list, path in right_list))

	def _save_options(self):
		"""Save item list options"""
		options = self._application.options
		section = options.section('item_list')

		# save settings
		section.set('row_hinting', self._checkbox_row_hinting.get_active())
		section.set('show_hidden', self._checkbox_show_hidden.get_active())
		section.set('case_sensitive_sort', self._checkbox_case_sensitive.get_active())
		section.set('number_sensitive_sort', self._checkbox_number_sensitive.get_active())
		section.set('single_click_navigation', self._checkbox_single_click.get_active())
		section.set('right_click_select', self._checkbox_right_click.get_active())
		section.set('headers_visible', self._checkbox_show_headers.get_active())
		options.set('media_preview', self._checkbox_media_preview.get_active())
		section.set('breadcrumbs', self._combobox_breadcrumbs.get_active())
		section.set('mode_format', self._combobox_mode_format.get_active())
		section.set('grid_lines', self._combobox_grid_lines.get_active())
		section.set('time_format', self._entry_time_format.get_text())
		section.set('selection_color', self._button_selection_color.get_color().to_string())
		section.set('selection_indicator', self._combobox_indicator.get_active_text())
		section.set('force_directories', self._checkbox_load_directories.get_active())
		section.set('show_expanders', self._checkbox_show_expanders.get_active())
		section.set('hide_horizontal_scrollbar', self._checkbox_hide_scrollbar.get_active())

		search_modifier = "%d%d%d" % (
								self._checkbox_control.get_active(),
								self._checkbox_alt.get_active(),
								self._checkbox_shift.get_active()
							)
		section.set('search_modifier', search_modifier)

		# save column settings
		map(lambda extension: extension._save_settings(), self._application.column_editor_extensions)

		# save directories
		left_list = []
		right_list = []

		for row in self._directory_store:
			path = row[DirectoryColumn.PATH]
			add_to_left = row[DirectoryColumn.LEFT_LIST]
			add_to_right = row[DirectoryColumn.RIGHT_LIST]

			if add_to_left:
				left_list.append(path)

			if add_to_right:
				right_list.append(path)

		section.set('left_directories', left_list)
		section.set('right_directories', right_list)

