#!/usr/bin/env python

import gtk

class OptionsWindow(gtk.Window):

	def __init__(self, parent):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.connect('delete_event', self._hide)
		self.set_title('Options')
		self.set_size_request(600, 500)
		self.set_modal(True)
		self.set_skip_taskbar_hint(True)
		self.set_deletable(False)

		# create gui
		vbox = gtk.VBox(False, 5)
		vbox.set_border_width(5)

		# create tabs
		self._tabs = gtk.Notebook()
		self._tabs.set_tab_pos(gtk.POS_LEFT)

		self._tabs.append_page(
					DisplayOptions(self, parent),
					gtk.Label('Display')
					)
		self._tabs.append_page(
					ViewEditOptions(self, parent),
					gtk.Label('View & Edit')
					)
		self._tabs.append_page(
					ToolbarOptions(self, parent),
					gtk.Label('Toolbar')
					)
		self._tabs.append_page(
					BookmarkOptions(self, parent),
					gtk.Label('Bookmarks')
					)
		self._tabs.append_page(
					ToolOptions(self, parent),
					gtk.Label('Tools')
					)

		# create buttons
		hbox = gtk.HBox(False, 2)
		hbox.set_border_width(5)

		btn_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		btn_close.connect('clicked', self._hide)

		self._btn_save = gtk.Button(stock=gtk.STOCK_SAVE)
		self._btn_save.connect('clicked', self._save_options)

		hbox.pack_end(btn_close, False, False, 0)
		hbox.pack_end(self._btn_save, False, False, 0)

		# pack gui
		vbox.pack_start(self._tabs, True, True, 0)
		vbox.pack_start(hbox, False, False, 0)

		self.add(vbox)

	def _show(self, widget, data=None):
		"""Show dialog and reload options"""
		self._load_options()
		self.show_all()

	def _hide(self, widget, data=None):
		"""Hide dialog"""
		self.hide()
		return True  # avoid destroying components
	
	def _load_options(self):
		"""Change interface to present current state of configuration"""
		for i in range(self._tabs.get_n_pages()):
			page = self._tabs.get_nth_page(i)
			
			if hasattr(page, '_load_options'):
				page._load_options()
				
		self._btn_save.set_sensitive(False)
	
	def _save_options(self, widget, data=None):
		"""Save options"""
		for i in range(self._tabs.get_n_pages()):
			page = self._tabs.get_nth_page(i)
			
			if hasattr(page, '_save_options'):
				page._save_options()
		
		self._btn_save.set_sensitive(False)
		
	def enable_save(self, widget=None, data=None):
		"""Enable save button"""
		self._btn_save.set_sensitive(True)


