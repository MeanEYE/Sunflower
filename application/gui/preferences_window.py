import gtk

from widgets.settings_page import SettingsPage 

VISIBLE_ALWAYS		= 0
VISIBLE_WHEN_NEEDED	= 1
VISIBLE_NEVER		= 2

COL_NAME	= 0
COL_WIDGET	= 1


class PreferencesWindow(gtk.Window):

	def __init__(self, parent):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self._parent = parent
		self._tab_names = {}

		# configure self
		self.connect('delete_event', self._hide)
		self.set_title(_('Preferences'))
		self.set_size_request(640, 500)
		self.set_modal(True)
		self.set_skip_taskbar_hint(True)
		self.set_transient_for(parent)
		self.set_wmclass('Sunflower', 'Sunflower')

		# create GUI
		vbox = gtk.VBox(False, 10)
		vbox.set_border_width(10)
		
		hbox = gtk.HBox(False, 10)

		# create tab label container
		label_container = gtk.ScrolledWindow()
		label_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		label_container.set_shadow_type(gtk.SHADOW_IN)
		label_container.set_size_request(130, -1)
		
		self._labels = gtk.ListStore(str, int)
		self._tab_labels = gtk.TreeView(self._labels)

		cell_label = gtk.CellRendererText()
		col_label = gtk.TreeViewColumn(None, cell_label, text=COL_NAME)
		
		self._tab_labels.append_column(col_label)
		self._tab_labels.set_headers_visible(False)
		self._tab_labels.connect('cursor-changed', self._handle_cursor_change)

		# create tabs
		self._tabs = gtk.Notebook()
		self._tabs.set_show_tabs(False)
		self._tabs.set_show_border(False)
		self._tabs.connect('switch-page', self._handle_page_switch)

		DisplayOptions(self, parent)
		ItemListOptions(self, parent)
		TerminalOptions(self, parent)
		ViewEditOptions(self, parent)
		ToolbarOptions(self, parent)
		BookmarkOptions(self, parent)
		ToolOptions(self, parent)
		PluginOptions(self, parent)

		# select first tab
		self._tab_labels.set_cursor((0,))

		# create buttons
		hbox_controls = gtk.HBox(False, 5)

		btn_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		btn_close.connect('clicked', self._hide)

		self._button_save = gtk.Button(stock=gtk.STOCK_SAVE)
		self._button_save.connect('clicked', self._save_options)

		btn_help = gtk.Button(stock=gtk.STOCK_HELP)
		btn_help.connect(
					'clicked',
					parent.goto_web,
					'code.google.com/p/sunflower-fm/wiki/WelcomePage?tm=6'
				)

		# restart label
		self._label_restart = gtk.Label('<i>{0}</i>'.format(_('Program restart required!')))
		self._label_restart.set_alignment(0.5, 0.5)
		self._label_restart.set_use_markup(True)
		self._label_restart.set_property('no-show-all', True)

		# pack buttons
		label_container.add(self._tab_labels)
		
		hbox.pack_start(label_container, False, False, 0)
		hbox.pack_start(self._tabs, True, True, 0)
		
		hbox_controls.pack_start(btn_help, False, False, 0)
		hbox_controls.pack_start(self._label_restart, True, True, 0)
		hbox_controls.pack_end(btn_close, False, False, 0)
		hbox_controls.pack_end(self._button_save, False, False, 0)

		# pack UI
		vbox.pack_start(hbox, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)

		self.add(vbox)

	def _show(self, widget, tab_name=None):
		"""Show dialog and reload options"""
		self._load_options()
		self.show_all()

		if tab_name is not None and self._tab_names.has_key(tab_name):
			self._tabs.set_current_page(self._tab_names[tab_name])

	def _hide(self, widget, data=None):
		"""Hide dialog"""
		self.hide()
		return True  # avoid destroying components

	def _load_options(self):
		"""Change interface to present current state of configuration"""
		# call all tabs to load their options
		for i in range(self._tabs.get_n_pages()):
			page = self._tabs.get_nth_page(i)

			if hasattr(page, '_load_options'):
				page._load_options()

		# disable save button and hide label
		self._button_save.set_sensitive(False)
		self._label_restart.hide()

	def _save_options(self, widget, data=None):
		"""Save options"""
		# call all tabs to save their options
		for i in range(self._tabs.get_n_pages()):
			page = self._tabs.get_nth_page(i)

			if hasattr(page, '_save_options'):
				page._save_options()

		# disable save button
		self._button_save.set_sensitive(False)

		# call main window to propagate new settings
		self._parent.apply_settings()

		# write changes to configuration file
		self._parent.save_config()
		
	def _handle_cursor_change(self, widget, data=None):
		"""Change active tab when cursor is changed"""
		selection = self._tab_labels.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			new_tab = list_.get_value(iter_, COL_WIDGET)

			self._tabs.handler_block_by_func(self._handle_page_switch)
			self._tabs.set_current_page(new_tab)
			self._tabs.handler_unblock_by_func(self._handle_page_switch)
			
	def _handle_page_switch(self, widget, page, page_num, data=None):
		"""Handle changing page without user interaction"""
		self._tab_labels.handler_block_by_func(self._handle_cursor_change)
		self._tab_labels.set_cursor((page_num,))
		self._tab_labels.handler_unblock_by_func(self._handle_cursor_change)

	def enable_save(self, widget=None, show_restart=None):
		"""Enable save button"""
		self._button_save.set_sensitive(True)

		# show label with message
		if show_restart is not None and show_restart:
			self._label_restart.show()
			
	def add_tab(self, name, label, tab):
		"""Add new tab to preferences window
		
		If you are using SettingsPage class there's no need to call this
		method manually, class constructor will do it automatically for you!
		
		"""
		tab_number = self._tabs.get_n_pages()
		
		self._tab_names[name] = tab_number
		self._labels.append((label, tab_number))
		self._tabs.append_page(tab)


