#!/usr/bin/env python

import gtk

class OptionsWindow(gtk.Window):

	def __init__(self, parent):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.connect('delete_event', self._hide)
		self.set_title('Options')
		self.set_size_request(600, 450)
		self.set_modal(True)
		self.set_skip_taskbar_hint(True)
		self.set_deletable(False)

		# create gui
		vbox = gtk.VBox(False, 5)
		vbox.set_border_width(5)

		# create tabs
		tabs = gtk.Notebook()
		tabs.set_tab_pos(gtk.POS_LEFT)

		tabs.append_page(
					DisplayOptions(),
					gtk.Label('Display')
					)
		tabs.append_page(
					ViewEditOptions(),
					gtk.Label('View & Edit')
					)
		tabs.append_page(
					ToolbarOptions(),
					gtk.Label('Toolbar')
					)
		tabs.append_page(
					BookmarkOptions(),
					gtk.Label('Bookmarks')
					)

		# create buttons
		hbox = gtk.HBox(False, 2)
		hbox.set_border_width(5)

		btn_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		btn_close.connect('clicked', self._hide)

		btn_save = gtk.Button(stock=gtk.STOCK_SAVE)
		btn_save.set_sensitive(False)
		
		hbox.pack_end(btn_close, False, False, 0)
		hbox.pack_end(btn_save, False, False, 0)

		# pack gui
		vbox.pack_start(tabs, True, True, 0)
		vbox.pack_start(hbox, False, False, 0)

		self.add(vbox)

	def _show(self, widget, data=None):
		self.show_all()

	def _hide(self, widget, data=None):
		self.hide()
		return True  # avoid destroying components
	
	
class DisplayOptions(gtk.VBox):
	"""Display options extension class"""
	
	def __init__(self):
		gtk.VBox.__init__(self, False, False)
		
		# configure self
		self.set_border_width(10)
		self.set_spacing(5)
		
		# main window options
		frame_main_window = gtk.Frame('Main window')
		vbox_main_window = gtk.VBox(False, 0)
		vbox_main_window.set_border_width(5)
		
		checkbox_hide_on_close = gtk.CheckButton('Hide main window on close')
		checkbox_focus_new_tab = gtk.CheckButton('Focus new tab after opening')
		checkbox_show_toolbar = gtk.CheckButton('Show toolbar')
		checkbox_show_command_bar = gtk.CheckButton('Show command bar')
		
		# file list options
		frame_file_list = gtk.Frame('File list')
		vbox_file_list = gtk.VBox(False, 0)
		vbox_file_list.set_border_width(5)
		
		checkbox_row_hinting = gtk.CheckButton('Row hinting')
		checkbox_show_hidden = gtk.CheckButton('Show hidden files')
		checkbox_show_mount_points = gtk.CheckButton('Show mount points on bookmarks menu')
		
		vbox_grid_lines = gtk.VBox(False, 0)
		label_grid_lines = gtk.Label('Show grid lines:')
		label_grid_lines.set_alignment(0, 0.1)
		
		list_grid_lines = gtk.ListStore(str, int)
		list_grid_lines.append(('None', gtk.TREE_VIEW_GRID_LINES_NONE))
		list_grid_lines.append(('Horizontal', gtk.TREE_VIEW_GRID_LINES_HORIZONTAL))
		list_grid_lines.append(('Vertical', gtk.TREE_VIEW_GRID_LINES_VERTICAL))
		list_grid_lines.append(('Both', gtk.TREE_VIEW_GRID_LINES_BOTH))
		
		cell_grid_lines = gtk.CellRendererText()
		
		combobox_grid_lines = gtk.ComboBox(list_grid_lines)
		combobox_grid_lines.pack_start(cell_grid_lines)
		combobox_grid_lines.add_attribute(cell_grid_lines, 'text', 0)
				
		# pack ui
		vbox_grid_lines.pack_start(label_grid_lines, False, False, 0)
		vbox_grid_lines.pack_start(combobox_grid_lines, False, False, 0)

		vbox_main_window.pack_start(checkbox_hide_on_close, False, False, 0)
		vbox_main_window.pack_start(checkbox_focus_new_tab, False, False, 0)
		vbox_main_window.pack_start(checkbox_show_toolbar, False, False, 0)
		vbox_main_window.pack_start(checkbox_show_command_bar, False, False, 0)
		
		vbox_file_list.pack_start(checkbox_row_hinting, False, False, 0)
		vbox_file_list.pack_start(vbox_grid_lines, False, False, 5)
		vbox_file_list.pack_start(checkbox_show_hidden, False, False, 0)
		vbox_file_list.pack_start(checkbox_show_mount_points, False, False, 0)
		
		frame_main_window.add(vbox_main_window)
		frame_file_list.add(vbox_file_list)
		
		self.pack_start(frame_main_window, False, False, 0)
		self.pack_start(frame_file_list, False, False, 0)


class ViewEditOptions(gtk.VBox):
	"""View & Edit options extension class"""
	
	def __init__(self):
		gtk.VBox.__init__(self, False, 0)
		
		# configure self
		self.set_border_width(10)
		self.set_spacing(5)


class ToolbarOptions(gtk.VBox):
	"""Toolbar options extension class"""
	
	def __init__(self):
		gtk.VBox.__init__(self, False, 0)
		
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
	
	def __init__(self):
		gtk.VBox.__init__(self, False, 0)
		
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
		
		col_command = gtk.TreeViewColumn('Command', cell_command, text=1)
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
		
	def _edited_bookmark(self, cell, path, text, column):
		"""Record edited text"""
		iter = self._bookmarks.get_iter(path)
		self._bookmarks.set_value(iter, column, text)

	def _delete_bookmark(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		list, iter = selection.get_selected()

		if iter is not None:
			list.remove(iter)
			
	def _move_bookmark(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list, iter = selection.get_selected()

		if iter is not None:
			index = list.get_path(iter)[0]

			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list) - 1):
				list.swap(iter, list[index + direction].iter)		