class DisplayOptions(gtk.VBox):
	"""Display options extension class"""

	def __init__(self, parent, application):
		gtk.VBox.__init__(self, False, False)

		self._parent = parent
		self._application = application

		# configure self
		self.set_border_width(10)
		self.set_spacing(5)

		# main window options
		frame_main_window = gtk.Frame('Main window')
		vbox_main_window = gtk.VBox(False, 0)
		vbox_main_window.set_border_width(5)

		self._checkbox_hide_on_close = gtk.CheckButton('Hide main window on close')
		self._checkbox_focus_new_tab = gtk.CheckButton('Focus new tab after opening')
		self._checkbox_show_toolbar = gtk.CheckButton('Show toolbar')
		self._checkbox_show_command_bar = gtk.CheckButton('Show command bar')
		
		self._checkbox_hide_on_close.connect('toggled', self._parent.enable_save)
		self._checkbox_focus_new_tab.connect('toggled', self._parent.enable_save)
		self._checkbox_show_toolbar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_bar.connect('toggled', self._parent.enable_save)

		# file list options
		frame_file_list = gtk.Frame('File list')
		vbox_file_list = gtk.VBox(False, 0)
		vbox_file_list.set_border_width(5)

		self._checkbox_row_hinting = gtk.CheckButton('Row hinting')
		self._checkbox_show_hidden = gtk.CheckButton('Show hidden files')
		self._checkbox_show_mount_points = gtk.CheckButton('Show mount points on bookmarks menu')
		
		self._checkbox_row_hinting.connect('toggled', self._parent.enable_save)
		self._checkbox_show_hidden.connect('toggled', self._parent.enable_save)
		self._checkbox_show_mount_points.connect('toggled', self._parent.enable_save)

		vbox_grid_lines = gtk.VBox(False, 0)
		label_grid_lines = gtk.Label('Show grid lines:')
		label_grid_lines.set_alignment(0, 0.5)

		list_grid_lines = gtk.ListStore(str, int)
		list_grid_lines.append(('None', gtk.TREE_VIEW_GRID_LINES_NONE))
		list_grid_lines.append(('Horizontal', gtk.TREE_VIEW_GRID_LINES_HORIZONTAL))
		list_grid_lines.append(('Vertical', gtk.TREE_VIEW_GRID_LINES_VERTICAL))
		list_grid_lines.append(('Both', gtk.TREE_VIEW_GRID_LINES_BOTH))

		cell_grid_lines = gtk.CellRendererText()

		self._combobox_grid_lines = gtk.ComboBox(list_grid_lines)
		self._combobox_grid_lines.connect('changed', self._parent.enable_save)
		self._combobox_grid_lines.pack_start(cell_grid_lines)
		self._combobox_grid_lines.add_attribute(cell_grid_lines, 'text', 0)

		vbox_time_format = gtk.VBox(False, 0)
		label_time_format = gtk.Label('Date format:')
		label_time_format.set_alignment(0, 0.5)
		self._entry_time_format = gtk.Entry()
		self._entry_time_format.set_tooltip_markup(
								'<b>Time is formed using the format located at:</b>\n'
								'http://docs.python.org/library/time.html#time.strftime'
								)
		self._entry_time_format.connect('activate', self._parent.enable_save)
		
		vbox_status_text = gtk.VBox(False, 0)
		label_status_text = gtk.Label('Status text:')
		label_status_text.set_alignment(0, 0.5)
		self._entry_status_text = gtk.Entry()
		self._entry_status_text.set_tooltip_markup(
								'<b>Replacement strings:</b>\n'
								'<i>%(dir_count)i</i>\t\tTotal directory count\n'
								'<i>%(dir_count_sel)i</i>\tSelected directories count\n'
								'<i>%(file_count)i</i>\t\tTotal file count\n'
								'<i>%(file_count_sel)i</i>\tSelected file count'
								)
		self._entry_status_text.connect('activate', self._parent.enable_save)

		# pack ui
		vbox_grid_lines.pack_start(label_grid_lines, False, False, 0)
		vbox_grid_lines.pack_start(self._combobox_grid_lines, False, False, 0)
		
		vbox_time_format.pack_start(label_time_format, False, False, 0)
		vbox_time_format.pack_start(self._entry_time_format, False, False, 0)
		
		vbox_status_text.pack_start(label_status_text, False, False, 0)
		vbox_status_text.pack_start(self._entry_status_text, False, False, 0)

		vbox_main_window.pack_start(self._checkbox_hide_on_close, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_focus_new_tab, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_toolbar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_bar, False, False, 0)

		vbox_file_list.pack_start(self._checkbox_row_hinting, False, False, 0)
		vbox_file_list.pack_start(vbox_grid_lines, False, False, 5)
		vbox_file_list.pack_start(self._checkbox_show_hidden, False, False, 0)
		vbox_file_list.pack_start(self._checkbox_show_mount_points, False, False, 0)
		vbox_file_list.pack_start(vbox_time_format, False, False, 5)
		vbox_file_list.pack_start(vbox_status_text, False, False, 5)

		frame_main_window.add(vbox_main_window)
		frame_file_list.add(vbox_file_list)

		self.pack_start(frame_main_window, False, False, 0)
		self.pack_start(frame_file_list, False, False, 0)
		
	def _load_options(self):
		"""Load display options"""
		options = self._application.options
		
		self._checkbox_hide_on_close.set_active(options.getboolean('main', 'hide_on_close'))
		self._checkbox_focus_new_tab.set_active(options.getboolean('main', 'focus_new_tab'))
		self._checkbox_show_toolbar.set_active(options.getboolean('main', 'show_toolbar'))
		self._checkbox_show_command_bar.set_active(options.getboolean('main', 'show_command_bar'))
		self._checkbox_row_hinting.set_active(options.getboolean('main', 'row_hinting'))
		self._combobox_grid_lines.set_active(options.getint('main', 'grid_lines'))
		self._checkbox_show_hidden.set_active(options.getboolean('main', 'show_hidden'))
		self._checkbox_show_mount_points.set_active(options.getboolean('main', 'show_mounts'))
		self._entry_time_format.set_text(options.get('main', 'time_format'))
		self._entry_status_text.set_text(options.get('main', 'status_text'))
	
	def _save_options(self):
		"""Save display options"""
		options = self._application.options
		# for config parser to get boolean, you need to set string :/. makes sense?
		bool = ('False', 'True')
		
		# save options
		options.set('main', 'hide_on_close', bool[self._checkbox_hide_on_close.get_active()])
		options.set('main', 'focus_new_tab', bool[self._checkbox_focus_new_tab.get_active()])
		options.set('main', 'show_toolbar', bool[self._checkbox_show_toolbar.get_active()])
		options.set('main', 'show_command_bar', bool[self._checkbox_show_command_bar.get_active()])
		options.set('main', 'row_hinting', bool[self._checkbox_row_hinting.get_active()])
		options.set('main', 'grid_lines', self._combobox_grid_lines.get_active())
		options.set('main', 'show_hidden', bool[self._checkbox_show_hidden.get_active()])
		options.set('main', 'show_mounts', bool[self._checkbox_show_mount_points.get_active()])
		options.set('main', 'time_format', self._entry_time_format.get_text())
		options.set('main', 'status_text', self._entry_status_text.get_text())
		
		# change ui states
		show_hidden = self._application.menu_manager.get_item_by_name('show_hidden_files')
		show_hidden.set_active(self._checkbox_show_hidden.get_active())
			
		show_command_bar = self._application.menu_manager.get_item_by_name('show_command_bar')
		show_command_bar.set_active(self._checkbox_show_command_bar.get_active())
		
		show_toolbar = self._application.menu_manager.get_item_by_name('show_toolbar')
		show_toolbar.set_active(self._checkbox_show_toolbar.get_active())