class DisplayOptions(SettingsPage):
	"""Display options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'display', _('Display'))

		# main window options
		frame_main_window = gtk.Frame(_('Main window'))
		vbox_main_window = gtk.VBox(False, 0)
		vbox_main_window.set_border_width(5)

		self._checkbox_hide_on_close = gtk.CheckButton(_('Hide main window on close'))
		self._checkbox_show_toolbar = gtk.CheckButton(_('Show toolbar'))
		self._checkbox_show_command_bar = gtk.CheckButton(_('Show command bar'))
		self._checkbox_show_command_entry = gtk.CheckButton(_('Show command entry'))

		self._checkbox_hide_on_close.connect('toggled', self._parent.enable_save, True)
		self._checkbox_show_toolbar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_bar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_entry.connect('toggled', self._parent.enable_save)

		# tab options
		frame_tabs = gtk.Frame(_('Tabs'))
		vbox_tabs = gtk.VBox(False, 0)
		vbox_tabs.set_border_width(5)

		self._checkbox_focus_new_tab = gtk.CheckButton(_('Focus new tab after opening'))
		self._checkbox_button_relief = gtk.CheckButton(_('Show normal button relief'))
		self._checkbox_button_icons = gtk.CheckButton(_('Show icons instead of text in tab buttons'))
		self._checkbox_tab_close_button = gtk.CheckButton(_('Show close button'))
		self._checkbox_always_show_tabs = gtk.CheckButton(_('Show tab(s) even if there is only one'))
		self._checkbox_ubuntu_coloring = gtk.CheckButton(_('Use Ubuntu coloring method for tab title bars'))

		self._checkbox_focus_new_tab.connect('toggled', self._parent.enable_save)
		self._checkbox_button_relief.connect('toggled', self._parent.enable_save)
		self._checkbox_button_icons.connect('toggled', self._parent.enable_save, True)
		self._checkbox_tab_close_button.connect('toggled', self._parent.enable_save)
		self._checkbox_always_show_tabs.connect('toggled', self._parent.enable_save)
		self._checkbox_ubuntu_coloring.connect('toggled', self._parent.enable_save)

		vbox_status_bar = gtk.VBox(False, 0)
		vbox_status_bar.set_border_width(5)

		label_status_bar = gtk.Label(_('Show status bar:'))
		label_status_bar.set_alignment(0, 0.5)

		list_status_bar = gtk.ListStore(str, int)
		list_status_bar.append((_('Always'), VISIBLE_ALWAYS))
		list_status_bar.append((_('When needed'), VISIBLE_WHEN_NEEDED))
		list_status_bar.append((_('Never'), VISIBLE_NEVER))

		cell_status_bar = gtk.CellRendererText()

		self._combobox_status_bar = gtk.ComboBox(list_status_bar)
		self._combobox_status_bar.connect('changed', self._parent.enable_save)
		self._combobox_status_bar.pack_start(cell_status_bar)
		self._combobox_status_bar.add_attribute(cell_status_bar, 'text', 0)

		# operation options
		frame_operation = gtk.Frame(_('Other'))
		vbox_operation = gtk.VBox(False, 0)
		vbox_operation.set_border_width(5)

		self._checkbox_hide_window_on_minimize = gtk.CheckButton(_('Hide operation window on minimize'))
		self._checkbox_human_readable_size = gtk.CheckButton(_('Show sizes in human readable format'))

		self._checkbox_hide_window_on_minimize.connect('toggled', self._parent.enable_save)
		self._checkbox_human_readable_size.connect('toggled', self._parent.enable_save)

		# pack ui
		vbox_status_bar.pack_start(label_status_bar, False, False, 0)
		vbox_status_bar.pack_start(self._combobox_status_bar, False, False, 0)

		vbox_main_window.pack_start(self._checkbox_hide_on_close, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_toolbar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_bar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_entry, False, False, 0)

		vbox_tabs.pack_start(self._checkbox_focus_new_tab, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_button_relief, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_button_icons, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_tab_close_button, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_always_show_tabs, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_ubuntu_coloring, False, False, 0)
		vbox_tabs.pack_start(vbox_status_bar, False, False, 0)

		vbox_operation.pack_start(self._checkbox_hide_window_on_minimize, False, False, 0)
		vbox_operation.pack_start(self._checkbox_human_readable_size, False, False, 0)

		frame_main_window.add(vbox_main_window)
		frame_tabs.add(vbox_tabs)
		frame_operation.add(vbox_operation)

		self.pack_start(frame_main_window, False, False, 0)
		self.pack_start(frame_tabs, False, False, 0)
		self.pack_start(frame_operation, False, False, 0)

	def _load_options(self):
		"""Load display options"""
		options = self._application.options

		self._checkbox_hide_on_close.set_active(options.getboolean('main', 'hide_on_close'))
		self._checkbox_focus_new_tab.set_active(options.getboolean('main', 'focus_new_tab'))
		self._checkbox_show_toolbar.set_active(options.getboolean('main', 'show_toolbar'))
		self._checkbox_show_command_bar.set_active(options.getboolean('main', 'show_command_bar'))
		self._checkbox_show_command_entry.set_active(options.getboolean('main', 'show_command_entry'))
		self._checkbox_button_relief.set_active(bool(options.getint('main', 'button_relief')))
		self._checkbox_button_icons.set_active(options.getboolean('main', 'tab_button_icons'))
		self._checkbox_tab_close_button.set_active(options.getboolean('main', 'tab_close_button'))
		self._checkbox_always_show_tabs.set_active(options.getboolean('main', 'always_show_tabs'))
		self._checkbox_ubuntu_coloring.set_active(options.getboolean('main', 'ubuntu_coloring'))
		self._checkbox_hide_window_on_minimize.set_active(options.getboolean('main', 'hide_operation_on_minimize'))
		self._checkbox_human_readable_size.set_active(options.getboolean('main', 'human_readable_size'))
		self._combobox_status_bar.set_active(options.getint('main', 'show_status_bar'))

	def _save_options(self):
		"""Save display options"""
		options = self._application.options

		# for config parser to get boolean, you need to set string :/. makes sense?
		_bool = ('False', 'True')

		# save options
		options.set('main', 'hide_on_close', _bool[self._checkbox_hide_on_close.get_active()])
		options.set('main', 'focus_new_tab', _bool[self._checkbox_focus_new_tab.get_active()])
		options.set('main', 'show_toolbar', _bool[self._checkbox_show_toolbar.get_active()])
		options.set('main', 'show_command_bar', _bool[self._checkbox_show_command_bar.get_active()])
		options.set('main', 'show_command_entry', _bool[self._checkbox_show_command_entry.get_active()])
		options.set('main', 'button_relief', int(self._checkbox_button_relief.get_active()))
		options.set('main', 'tab_button_icons', _bool[self._checkbox_button_icons.get_active()])
		options.set('main', 'tab_close_button', _bool[self._checkbox_tab_close_button.get_active()])
		options.set('main', 'always_show_tabs', _bool[self._checkbox_always_show_tabs.get_active()])
		options.set('main', 'ubuntu_coloring', _bool[self._checkbox_ubuntu_coloring.get_active()])
		options.set('main', 'hide_operation_on_minimize', _bool[self._checkbox_hide_window_on_minimize.get_active()])
		options.set('main', 'human_readable_size', _bool[self._checkbox_human_readable_size.get_active()])
		options.set('main', 'show_status_bar', self._combobox_status_bar.get_active())


class ItemListOptions(SettingsPage):
	"""Options related to item lists"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'item_list', _('Item List'))

		# create frames
		frame_look_and_feel = gtk.Frame()
		frame_look_and_feel.set_label(_('Look & feel'))

		frame_operation = gtk.Frame()
		frame_operation.set_label(_('Operation'))

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
		self._checkbox_vim_bindings = gtk.CheckButton(_('Enable VIM bindings'))
		self._checkbox_show_headers = gtk.CheckButton(_('Show list headers'))
		self._checkbox_media_preview = gtk.CheckButton(_('Fast media preview'))

		self._checkbox_row_hinting.connect('toggled', self._parent.enable_save)
		self._checkbox_show_hidden.connect('toggled', self._parent.enable_save)
		self._checkbox_case_sensitive.connect('toggled', self._parent.enable_save)
		self._checkbox_right_click.connect('toggled', self._parent.enable_save)
		self._checkbox_vim_bindings.connect('toggled', self._vim_bindings_toggled)
		self._checkbox_show_headers.connect('toggled', self._parent.enable_save)
		self._checkbox_media_preview.connect('toggled', self._parent.enable_save)

		# grid lines
		vbox_grid_lines = gtk.VBox(False, 0)
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
		self._entry_time_format.connect('activate', self._parent.enable_save)

		vbox_status_text = gtk.VBox(False, 0)
		label_status_text = gtk.Label(_('Status text:'))
		label_status_text.set_alignment(0, 0.5)
		self._entry_status_text = gtk.Entry()
		self._entry_status_text.set_tooltip_markup(
								'<b>' + _('Replacement strings:') + '</b>\n'
								'<i>%dir_count</i>\t\t' + _('Total directory count') + '\n'
								'<i>%dir_sel</i>\t\t' + _('Selected directories count') + '\n'
								'<i>%file_count</i>\t\t' + _('Total file count') + '\n'
								'<i>%file_sel</i>\t\t' + _('Selected file count') + '\n'
								'<i>%size_total</i>\t\t' + _('Total size of files in directory') + '\n'
								'<i>%size_sel</i>\t\t' + _('Total size of selected files')
								)
		self._entry_status_text.connect('activate', self._parent.enable_save)

		# pack interface
		hbox_quick_search.pack_start(label_quick_search, False, False, 0)
		hbox_quick_search.pack_start(self._checkbox_control, False, False, 0)
		hbox_quick_search.pack_start(self._checkbox_alt, False, False, 0)
		hbox_quick_search.pack_start(self._checkbox_shift, False, False, 0)

		vbox_grid_lines.pack_start(label_grid_lines, False, False, 0)
		vbox_grid_lines.pack_start(self._combobox_grid_lines, False, False, 0)

		vbox_time_format.pack_start(label_time_format, False, False, 0)
		vbox_time_format.pack_start(self._entry_time_format, False, False, 0)

		vbox_status_text.pack_start(label_status_text, False, False, 0)
		vbox_status_text.pack_start(self._entry_status_text, False, False, 0)

		vbox_look_and_feel.pack_start(self._checkbox_row_hinting, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_headers, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_media_preview, False, False, 0)
		vbox_look_and_feel.pack_start(self._checkbox_show_hidden, False, False, 0)

		vbox_operation.pack_start(self._checkbox_case_sensitive, False, False, 0)
		vbox_operation.pack_start(self._checkbox_right_click, False, False, 0)
		vbox_operation.pack_start(self._checkbox_vim_bindings, False, False, 0)
		vbox_operation.pack_start(hbox_quick_search, False, False, 5)
		vbox_operation.pack_start(vbox_grid_lines, False, False, 5)
		vbox_operation.pack_start(vbox_time_format, False, False, 5)
		vbox_operation.pack_start(vbox_status_text, False, False, 5)

		frame_look_and_feel.add(vbox_look_and_feel)
		frame_operation.add(vbox_operation)

		self.pack_start(frame_look_and_feel, False, False, 0)
		self.pack_start(frame_operation, False, False, 0)

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
		self._checkbox_vim_bindings.set_active(options.getboolean('main', 'vim_movement'))
		self._checkbox_show_headers.set_active(options.getboolean('main', 'headers_visible'))
		self._checkbox_media_preview.set_active(options.getboolean('main', 'media_preview'))
		self._combobox_grid_lines.set_active(options.getint('main', 'grid_lines'))
		self._entry_time_format.set_text(options.get('main', 'time_format'))
		self._entry_status_text.set_text(options.get('main', 'status_text'))

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
		options.set('main', 'vim_movement', _bool[self._checkbox_vim_bindings.get_active()])
		options.set('main', 'headers_visible', _bool[self._checkbox_show_headers.get_active()])
		options.set('main', 'media_preview', _bool[self._checkbox_media_preview.get_active()])
		options.set('main', 'grid_lines', self._combobox_grid_lines.get_active())
		options.set('main', 'time_format', self._entry_time_format.get_text())
		options.set('main', 'status_text', self._entry_status_text.get_text())

		search_modifier = "%d%d%d" % (
								self._checkbox_control.get_active(),
								self._checkbox_alt.get_active(),
								self._checkbox_shift.get_active()
							)
		options.set('main', 'search_modifier', search_modifier)


