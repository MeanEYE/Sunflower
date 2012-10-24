import gtk

from common import AccessModeFormat
from widgets.settings_page import SettingsPage


class Column:
	NAME = 0
	SIZE = 1
	VISIBLE = 2


class ExtensionColumn:
	NAME = 0
	CLASS_NAME = 1


class ItemListOptions(SettingsPage):
	"""Options related to item lists"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'item_list', _('Item List'))

		notebook = gtk.Notebook()

		# create frames
		label_look_and_feel = gtk.Label(_('Look & feel'))
		label_operation = gtk.Label(_('Operation'))
		label_columns = gtk.Label(_('Columns'))

		# vertical boxes
		vbox_look_and_feel = gtk.VBox(False, 0)
		vbox_operation = gtk.VBox(False, 0)
		vbox_columns = gtk.VBox(False, 0)

		vbox_look_and_feel.set_border_width(5)
		vbox_operation.set_border_width(5)
		vbox_columns.set_border_width(5)

		# file list options
		self._checkbox_row_hinting = gtk.CheckButton(_('Row hinting'))
		self._checkbox_show_hidden = gtk.CheckButton(_('Show hidden files'))
		self._checkbox_case_sensitive = gtk.CheckButton(_('Case sensitive item sorting'))
		self._checkbox_right_click = gtk.CheckButton(_('Right click selects items'))
		self._checkbox_trash_files = gtk.CheckButton(_('Delete items to trash can'))
		self._checkbox_reserve_size = gtk.CheckButton(_('Reserve free space on copy/move'))
		self._checkbox_show_headers = gtk.CheckButton(_('Show list headers'))
		self._checkbox_media_preview = gtk.CheckButton(_('Fast media preview'))

		self._checkbox_row_hinting.connect('toggled', self._parent.enable_save)
		self._checkbox_show_hidden.connect('toggled', self._parent.enable_save)
		self._checkbox_case_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_right_click.connect('toggled', self._parent.enable_save)
		self._checkbox_trash_files.connect('toggled', self._parent.enable_save)
		self._checkbox_reserve_size.connect('toggled', self._parent.enable_save)
		self._checkbox_show_headers.connect('toggled', self._parent.enable_save)
		self._checkbox_media_preview.connect('toggled', self._parent.enable_save)

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
		self._columns_store = gtk.ListStore(str, int, bool)
		self._columns_list = gtk.TreeView()

		self._columns_list.set_model(self._columns_store)
		self._columns_list.set_rules_hint(True)
		self._columns_list.set_enable_search(True)
		self._columns_list.set_search_column(Column.NAME)

		cell_name = gtk.CellRendererText()
		cell_size = gtk.CellRendererText()
		cell_visible = gtk.CellRendererToggle()

		cell_size.set_property('editable', True)
		cell_size.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_size.connect('edited', self._edited_column_size)

		cell_visible.connect('toggled', self._toggle_column_visible)

		col_name = gtk.TreeViewColumn(_('Column'), cell_name, text=Column.NAME)
		col_name.set_min_width(150)
		col_name.set_resizable(True)
		col_name.set_expand(True)

		col_size = gtk.TreeViewColumn(_('Size'), cell_size, text=Column.SIZE)
		col_size.set_min_width(50)

		col_visible = gtk.TreeViewColumn(_('Visible'), cell_visible, active=Column.VISIBLE)
		col_visible.set_min_width(50)

		self._columns_list.append_column(col_name)
		self._columns_list.append_column(col_size)
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
		container_columns.add(self._columns_list)
		container_plugin.add(self._extension_list)

		hbox_columns.pack_start(container_plugin, False, False, 0)
		hbox_columns.pack_start(container_columns, True, True, 0)

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
		vbox_look_and_feel.pack_start(self._checkbox_show_hidden, False, False, 0)
		vbox_look_and_feel.pack_start(hbox_mode_format, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_grid_lines, False, False, 5)
		vbox_look_and_feel.pack_start(hbox_selection_color, False, False, 5)

		vbox_operation.pack_start(self._checkbox_case_sensitive, False, False, 0)
		vbox_operation.pack_start(self._checkbox_right_click, False, False, 0)
		vbox_operation.pack_start(self._checkbox_trash_files, False, False, 0)
		vbox_operation.pack_start(self._checkbox_reserve_size, False, False, 0)
		vbox_operation.pack_start(hbox_quick_search, False, False, 5)
		vbox_operation.pack_start(vbox_time_format, False, False, 5)

		vbox_columns.pack_start(hbox_columns, True, True, 0)

		notebook.append_page(vbox_look_and_feel, label_look_and_feel)
		notebook.append_page(vbox_operation, label_operation)
		notebook.append_page(vbox_columns, label_columns)

		self.pack_start(notebook, True, True, 0)

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

				self._columns_store.append((column, size, is_visible))

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
		self._checkbox_right_click.set_active(section.get('right_click_select'))
		self._checkbox_trash_files.set_active(options.section('operations').get('trash_files'))
		self._checkbox_reserve_size.set_active(options.section('operations').get('reserve_size'))
		self._checkbox_show_headers.set_active(section.get('headers_visible'))
		self._checkbox_media_preview.set_active(options.get('media_preview'))
		self._combobox_mode_format.set_active(section.get('mode_format'))
		self._combobox_grid_lines.set_active(section.get('grid_lines'))
		self._entry_time_format.set_text(section.get('time_format'))
		self._button_selection_color.set_color(gtk.gdk.color_parse(section.get('selection_color')))

		search_modifier = section.get('search_modifier')
		self._checkbox_control.set_active(search_modifier[0] == '1')
		self._checkbox_alt.set_active(search_modifier[1] == '1')
		self._checkbox_shift.set_active(search_modifier[2] == '1')

		# load column settings
		map(lambda extension: extension._load_settings(), self._application.column_editor_extensions)

		# populate editor
		self._populate_column_editor_extensions()

	def _save_options(self):
		"""Save item list options"""
		options = self._application.options
		section = options.section('item_list')

		# save settings
		section.set('row_hinting', self._checkbox_row_hinting.get_active())
		section.set('show_hidden', self._checkbox_show_hidden.get_active())
		section.set('case_sensitive_sort', self._checkbox_case_sensitive.get_active())
		section.set('right_click_select', self._checkbox_right_click.get_active())
		options.section('operations').set('trash_files', self._checkbox_trash_files.get_active())
		options.section('operations').set('reserve_size', self._checkbox_reserve_size.get_active())
		section.set('headers_visible', self._checkbox_show_headers.get_active())
		options.set('media_preview', self._checkbox_media_preview.get_active())
		section.set('mode_format', self._combobox_mode_format.get_active())
		section.set('grid_lines', self._combobox_grid_lines.get_active())
		section.set('time_format', self._entry_time_format.get_text())
		section.set('selection_color', self._button_selection_color.get_color().to_string())

		search_modifier = "%d%d%d" % (
								self._checkbox_control.get_active(),
								self._checkbox_alt.get_active(),
								self._checkbox_shift.get_active()
							)
		section.set('search_modifier', search_modifier)

		# save column settings
		map(lambda extension: extension._save_settings(), self._application.column_editor_extensions)