class ViewEditOptions(gtk.VBox):
	"""View & Edit options extension class"""

	def __init__(self, parent, application):
		gtk.VBox.__init__(self, False, 0)

		self._parent = parent
		self._application = application

		# configure self
		self.set_border_width(10)
		self.set_spacing(5)

		# viewer options
		frame_view = gtk.Frame('View')

		label_not_implemented = gtk.Label('This option is not implemented yet.')
		label_not_implemented.set_sensitive(False)

		# editor options
		frame_edit = gtk.Frame('Edit')
		
		vbox_edit = gtk.VBox(False, 0)
		vbox_edit.set_border_width(5)

		# external options
		radio_external = gtk.RadioButton(label='Use external editor')
		
		vbox_external = gtk.VBox(False, 0)
		vbox_external.set_border_width(10)
		
		label_editor = gtk.Label('Command line:')
		label_editor.set_alignment(0, 0.5)
		label_editor.set_use_markup(True)
		self._entry_editor = gtk.Entry()
		self._entry_editor.connect('activate', self._parent.enable_save)
		
		self._checkbox_wait_for_editor = gtk.CheckButton('Wait for editor process to end')
		self._checkbox_wait_for_editor.connect('toggled', self._parent.enable_save)
		
		# internal options
		radio_internal = gtk.RadioButton(
									group=radio_external, 
									label='Use internal editor (not implemented)'
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


class ToolbarOptions(gtk.VBox):
	"""Toolbar options extension class"""

	def __init__(self, parent, application):
		gtk.VBox.__init__(self, False, 0)

		self._parent = parent
		self._application = application

		# configure self
		self.set_border_width(10)
		self.set_spacing(5)

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._list = gtk.TreeView()
		container.add(self._list)

		# create controls
		button_box = gtk.HButtonBox()
		button_box.set_layout(gtk.BUTTONBOX_START)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)

		button_move_up = gtk.Button('Move Up')
		button_move_down = gtk.Button('Move Down')

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_start(button_move_up, False, False, 0)
		button_box.pack_start(button_move_down, False, False, 0)

		button_box.set_child_secondary(button_move_up, True)
		button_box.set_child_secondary(button_move_down, True)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)