class ViewEditOptions(SettingsPage):
	"""View & Edit options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'view_and_edit', _('View & Edit'))

		# viewer options
		frame_view = gtk.Frame(_('View'))

		label_not_implemented = gtk.Label('This option is not implemented yet.')
		label_not_implemented.set_sensitive(False)

		# editor options
		frame_edit = gtk.Frame(_('Edit'))

		vbox_edit = gtk.VBox(False, 0)
		vbox_edit.set_border_width(5)

		# external options
		radio_external = gtk.RadioButton(label=_('Use external editor'))

		vbox_external = gtk.VBox(False, 0)
		vbox_external.set_border_width(10)

		label_editor = gtk.Label(_('Command line:'))
		label_editor.set_alignment(0, 0.5)
		label_editor.set_use_markup(True)
		self._entry_editor = gtk.Entry()
		self._entry_editor.connect('activate', self._parent.enable_save)

		self._checkbox_wait_for_editor = gtk.CheckButton(_('Wait for editor process to end'))
		self._checkbox_wait_for_editor.connect('toggled', self._parent.enable_save)

		# internal options
		radio_internal = gtk.RadioButton(
									group=radio_external,
									label=_('Use internal editor') + ' (not implemented)'
								)
		radio_internal.set_sensitive(False)

		vbox_internal = gtk.VBox(False, 0)
		vbox_internal.set_border_width(5)

		# pack ui
		vbox_external.pack_start(label_editor, False, False, 0)
		vbox_external.pack_start(self._entry_editor, False, False, 0)
		vbox_external.pack_start(self._checkbox_wait_for_editor, False, False, 0)

		vbox_edit.pack_start(radio_external, False, False, 0)
		vbox_edit.pack_start(vbox_external, False, False, 0)
		vbox_edit.pack_start(radio_internal, False, False, 0)
		vbox_edit.pack_start(vbox_internal, False, False, 0)

		frame_view.add(label_not_implemented)
		frame_edit.add(vbox_edit)

		self.pack_start(frame_view, False, False, 0)
		self.pack_start(frame_edit, False, False, 0)

	def _load_options(self):
		"""Load options"""
		options = self._application.options

		self._entry_editor.set_text(options.get('main', 'default_editor'))
		self._checkbox_wait_for_editor.set_active(options.getboolean('main', 'wait_for_editor'))

	def _save_options(self):
		"""Save options"""
		options = self._application.options
		bool = ('False', 'True')

		options.set('main', 'default_editor', self._entry_editor.get_text())
		options.set('main', 'wait_for_editor', bool[self._checkbox_wait_for_editor.get_active()])


class ToolbarOptions(SettingsPage):
	"""Toolbar options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'toolbar', _('Toolbar'))

		self._toolbar_manager = self._application.toolbar_manager

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._store = gtk.ListStore(str, str, str, str)
		self._list = gtk.TreeView()
		self._list.set_model(self._store)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_type = gtk.CellRendererText()

		# create name column
		col_name = gtk.TreeViewColumn(_('Name'))
		col_name.set_min_width(200)
		col_name.set_resizable(True)

		# pack and configure renderes
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.add_attribute(cell_icon, 'icon-name', 3)
		col_name.add_attribute(cell_name, 'text', 0)

		# create type column
		col_type = gtk.TreeViewColumn(_('Type'), cell_type, markup=1)
		col_type.set_resizable(True)
		col_type.set_expand(True)

		# add columns to the list
		self._list.append_column(col_name)
		self._list.append_column(col_type)

		container.add(self._list)

		# create controls
		button_box = gtk.HBox(False, 5)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_widget)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_widget)

		button_edit = gtk.Button(stock=gtk.STOCK_EDIT)
		button_edit.connect('clicked', self._edit_widget)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_move_up = gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._move_widget, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_move_down = gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._move_widget, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_start(button_edit, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_widget(self, widget, data=None):
		"""Show dialog for creating toolbar widget"""
		widget_added = self._toolbar_manager.show_create_widget_dialog(self._parent)

		if widget_added:
			# reload configuratin file
			self._load_options()

			# enable save button
			self._parent.enable_save()

	def _delete_widget(self, widget, data=None):
		"""Delete selected toolbar widget"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# remove item from list
			list_.remove(iter_)

			# enable save button if item was removed
			self._parent.enable_save()

	def _edit_widget(self, widget, data=None):
		"""Edit selected toolbar widget"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			name = list_.get_value(iter_, 0)
			widget_type = list_.get_value(iter_, 2)

			edited = self._toolbar_manager.show_configure_widget_dialog(
			                                                name,
			                                                widget_type,
			                                                self._parent
			                                            )

			# enable save button
			if edited:
				self._parent.enable_save()

	def _move_widget(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get iter index
			index = list_.get_path(iter_)[0]

			# depending on direction, swap iters
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list_) - 1):
				list_.swap(iter_, list_[index + direction].iter)

			# enable save button if iters were swapped
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		toolbar_options = self._application.toolbar_options
		count = len(toolbar_options.options('widgets')) / 2

		# clear list store
		self._store.clear()

		for number in range(0, count):
			name = toolbar_options.get('widgets', 'name_{0}'.format(number))
			widget_type = toolbar_options.get('widgets', 'type_{0}'.format(number))

			data = self._toolbar_manager.get_widget_data(widget_type)

			if data is not None:
				icon = data[1]
				description = data[0]

			else:  # failsafe, display raw widget type
				icon = ''
				description = '{0} <small><i>({1})</i></small>'.format(widget_type, _('missing plugin'))

			self._store.append((name, description, widget_type, icon))

	def _save_options(self):
		"""Save settings to config file"""
		toolbar_options = self._application.toolbar_options
		count = len(self._store)

		# get section list, we'll use this
		# list to remove orphan configurations
		section_list = toolbar_options.sections()

		# clear section
		toolbar_options.remove_section('widgets')
		toolbar_options.add_section('widgets')
		section_list.pop(section_list.index('widgets'))

		# write widgets in specified order
		for number in range(0, count):
			data = self._store[number]
			toolbar_options.set('widgets', 'name_{0}'.format(number), data[0])
			toolbar_options.set('widgets', 'type_{0}'.format(number), data[2])

			# remove section from temporary list
			section_name = self._toolbar_manager.get_section_name(data[0])
			section_list.pop(section_list.index(section_name))

		# remove orphan configurations
		for section in section_list:
			toolbar_options.remove_section(section)


