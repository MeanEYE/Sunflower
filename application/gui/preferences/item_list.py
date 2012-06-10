import gtk

import common
from widgets.settings_page import SettingsPage


class ItemListOptions(SettingsPage):
	"""Options related to item lists"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'item_list', _('Item List'))

		notebook = gtk.Notebook()

		# create frames
		label_look_and_feel = gtk.Label(_('Look & feel'))
		label_operation = gtk.Label(_('Operation'))

		# vertical boxes
		vbox_look_and_feel = gtk.VBox(False, 0)
		vbox_operation = gtk.VBox(False, 0)

		vbox_look_and_feel.set_border_width(5)
		vbox_operation.set_border_width(5)

		# file list options
		self._checkbox_row_hinting = gtk.CheckButton(_('Row hinting'))
		self._checkbox_show_hidden = gtk.CheckButton(_('Show hidden files'))
		self._checkbox_case_sensitive = gtk.CheckButton(_('Case sensitive item sorting'))
		self._checkbox_right_click = gtk.CheckButton(_('Right click selects items'))
		self._checkbox_trash_files = gtk.CheckButton(_('Delete items to trash can'))
		self._checkbox_show_headers = gtk.CheckButton(_('Show list headers'))
		self._checkbox_media_preview = gtk.CheckButton(_('Fast media preview'))

		self._checkbox_row_hinting.connect('toggled', self._parent.enable_save)
		self._checkbox_show_hidden.connect('toggled', self._parent.enable_save)
		self._checkbox_case_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_right_click.connect('toggled', self._parent.enable_save)
		self._checkbox_trash_files.connect('toggled', self._parent.enable_save)
		self._checkbox_show_headers.connect('toggled', self._parent.enable_save)
		self._checkbox_media_preview.connect('toggled', self._parent.enable_save)

		# file access mode format
		hbox_mode_format = gtk.HBox(False, 5)
		label_mode_format = gtk.Label(_('File access mode format:'))
		label_mode_format.set_alignment(0, 0.5)

		list_mode_format = gtk.ListStore(str, int)
		list_mode_format.append((_('Octal'), common.ModeFormat.OCTAL))
		list_mode_format.append((_('Textual'), common.ModeFormat.TEXTUAL))

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

		# pack interface
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
		vbox_operation.pack_start(hbox_quick_search, False, False, 5)
		vbox_operation.pack_start(vbox_time_format, False, False, 5)

		notebook.append_page(vbox_look_and_feel, label_look_and_feel)
		notebook.append_page(vbox_operation, label_operation)

		self.pack_start(notebook, True, True, 0)

	def _vim_bindings_toggled(self, widget, data=None):
		"""Handle toggling VIM bindings on or off"""
		if widget.get_active() \
		and self._application.options.get('main', 'search_modifier') == '000':
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

	def _load_options(self):
		"""Load item list options"""
		options = self._application.options

		self._checkbox_row_hinting.set_active(options.getboolean('main', 'row_hinting'))
		self._checkbox_show_hidden.set_active(options.getboolean('main', 'show_hidden'))
		self._checkbox_case_sensitive.set_active(options.getboolean('main', 'case_sensitive_sort'))
		self._checkbox_right_click.set_active(options.getboolean('main', 'right_click_select'))
		self._checkbox_trash_files.set_active(options.getboolean('main', 'trash_files'))
		self._checkbox_show_headers.set_active(options.getboolean('main', 'headers_visible'))
		self._checkbox_media_preview.set_active(options.getboolean('main', 'media_preview'))
		self._combobox_mode_format.set_active(options.getint('main', 'mode_format'))
		self._combobox_grid_lines.set_active(options.getint('main', 'grid_lines'))
		self._entry_time_format.set_text(options.get('main', 'time_format'))
		self._button_selection_color.set_color(gtk.gdk.color_parse(options.get('main', 'selection_color')))

		search_modifier = options.get('main', 'search_modifier')
		self._checkbox_control.set_active(search_modifier[0] == '1')
		self._checkbox_alt.set_active(search_modifier[1] == '1')
		self._checkbox_shift.set_active(search_modifier[2] == '1')

	def _save_options(self):
		"""Save item list options"""
		options = self._application.options
		_bool = ('False', 'True')

		options.set('main', 'row_hinting', _bool[self._checkbox_row_hinting.get_active()])
		options.set('main', 'show_hidden', _bool[self._checkbox_show_hidden.get_active()])
		options.set('main', 'case_sensitive_sort', _bool[self._checkbox_case_sensitive.get_active()])
		options.set('main', 'right_click_select', _bool[self._checkbox_right_click.get_active()])
		options.set('main', 'trash_files', _bool[self._checkbox_trash_files.get_active()])
		options.set('main', 'headers_visible', _bool[self._checkbox_show_headers.get_active()])
		options.set('main', 'media_preview', _bool[self._checkbox_media_preview.get_active()])
		options.set('main', 'mode_format', self._combobox_mode_format.get_active())
		options.set('main', 'grid_lines', self._combobox_grid_lines.get_active())
		options.set('main', 'time_format', self._entry_time_format.get_text())
		options.set('main', 'selection_color', self._button_selection_color.get_color().to_string())

		search_modifier = "%d%d%d" % (
								self._checkbox_control.get_active(),
								self._checkbox_alt.get_active(),
								self._checkbox_shift.get_active()
							)
		options.set('main', 'search_modifier', search_modifier)