class BookmarkOptions(gtk.VBox):
	"""Bookmark options extension class"""

	def __init__(self, parent, application):
		gtk.VBox.__init__(self, False, 0)
		
		self._parent = parent
		self._application = application

		# configure self
		self.set_border_width(10)
		self.set_spacing(5)

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

		col_title = gtk.TreeViewColumn('Title', cell_title, text=0)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn('Location', cell_command, text=1)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)

		container.add(self._list)

		# create controls
		button_box = gtk.HButtonBox()
		button_box.set_layout(gtk.BUTTONBOX_START)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_bookmark)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_bookmark)

		button_move_up = gtk.Button('Move Up')
		button_move_up.connect('clicked', self._move_bookmark, -1)

		button_move_down = gtk.Button('Move Down')
		button_move_down.connect('clicked', self._move_bookmark, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_start(button_move_up, False, False, 0)
		button_box.pack_start(button_move_down, False, False, 0)

		button_box.set_child_secondary(button_move_up, True)
		button_box.set_child_secondary(button_move_down, True)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_bookmark(self, widget, data=None):
		"""Add new bookmark to the store"""

		if data is None:
			data = ('New bookmark', '')

		self._bookmarks.append(data)
		self._parent.enable_save()

	def _edited_bookmark(self, cell, path, text, column):
		"""Record edited text"""
		iter = self._bookmarks.get_iter(path)
		self._bookmarks.set_value(iter, column, text)
		self._parent.enable_save()

	def _delete_bookmark(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		list, iter = selection.get_selected()

		if iter is not None:
			list.remove(iter)
			
		self._parent.enable_save()

	def _move_bookmark(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list, iter = selection.get_selected()

		if iter is not None:
			index = list.get_path(iter)[0]

			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list) - 1):
				list.swap(iter, list[index + direction].iter)
				
		self._parent.enable_save()		
			
	def _load_options(self):
		"""Load options from file"""
		bookmark_options = self._application.bookmark_options
		
		if bookmark_options.has_section('bookmarks'):
			item_list = bookmark_options.options('bookmarks')
			item_list.sort()
			self._bookmarks.clear()
			
			for item in item_list:
				bookmark = bookmark_options.get('bookmarks', item).split(';', 1)
				self._bookmarks.append((bookmark[0], bookmark[1]))
		
	def _save_options(self):
		"""Save bookmarks to file"""
		bookmark_options = self._application.bookmark_options
		
		bookmark_options.remove_section('bookmarks')
		bookmark_options.add_section('bookmarks')
			
		for i, bookmark in enumerate(self._bookmarks, 1):
			bookmark_options.set(
								'bookmarks',
								'b_{0}'.format(i),
								'{0};{1}'.format(bookmark[0], bookmark[1])
								)
			
		# recreate bookmarks menu
		self._application._create_bookmarks_menu()

				
class ToolOptions(gtk.VBox):
	"""Bookmark options extension class"""

	def __init__(self, parent, application):
		gtk.VBox.__init__(self, False, 0)

		self._parent = parent
		self._application = application

		# configure self
		self.set_border_width(10)
		self.set_spacing(5)