class BookmarkOptions(SettingsPage):
	"""Bookmark options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'bookmarks', _('Bookmarks'))

		# mounts checkbox
		self._checkbox_show_mount_points = gtk.CheckButton(_('Show mount points in bookmarks menu'))
		self._checkbox_show_mount_points.connect('toggled', self._parent.enable_save)

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

		col_title = gtk.TreeViewColumn(_('Title'), cell_title, text=0)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn(_('Location'), cell_command, text=1)
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
		iter_ = self._bookmarks.get_iter(path)
		self._bookmarks.set_value(iter_, column, text)

		# enable save button
		self._parent.enable_save()

	def _delete_bookmark(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# remove item from the store
			list_.remove(iter_)

			# enable save button if item was removed
			self._parent.enable_save()

	def _move_bookmark(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get iter index
			index = list_.get_path(iter_)[0]

			# depending on direction, swap iters
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list_) - 1):
				list_.swap(iter_, list_[index + direction].iter)

			# enable save button if iters were swapped
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		options = self._application.options
		bookmark_options = self._application.bookmark_options

		# get checkbox states
		self._checkbox_show_mount_points.set_active(options.getboolean('main', 'show_mounts'))
		self._checkbox_add_home.set_active(options.getboolean('main', 'add_home'))

		# load and parse bookmars
		if bookmark_options.has_section('bookmarks'):
			item_list = bookmark_options.options('bookmarks')

			self._bookmarks.clear()

			for index in range(1, len(item_list) + 1):
				bookmark = bookmark_options.get('bookmarks', 'b_{0}'.format(index)).split(';', 1)
				self._bookmarks.append((bookmark[0], bookmark[1]))

	def _save_options(self):
		"""Save bookmarks to file"""
		options = self._application.options
		bookmark_options = self._application.bookmark_options
		_bool = ('False', 'True')

		# save show mounts checkbox state
		options.set('main', 'show_mounts', _bool[self._checkbox_show_mount_points.get_active()])
		options.set('main', 'add_home', _bool[self._checkbox_add_home.get_active()])

		# save bookmars
		bookmark_options.remove_section('bookmarks')
		bookmark_options.add_section('bookmarks')

		for i, bookmark in enumerate(self._bookmarks, 1):
			bookmark_options.set(
								'bookmarks',
								'b_{0}'.format(i),
								'{0};{1}'.format(bookmark[0], bookmark[1])
								)


class ToolOptions(SettingsPage):
	"""Tools options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'tools', _('Tools Menu'))

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._tools = gtk.ListStore(str, str)

		self._list = gtk.TreeView()
		self._list.set_model(self._tools)
		self._list.set_rules_hint(True)

		# create and configure cell renderers
		cell_title = gtk.CellRendererText()
		cell_title.set_property('editable', True)
		cell_title.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_title.connect('edited', self._edited_tool, 0)

		cell_command = gtk.CellRendererText()
		cell_command.set_property('editable', True)
		cell_command.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_command.connect('edited', self._edited_tool, 1)

		# create and pack columns
		col_title = gtk.TreeViewColumn(_('Title'), cell_title, text=0)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn(_('Command'), cell_command, text=1)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)

		container.add(self._list)

		# create controls
		button_box = gtk.HBox(False, 5)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_tool)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_tool)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_move_up = gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._move_tool, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_move_down = gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._move_tool, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_tool(self, widget, data=None):
		"""Add new tool to the store"""
		if data is None:
			data = ('New tool', '')

		# add new item to store
		self._tools.append(data)

		# enable save button on parent
		self._parent.enable_save()

	def _edited_tool(self, cell, path, text, column):
		"""Record edited text"""
		iter_ = self._tools.get_iter(path)
		self._tools.set_value(iter_, column, text)

		# enable save button
		self._parent.enable_save()

	def _delete_tool(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# remove item from the list
			list_.remove(iter_)

			# enable save button in case item was removed
			self._parent.enable_save()

	def _move_tool(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get iter index
			index = list_.get_path(iter_)[0]

			# swap iters depending on specified direction
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list_) - 1):
				list_.swap(iter_, list_[index + direction].iter)

			# it items were swapped, enable save button
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		tool_options = self._application.tool_options

		# load and parse tools
		if tool_options.has_section('tools'):
			item_list = tool_options.options('tools')
			self._tools.clear()

			for index in range(1, (len(item_list) / 2) + 1):
				tool_title = tool_options.get('tools', 'title_{0}'.format(index))
				tool_command = tool_options.get('tools', 'command_{0}'.format(index))

				# add item to the store
				self._tools.append((tool_title, tool_command))

	def _save_options(self):
		"""Save bookmarks to file"""
		tool_options = self._application.tool_options

		# save bookmars
		tool_options.remove_section('tools')
		tool_options.add_section('tools')

		for index, tool in enumerate(self._tools, 1):
			tool_options.set('tools', 'title_{0}'.format(index), tool[0])
			tool_options.set('tools', 'command_{0}'.format(index), tool[1])


