from gi.repository import Gtk, Gdk

from sunflower.common import AccessModeFormat
from sunflower.widgets.breadcrumbs import Breadcrumbs
from sunflower.widgets.settings_page import SettingsPage
from sunflower.gui.input_dialog import InputDialog


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

		notebook = Gtk.Notebook()

		# create frames
		label_look_and_feel = Gtk.Label(label=_('Look & feel'))
		label_hidden_files = Gtk.Label(label=_('Hidden files'))
		label_operation = Gtk.Label(label=_('Operation'))
		label_directories = Gtk.Label(label=_('Directories'))
		label_columns = Gtk.Label(label=_('Columns'))

		# vertical boxes
		vbox_look_and_feel = Gtk.VBox(False, 0)
		vbox_hidden_files = Gtk.VBox(False, 0)
		vbox_operation = Gtk.VBox(False, 0)
		vbox_directory = Gtk.VBox(False, 0)
		vbox_columns = Gtk.VBox(False, 0)

		vbox_look_and_feel.set_border_width(5)
		vbox_hidden_files.set_border_width(5)
		vbox_operation.set_border_width(5)
		vbox_directory.set_border_width(5)
		vbox_directory.set_spacing(5)
		vbox_columns.set_border_width(5)

		# file list options
		self._checkbox_row_hinting = Gtk.CheckButton(_('Row hinting'))
		self._checkbox_case_sensitive = Gtk.CheckButton(_('Case sensitive item sorting'))
		self._checkbox_number_sensitive = Gtk.CheckButton(_('Number sensitive item sorting'))
		self._checkbox_single_click = Gtk.CheckButton(_('Single click navigation'))
		self._checkbox_right_click = Gtk.CheckButton(_('Right click selects items'))
		self._checkbox_show_headers = Gtk.CheckButton(_('Show list headers'))
		self._checkbox_media_preview = Gtk.CheckButton(_('Fast media preview'))
		self._checkbox_show_expanders = Gtk.CheckButton(_('Show tree expanders'))
		self._checkbox_second_extension = Gtk.CheckButton(_('Support second level extension'))

		self._checkbox_row_hinting.connect('toggled', self._parent.enable_save)
		self._checkbox_case_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_number_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_single_click.connect('toggled', self._parent.enable_save)
		self._checkbox_right_click.connect('toggled', self._parent.enable_save)
		self._checkbox_show_headers.connect('toggled', self._parent.enable_save)
		self._checkbox_media_preview.connect('toggled', self._parent.enable_save)
		self._checkbox_show_expanders.connect('toggled', self._parent.enable_save)
		self._checkbox_second_extension.connect('toggled', self._parent.enable_save)

		# file access mode format
		hbox_mode_format = Gtk.HBox(False, 5)
		label_mode_format = Gtk.Label(label=_('Access mode format:'))
		label_mode_format.set_alignment(0, 0.5)

		self._combobox_mode_format = Gtk.ComboBoxText.new()
		self._combobox_mode_format.connect('changed', self._parent.enable_save)
		self._combobox_mode_format.append(str(AccessModeFormat.OCTAL), _('Octal'))
		self._combobox_mode_format.append(str(AccessModeFormat.TEXTUAL), _('Textual'))

		# grid lines
		hbox_grid_lines = Gtk.HBox(False, 5)
		label_grid_lines = Gtk.Label(label=_('Show grid lines:'))
		label_grid_lines.set_alignment(0, 0.5)

		self._combobox_grid_lines = Gtk.ComboBoxText.new()
		self._combobox_grid_lines.connect('changed', self._parent.enable_save)
		self._combobox_grid_lines.append(str(Gtk.TreeViewGridLines.NONE), _('None'))
		self._combobox_grid_lines.append(str(Gtk.TreeViewGridLines.HORIZONTAL), _('Horizontal'))
		self._combobox_grid_lines.append(str(Gtk.TreeViewGridLines.VERTICAL), _('Vertical'))
		self._combobox_grid_lines.append(str(Gtk.TreeViewGridLines.BOTH), _('Both'))

		# selection color
		hbox_selection_color = Gtk.HBox(False, 5)

		label_selection_color = Gtk.Label(label=_('Selection color:'))
		label_selection_color.set_alignment(0, 0.5)

		self._button_selection_color = Gtk.ColorButton()
		self._button_selection_color.set_use_alpha(False)
		self._button_selection_color.connect('color-set', self._parent.enable_save)

		# selection indicator
		hbox_indicator = Gtk.HBox(False, 5)

		label_indicator = Gtk.Label(label=_('Selection indicator:'))
		label_indicator.set_alignment(0, 0.5)

		self._combobox_indicator = Gtk.ComboBoxText.new_with_entry()
		self._combobox_indicator.connect('changed', self._parent.enable_save)
		self._combobox_indicator.set_size_request(100, -1)
		self._combobox_indicator.append_text(u'\u25b6',)
		self._combobox_indicator.append_text(u'\u25e2',)
		self._combobox_indicator.append_text(u'\u25c8',)
		self._combobox_indicator.append_text(u'\u263b',)
		self._combobox_indicator.append_text(u'\u2771',)
		self._combobox_indicator.append_text(u'\u2738',)
		self._combobox_indicator.append_text(u'\u2731',)

		# quick search
		label_quick_search = Gtk.Label(label=_('Quick search combination:'))
		label_quick_search.set_alignment(0, 0.5)
		label_quick_search.set_use_markup(True)
		self._checkbox_control = Gtk.CheckButton(_('Control'))
		self._checkbox_alt = Gtk.CheckButton(_('Alt'))
		self._checkbox_shift = Gtk.CheckButton(_('Shift'))

		self._checkbox_control.connect('toggled', self._parent.enable_save)
		self._checkbox_alt.connect('toggled', self._parent.enable_save)
		self._checkbox_shift.connect('toggled', self._parent.enable_save)

		hbox_quick_search = Gtk.HBox(False, 5)

		vbox_time_format = Gtk.VBox(False, 0)
		label_time_format = Gtk.Label(label=_('Date format:'))
		label_time_format.set_alignment(0, 0.5)
		self._entry_time_format = Gtk.Entry()
		self._entry_time_format.set_tooltip_markup(
								'<b>' + _('Time is formed using the format located at:') + '</b>\n'
								'http://docs.python.org/library/time.html#time.strftime'
							)
		self._entry_time_format.connect('changed', self._parent.enable_save)

		# hidden files
		table_always_visible = Gtk.Table(rows=3, columns=1, homogeneous=False)
		table_always_visible.set_row_spacing(1, 5)

		self._checkbox_show_hidden = Gtk.CheckButton(_('Show hidden files'))
		self._checkbox_show_hidden.connect('toggled', self._parent.enable_save)

		container_always_visible = Gtk.ScrolledWindow()
		container_always_visible.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		container_always_visible.set_shadow_type(Gtk.ShadowType.IN)

		label_always_visible = Gtk.Label(label=_('Always visible files and directories:'))
		label_always_visible.set_alignment(0, 0.5)

		self._always_visible_store = Gtk.ListStore(str)
		self._always_visible_list = Gtk.TreeView(model=self._always_visible_store)
		self._always_visible_list.set_headers_visible(False)

		cell_name = Gtk.CellRendererText()
		col_name = Gtk.TreeViewColumn(None, cell_name, text=0)

		self._always_visible_list.append_column(col_name)

		hbox_always_visible = Gtk.HBox(False, 5)

		button_add_always_visible = Gtk.Button(stock=Gtk.STOCK_ADD)
		button_add_always_visible.connect('clicked', self._add_always_visible)

		button_delete_always_visible = Gtk.Button(stock=Gtk.STOCK_DELETE)
		button_delete_always_visible.connect('clicked', self._delete_always_visible)

		# create list of directories
		container_directory = Gtk.ScrolledWindow()
		container_directory.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		container_directory.set_shadow_type(Gtk.ShadowType.IN)

		self._checkbox_load_directories = Gtk.CheckButton(_('Load specified tabs instead of saved'))
		self._checkbox_load_directories.connect('toggled', self._parent.enable_save)

		self._directory_store = Gtk.ListStore(str, bool, bool)
		self._directory_list = Gtk.TreeView(model=self._directory_store)

		cell_directory = Gtk.CellRendererText()
		cell_left_list = Gtk.CellRendererToggle()
		cell_right_list = Gtk.CellRendererToggle()

		cell_left_list.connect('toggled', self._toggle_path, Source.LEFT)
		cell_right_list.connect('toggled', self._toggle_path, Source.RIGHT)

		col_directory = Gtk.TreeViewColumn(_('Directory'), cell_directory, text=DirectoryColumn.PATH)
		col_directory.set_min_width(200)
		col_directory.set_resizable(True)
		col_directory.set_expand(True)

		col_left_list = Gtk.TreeViewColumn(_('Left list'), cell_left_list, active=DirectoryColumn.LEFT_LIST)
		col_right_list = Gtk.TreeViewColumn(_('Right list'), cell_right_list, active=DirectoryColumn.RIGHT_LIST)

		self._directory_list.append_column(col_directory)
		self._directory_list.append_column(col_left_list)
		self._directory_list.append_column(col_right_list)

		hbox_directory = Gtk.HBox(False, 5)

		button_add_directory = Gtk.Button(stock=Gtk.STOCK_ADD)
		button_add_directory.connect('clicked', self.__button_add_clicked)

		button_delete_directory = Gtk.Button(stock=Gtk.STOCK_DELETE)
		button_delete_directory.connect('clicked', self._delete_path)

		image_up = Gtk.Image()
		image_up.set_from_stock(Gtk.STOCK_GO_UP, Gtk.IconSize.BUTTON)

		button_directory_move_up = Gtk.Button(label=None)
		button_directory_move_up.add(image_up)
		button_directory_move_up.set_tooltip_text(_('Move Up'))
		button_directory_move_up.connect('clicked', self._move_path, -1)

		image_down = Gtk.Image()
		image_down.set_from_stock(Gtk.STOCK_GO_DOWN, Gtk.IconSize.BUTTON)

		button_directory_move_down = Gtk.Button(label=None)
		button_directory_move_down.add(image_down)
		button_directory_move_down.set_tooltip_text(_('Move Down'))
		button_directory_move_down.connect('clicked', self._move_path, 1)

		self._menu_add_directory = Gtk.Menu()

		menu_item_custom = Gtk.MenuItem(_('Custom directory'))
		menu_item_separator = Gtk.SeparatorMenuItem()
		menu_item_left_directory = Gtk.MenuItem(_('Left directory'))
		menu_item_right_directory = Gtk.MenuItem(_('Right directory'))

		menu_item_custom.connect('activate', self._add_path, Source.CUSTOM)
		menu_item_left_directory.connect('activate', self._add_path, Source.LEFT)
		menu_item_right_directory.connect('activate', self._add_path, Source.RIGHT)

		self._menu_add_directory.append(menu_item_custom)
		self._menu_add_directory.append(menu_item_separator)
		self._menu_add_directory.append(menu_item_left_directory)
		self._menu_add_directory.append(menu_item_right_directory)

		self._menu_add_directory.show_all()

		# create columns editor
		hbox_columns = Gtk.HBox(False, 5)

		container_columns = Gtk.ScrolledWindow()
		container_columns.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		container_columns.set_shadow_type(Gtk.ShadowType.IN)

		container_plugin = Gtk.ScrolledWindow()
		container_plugin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		container_plugin.set_shadow_type(Gtk.ShadowType.IN)
		container_plugin.set_size_request(170, -1)

		# create variable to store active extension to
		self._extensions = {}
		self._active_extension = None

		# create column list
		self._columns_store = Gtk.ListStore(str, int, bool, str)
		self._columns_list = Gtk.TreeView()
		self._columns_list.set_model(self._columns_store)
		self._columns_list.set_rules_hint(True)
		self._columns_list.set_enable_search(True)
		self._columns_list.set_search_column(Column.NAME)

		cell_name = Gtk.CellRendererText()
		cell_size = Gtk.CellRendererText()
		cell_visible = Gtk.CellRendererToggle()
		cell_font_size = Gtk.CellRendererSpin()

		cell_size.set_property('editable', True)
		cell_size.set_property('mode', Gtk.CellRendererMode.EDITABLE)
		cell_size.connect('edited', self._edited_column_size)

		cell_font_size.set_property('editable', True)
		cell_font_size.set_property('mode', Gtk.CellRendererMode.EDITABLE)
		adjustment = Gtk.Adjustment(0, 0, 100, 1, 10, 0)
		cell_font_size.set_property('adjustment', adjustment)
		cell_font_size.connect('edited', self._edited_column_font_size)

		cell_visible.connect('toggled', self._toggle_column_visible)

		col_name = Gtk.TreeViewColumn(_('Column'), cell_name, text=Column.NAME)
		col_name.set_min_width(150)
		col_name.set_resizable(True)
		col_name.set_expand(True)

		col_size = Gtk.TreeViewColumn(_('Size'), cell_size, text=Column.SIZE)
		col_size.set_min_width(50)

		col_visible = Gtk.TreeViewColumn(_('Visible'), cell_visible, active=Column.VISIBLE)
		col_visible.set_min_width(50)

		col_font_size = Gtk.TreeViewColumn(_('Font'), cell_font_size, text=Column.FONT_SIZE)
		col_font_size.set_min_width(50)

		self._columns_list.append_column(col_name)
		self._columns_list.append_column(col_size)
		self._columns_list.append_column(col_font_size)
		self._columns_list.append_column(col_visible)

		# create plugin list
		self._extension_store = Gtk.ListStore(str, str)
		self._extension_list = Gtk.TreeView()
		self._extension_list.set_model(self._extension_store)
		self._extension_list.set_headers_visible(False)

		self._extension_list.connect('cursor-changed', self._handle_cursor_change)

		cell_name = Gtk.CellRendererText()
		col_name = Gtk.TreeViewColumn(None, cell_name, text=ExtensionColumn.NAME)

		self._extension_list.append_column(col_name)

		# pack interface
		container_directory.add(self._directory_list)
		container_columns.add(self._columns_list)
		container_plugin.add(self._extension_list)
		container_always_visible.add(self._always_visible_list)

		hbox_always_visible.pack_start(button_add_always_visible, False, False, 0)
		hbox_always_visible.pack_start(button_delete_always_visible, False, False, 0)

		table_always_visible.attach(label_always_visible, 0, 1, 0, 1, xoptions=Gtk.AttachOptions.SHRINK | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.SHRINK)
		table_always_visible.attach(container_always_visible, 0, 1, 1, 2, xoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL)
		table_always_visible.attach(hbox_always_visible, 0, 1, 2, 3, xoptions=Gtk.AttachOptions.SHRINK | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.SHRINK)

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

		hbox_mode_format.pack_start(label_mode_format, False, False, 0)
		hbox_mode_format.pack_start(self._combobox_mode_format, False, False, 0)

		hbox_grid_lines.pack_start(label_grid_lines, False, False, 0)
		hbox_grid_lines.pack_start(self._combobox_grid_lines, False, False, 0)

		vbox_time_format.pack_start(label_time_format, False, False, 0)
		vbox_time_format.pack_start(self._entry_time_format, False, False, 0)

		vbox_look_and_feel.pack_start(self._checkbox_row_hinting, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_headers, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_media_preview, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_expanders, False, False, 0)
		vbox_look_and_feel.pack_start(hbox_mode_format, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_grid_lines, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_selection_color, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_indicator, False, False, 5)

		vbox_hidden_files.pack_start(self._checkbox_show_hidden, False, False, 0)
		vbox_hidden_files.pack_start(table_always_visible, True, True, 0)

		vbox_operation.pack_start(self._checkbox_case_sensitive, False, False, 0)
		vbox_operation.pack_start(self._checkbox_number_sensitive, False, False, 0)
		vbox_operation.pack_start(self._checkbox_single_click, False, False, 0)
		vbox_operation.pack_start(self._checkbox_right_click, False, False, 0)
		vbox_operation.pack_start(self._checkbox_second_extension, False, False, 0)
		vbox_operation.pack_start(hbox_quick_search, False, False, 5)
		vbox_operation.pack_start(vbox_time_format, False, False, 5)

		vbox_directory.pack_start(self._checkbox_load_directories, False, False, 0)
		vbox_directory.pack_start(container_directory, True, True, 0)
		vbox_directory.pack_start(hbox_directory, False, False, 0)

		vbox_columns.pack_start(hbox_columns, True, True, 0)

		notebook.append_page(vbox_look_and_feel, label_look_and_feel)
		notebook.append_page(vbox_hidden_files, label_hidden_files)
		notebook.append_page(vbox_operation, label_operation)
		notebook.append_page(vbox_directory, label_directories)
		notebook.append_page(vbox_columns, label_columns)

		self.pack_start(notebook, True, True, 0)

	def __button_add_clicked(self, widget, data=None):
		"""Handle clicking on add button"""
		self._menu_add_directory.popup(None, None, self.__get_menu_position, widget, 1, 0)

	def __get_menu_position(self, menu, *args):
		"""Get history menu position"""
		# get coordinates
		button = args[-1]
		window_x, window_y = self._parent.get_window().get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return pos_x, pos_y, True

	def _add_always_visible(self, widget, data=None):
		"""Add item name to the list of always visible files and directories."""
		# show dialog
		dialog = InputDialog(self._parent)
		dialog.set_title(_('Add always visible item'))
		dialog.set_label(_('Full name of file or directory to always show:'))

		response = dialog.get_response()

		# add data to the list
		if response[0] == Gtk.ResponseType.OK:
			self._always_visible_store.append((response[1],))
			self._parent.enable_save()

	def _delete_always_visible(self, widget, data=None):
		"""Delete selected item from the list of always visible files and directories."""
		selection = self._always_visible_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# remove item from the store
			item_list.remove(selected_iter)

			# enable save button if item was removed
			self._parent.enable_save()

	def _add_path(self, widget, source):
		"""Add path to the list from specified source"""
		if source == Source.CUSTOM:
			# show dialog for custom path entry
			dialog = InputDialog(self._parent)
			dialog.set_title(_('Add custom directory'))
			dialog.set_label(_('Full path:'))

			response = dialog.get_response()

			if response[0] == Gtk.ResponseType.OK:
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
			dialog = Gtk.MessageDialog(
									self._application,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
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
		self._combobox_mode_format.set_active(section.get('mode_format'))
		self._combobox_grid_lines.set_active(section.get('grid_lines'))
		self._combobox_indicator.get_child().set_text(section.get('selection_indicator'))
		self._entry_time_format.set_text(section.get('time_format'))
		self._button_selection_color.set_color(Gdk.color_parse(section.get('selection_color')))
		self._checkbox_load_directories.set_active(section.get('force_directories'))
		self._checkbox_show_expanders.set_active(section.get('show_expanders'))
		self._checkbox_second_extension.set_active(section.get('second_extension'))

		search_modifier = section.get('search_modifier')
		self._checkbox_control.set_active(search_modifier[0] == '1')
		self._checkbox_alt.set_active(search_modifier[1] == '1')
		self._checkbox_shift.set_active(search_modifier[2] == '1')

		# load always visible items
		always_visible = section.get('always_visible')

		self._always_visible_store.clear()
		for item in always_visible:
			self._always_visible_store.append((item,))

		# load column settings
		for extension in self._application.column_editor_extensions:
			extension._load_settings()

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
		section.set('mode_format', self._combobox_mode_format.get_active())
		section.set('grid_lines', self._combobox_grid_lines.get_active())
		section.set('time_format', self._entry_time_format.get_text())
		section.set('selection_color', self._button_selection_color.get_color().to_string())
		section.set('selection_indicator', self._combobox_indicator.get_active_text())
		section.set('force_directories', self._checkbox_load_directories.get_active())
		section.set('show_expanders', self._checkbox_show_expanders.get_active())
		section.set('second_extension', self._checkbox_second_extension.get_active())

		search_modifier = "%d%d%d" % (
								self._checkbox_control.get_active(),
								self._checkbox_alt.get_active(),
								self._checkbox_shift.get_active()
							)
		section.set('search_modifier', search_modifier)

		# save always visible items
		always_visible = [ row[0] for row in self._always_visible_store ]
		section.set('always_visible', always_visible)

		# save column settings
		for extension in self._application.column_editor_extensions:
			extension._save_settings()

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