class TerminalOptions(SettingsPage):
	"""Terminal options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'terminal', _('Terminal'))

		# create interface
		self._checkbox_scrollbars_visible = gtk.CheckButton(_('Show scrollbars when needed'))
		self._checkbox_scrollbars_visible.connect('toggled', self._parent.enable_save)

		# pack interface
		self.pack_start(self._checkbox_scrollbars_visible, False, False, 0)

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options

		self._checkbox_scrollbars_visible.set_active(options.getboolean('main', 'terminal_scrollbars'))

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options
		_bool = ('False', 'True')

		options.set('main', 'terminal_scrollbars', _bool[self._checkbox_scrollbars_visible.get_active()])


class PluginOptions(SettingsPage):
	"""Plugins options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'plugins', _('Plugins'))

		# create interface
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		# create list box
		self._plugins = gtk.ListStore(bool, str)

		self._list = gtk.TreeView()
		self._list.set_model(self._plugins)
		self._list.set_rules_hint(True)

		# create and configure cell renderers
		cell_active = gtk.CellRendererToggle()
		cell_active.connect('toggled', self._toggle_plugin)
		cell_name = gtk.CellRendererText()

		# create and pack columns
		col_active = gtk.TreeViewColumn(_('Active'), cell_active, active=0)

		col_name = gtk.TreeViewColumn(_('Plugin file'), cell_name, text=1)
		col_name.set_resizable(True)
		col_name.set_expand(True)

		self._list.append_column(col_active)
		self._list.append_column(col_name)

		container.add(self._list)
		self.pack_start(container, True, True, 0)

	def _toggle_plugin(self, cell, path):
		"""Handle changing plugin state"""
		plugin = self._plugins[path][1]

		if plugin not in self._application.protected_plugins:
			# plugin is not protected, toggle it's state
			self._plugins[path][0] = not self._plugins[path][0]

			# enable save button
			self._parent.enable_save(show_restart=True)

		else:
			# plugin is protected, show appropriate message
			dialog = gtk.MessageDialog(
									self._application,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_INFO,
									gtk.BUTTONS_OK,
									_(
										"Specified plugin ('{0}') is required for "
										"normal program operation and therefore can "
										"not be deactivated!"
									).format(plugin)
								)

			dialog.run()
			dialog.destroy()

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options

		# clear existing list
		self._plugins.clear()

		# get list of plugins
		list_ = self._application._get_plugin_list()
		plugins_to_load = options.get('main', 'plugins').split(',')

		# populate list
		for plugin in list_:
			self._plugins.append((
							plugin in plugins_to_load,
							plugin
						))

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options

		# get only selected plugins
		list_ = filter(lambda row: row[0], self._plugins)

		# we need only plugin names
		list_ = [row[1] for row in list_]

		# save plugin list
		options.set('main', 'plugins', ','.join(list_))
