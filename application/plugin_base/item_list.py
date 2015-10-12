import os
import gtk
import urllib
import common
import user

from plugin import PluginBase
from operation import CopyOperation, MoveOperation
from accelerator_group import AcceleratorGroup
from parameters import Parameters
from tools.viewer import Viewer
from gui.input_dialog import CopyDialog, MoveDialog, InputDialog, PathInputDialog
from gui.preferences.display import StatusVisible
from gui.history_list import HistoryList
from history import HistoryManager
from plugin_base.provider import Mode as FileMode


class ButtonText:
	BOOKMARKS = u'\u2318'
	HISTORY = u'\u2630'
	TERMINAL = u'\u2605'
	TRASH = u'\u239a'


class ItemList(PluginBase):
	"""General item list

	Abstract class for all list based plugins. It provides basic
	user interface elements as well as some predefined methods.

	You are strongly encouraged to use predefined methods rather than
	defining your own.

	"""

	def __init__(self, parent, notebook, options):
		# call parent constructor
		PluginBase.__init__(self, parent, notebook, options)

		options = self._parent.options
		section = options.section('item_list')

		# store local stuff
		self._providers = {}
		self._current_provider = None
		self._menu_timer = None
		self._monitor_list = []

		self.history = []
		self.history_manager = HistoryManager(self, self.history)

		# list statistics
		self._dirs = {'count': 0, 'selected': 0}
		self._files = {'count': 0, 'selected': 0}
		self._size = {'total': 0L, 'selected': 0L}

		# preload commonly used options
		self._size_format = self._parent.options.get('size_format')
		self._selection_color = section.get('selection_color')
		self._selection_indicator = section.get('selection_indicator')
		self._second_extension = section.get('second_extension')

		# we use this variable to prevent dead loop during column resize
		self._is_updating = False

		# sort options
		self._sort_column = self._options.get('sort_column')
		self._sort_ascending = self._options.get('sort_ascending')
		self._sort_column_widget = None
		self._sort_case_sensitive = section.get('case_sensitive_sort')
		self._sort_number_sensitive = section.get('number_sensitive_sort')
		self._columns = []

		# configure status bar
		self._status_bar.add_group_with_icon('dirs', 'folder', '0/0', tooltip=_('Directories (selected/total)'))
		self._status_bar.add_group_with_icon('files', 'document', '0/0', tooltip=_('Files (selected/total)'))
		self._status_bar.add_group_with_icon('size', 'add', '0/0', tooltip=_('Size (selected/total)'))

		# file list
		self._container = gtk.ScrolledWindow()
		self._container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		self._container.set_shadow_type(gtk.SHADOW_IN)

		self._item_list = gtk.TreeView()
		self._item_list.set_fixed_height_mode(True)

		# apply header visibility
		headers_visible = section.get('headers_visible')
		self._item_list.set_headers_visible(headers_visible)

		# apply scrollbar visibility
		hide_scrollbar = section.get('hide_horizontal_scrollbar')
		scrollbar_horizontal = self._container.get_hscrollbar()
		scrollbar_horizontal.set_child_visible(not hide_scrollbar)

		# connect events
		self._item_list.connect('button-press-event', self._handle_button_press)
		self._item_list.connect('button-release-event', self._handle_button_press)
		self._item_list.connect('cursor-changed', self._handle_cursor_change)
		self._item_list.connect('columns-changed', self._column_changed)
		self._connect_main_object(self._item_list)

		self._container.add(self._item_list)

		# quick search
		self._search_panel = gtk.HBox(False, 0)

		label = gtk.Label(_('Search:'))

		self._search_entry = gtk.Entry()
		self._search_entry.connect('key-press-event', self._handle_search_key_press)
		self._search_entry.connect('focus-out-event', self._stop_search)
		self._item_list.set_search_entry(self._search_entry)

		compare = lambda model, column, key, iter_: key.lower() not in model.get_value(iter_, column).lower()
		self._item_list.set_search_equal_func(compare)

		self._search_panel.pack_start(label, False, False, 3)
		self._search_panel.pack_start(self._search_entry, True, True, 0)

		# popup menu
		self._open_with_item = None
		self._open_with_menu = None
		self._popup_menu = self._create_popup_menu()

		# tab menu
		self._tab_menu = gtk.Menu()
		self._title_bar.set_menu(self._tab_menu)

		# create reload menu item
		image_refresh = gtk.Image()
		image_refresh.set_from_icon_name('reload', gtk.ICON_SIZE_MENU)

		menu_item_refresh = gtk.ImageMenuItem()
		menu_item_refresh.set_label(_('Reload item list'))
		menu_item_refresh.set_image(image_refresh)
		menu_item_refresh.connect('activate', self.refresh_file_list)
		menu_item_refresh.show()
		self._tab_menu.append(menu_item_refresh)

		# create copy path item
		separator_path = gtk.SeparatorMenuItem()
		separator_path.show()
		self._tab_menu.append(separator_path)

		image_copy = gtk.Image()
		image_copy.set_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)

		menu_item_copy_path = gtk.ImageMenuItem()
		menu_item_copy_path.set_label(_('Copy path to clipboard'))
		menu_item_copy_path.set_image(image_copy)
		menu_item_copy_path.connect('activate', self.copy_path_to_clipboard)
		menu_item_copy_path.show()
		self._tab_menu.append(menu_item_copy_path)

		# create path entry item
		menu_path_entry = gtk.MenuItem()
		menu_path_entry.set_label(_('Enter path...'))
		menu_path_entry.connect('activate', self.custom_path_entry)
		menu_path_entry.show()
		self._tab_menu.append(menu_path_entry)

		# history menu
		self._history_menu = gtk.Menu()

		# emblem menu
		self._emblem_menu = gtk.Menu()
		self._prepare_emblem_menu()

		# pack gui
		self.pack_start(self._container, True, True, 0)
		self.pack_start(self._search_panel, False, False, 0)

		self.show_all()
		self._search_panel.hide()

	def _create_buttons(self):
		"""Create titlebar buttons."""
		options = self._parent.options

		# bookmarks button
		self._bookmarks_button = gtk.Button()

		if options.get('tab_button_icons'):
			image_bookmarks = gtk.Image()
			image_bookmarks.set_from_icon_name('go-jump', gtk.ICON_SIZE_MENU)
			self._bookmarks_button.set_image(image_bookmarks)

		else:
			self._bookmarks_button.set_label(ButtonText.BOOKMARKS)

		self._bookmarks_button.set_focus_on_click(False)
		self._bookmarks_button.set_tooltip_text(_('Bookmarks'))
		self._bookmarks_button.connect('clicked', self._bookmarks_button_clicked)

		self._title_bar.add_control(self._bookmarks_button)

		# history button
		self._history_button = gtk.Button()

		if options.get('tab_button_icons'):
			# set icon
			image_history = gtk.Image()
			image_history.set_from_icon_name('document-open-recent', gtk.ICON_SIZE_MENU)
			self._history_button.set_image(image_history)
		else:
			# set text
			self._history_button.set_label(ButtonText.HISTORY)

		self._history_button.set_focus_on_click(False)
		self._history_button.set_tooltip_text(_('History'))
		self._history_button.connect('clicked', self._history_button_clicked)

		self._title_bar.add_control(self._history_button)

		# terminal button
		self._terminal_button = gtk.Button()

		if options.get('tab_button_icons'):
			# set icon
			image_terminal = gtk.Image()
			image_terminal.set_from_icon_name('terminal', gtk.ICON_SIZE_MENU)
			self._terminal_button.set_image(image_terminal)
		else:
			# set text
			self._terminal_button.set_label(ButtonText.TERMINAL)

		self._terminal_button.set_focus_on_click(False)
		self._terminal_button.set_tooltip_text(_('Terminal'))
		self._terminal_button.connect('clicked', self._create_terminal)

		self._title_bar.add_control(self._terminal_button)

	def _configure_accelerators(self):
		"""Configure accelerator group"""
		group = AcceleratorGroup(self._parent)
		keyval = gtk.gdk.keyval_from_name

		# give parent chance to register its own accelerator group
		PluginBase._configure_accelerators(self)

		# configure accelerator group
		group.set_name('item_list')
		group.set_title(_('Item List'))

		# add all methods to group
		group.add_method('execute_item', _('Execute selected item'), self._execute_selected_item)
		group.add_method('execute_with_application', _('Select application and execute item'), self._execute_with_application)
		group.add_method('item_properties', _('Show selected item properties'), self._item_properties)
		group.add_method('add_bookmark', _('Bookmark current directory'), self._add_bookmark)
		group.add_method('edit_bookmarks', _('Edit bookmarks'), self._edit_bookmarks)
		group.add_method('cut_to_clipboard', _('Cut selection to clipboard'), self._cut_files_to_clipboard)
		group.add_method('copy_to_clipboard', _('Copy selection to clipboard'), self._copy_files_to_clipboard)
		group.add_method('paste_from_clipboard', _('Paste items from clipboard'), self._paste_files_from_clipboard)
		group.add_method('open_in_new_tab', _('Open selected directory in new tab'), self._open_in_new_tab)
		group.add_method('open_directory', _('Open selected directory'), self._open_directory)
		group.add_method('create_terminal', _('Create terminal tab'), self._create_terminal)
		group.add_method('parent_directory', _('Go to parent directory'), self._parent_directory)
		group.add_method('root_directory', _('Go to root directory'), self._root_directory)
		group.add_method('refresh_list', _('Reload items in current directory'), self.refresh_file_list)
		group.add_method('show_history', _('Show history browser'), self._show_history_window)
		group.add_method('back_in_history', _('Go back in history'), self._history_go_back)
		group.add_method('forward_in_history', _('Go forward in history'), self._history_go_forward)
		group.add_method('select_all', _('Select all'), self._select_all)
		group.add_method('deselect_all', _('Deselect all'), self._deselect_all)
		group.add_method('invert_selection', _('Invert selection'), self._invert_selection)
		group.add_method('toggle_selection', _('Toggle selection'), self._toggle_selection)
		group.add_method('toggle_selection_up', _('Toggle selection and move marker up'), self._toggle_selection_up)
		group.add_method('delete_files', _('Trash or delete selected items'), self._delete_files, False)
		group.add_method('force_delete_files', _('Force deleting selected items'), self._delete_files, True)
		group.add_method('show_bookmarks', _('Show bookmarks for current list'), self._show_bookmarks)
		group.add_method('show_left_bookmarks', _('Show bookmarks for left list'), self._show_left_bookmarks)
		group.add_method('show_right_bookmarks', _('Show bookmarks for right list'), self._show_right_bookmarks)
		group.add_method('rename_file', _('Rename selected item'), self._rename_file)
		group.add_method('view_selected', _('View selected item'), self._view_selected)
		group.add_method('edit_selected', _('Edit selected item'), self._edit_selected)
		group.add_method('copy_files', _('Copy selected items'), self._copy_files)
		group.add_method('move_files', _('Move selected items'), self._move_files)
		group.add_method('show_popup_menu', _('Show context menu'), self._show_popup_menu)
		group.add_method('show_open_with_menu', _('Show "open with" menu'), self._show_open_with_menu)
		group.add_method('inherit_left_path', _('Assign path from left list'), self._inherit_left_path)
		group.add_method('inherit_right_path', _('Assign path from right list'), self._inherit_right_path)
		group.add_method('swap_paths', _('Swap right and left paths'), self._swap_paths)
		group.add_method('move_marker_up', _('Move selection marker up'), self._move_marker_up)
		group.add_method('move_marker_down', _('Move selection marker down'), self._move_marker_down)
		group.add_method('show_tab_menu', _('Show tab menu'), self._show_tab_menu)
		group.add_method('copy_path_to_clipboard', _('Copy path to clipboard'), self.copy_path_to_clipboard)
		group.add_method('copy_selected_path_to_clipboard', _('Copy selected path to clipboard'), self.copy_selected_path_to_clipboard)
		group.add_method('copy_path_to_command_entry', _('Copy path to command entry'), self.copy_path_to_command_entry)
		group.add_method('copy_selection_to_command_entry', _('Copy selection to command entry'), self.copy_selection_to_command_entry)
		group.add_method('custom_path_entry', _('Ask and navigate to path'), self.custom_path_entry)
		group.add_method('start_quick_search', _('Start quick search'), self._handle_start_search)
		group.add_method('expand_directory', _('Expand directory'), self._expand_directory)
		group.add_method('collapse_directory', _('Collapse directory'), self._collapse_directory)
		group.add_method('create_link', _('Create symbolic or hard link'), self._create_link)
		group.add_method('show_emblem_menu', _('Show emblem menu'), self._show_emblem_menu)

		# configure accelerators
		group.set_accelerator('execute_item', keyval('Return'), 0)
		group.set_alt_accelerator('execute_item', keyval('KP_Enter'), 0)
		group.set_accelerator('item_properties', keyval('Return'), gtk.gdk.MOD1_MASK)
		group.set_alt_accelerator('item_properties', keyval('KP_Enter'), gtk.gdk.MOD1_MASK)
		group.set_accelerator('add_bookmark', keyval('d'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('edit_bookmarks', keyval('b'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('cut_to_clipboard', keyval('x'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('copy_to_clipboard', keyval('c'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('paste_from_clipboard', keyval('v'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('open_in_new_tab', keyval('t'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('create_terminal', keyval('z'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('parent_directory', keyval('BackSpace'), 0)
		group.set_accelerator('root_directory', keyval('backslash'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('refresh_list', keyval('R'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('show_history', keyval('BackSpace'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('back_in_history', keyval('Left'), gtk.gdk.MOD1_MASK)
		group.set_accelerator('forward_in_history', keyval('Right'), gtk.gdk.MOD1_MASK)
		group.set_accelerator('select_all', keyval('A'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('deselect_all', keyval('A'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('invert_selection', keyval('asterisk'), gtk.gdk.SHIFT_MASK)
		group.set_alt_accelerator('invert_selection', keyval('KP_Multiply'), 0)
		group.set_accelerator('toggle_selection', keyval('Insert'), 0)
		group.set_alt_accelerator('toggle_selection', keyval('Down'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('toggle_selection_up', keyval('Up'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('delete_files', keyval('Delete'), 0)
		group.set_accelerator('force_delete_files', keyval('Delete'), gtk.gdk.SHIFT_MASK)
		group.set_alt_accelerator('delete_files', keyval('F8'), 0)
		group.set_accelerator('show_left_bookmarks', keyval('F1'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('show_right_bookmarks', keyval('F2'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('rename_file', keyval('F2'), 0)
		group.set_alt_accelerator('rename_file', keyval('F6'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('view_selected', keyval('F3'), 0)
		group.set_accelerator('edit_selected', keyval('F4'), 0)
		group.set_accelerator('copy_files', keyval('F5'), 0)
		group.set_accelerator('move_files', keyval('F6'), 0)
		group.set_accelerator('show_popup_menu', keyval('Menu'), 0)
		group.set_alt_accelerator('show_popup_menu', keyval('F10'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('show_open_with_menu', keyval('Menu'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('inherit_left_path', keyval('Right'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('inherit_right_path', keyval('Left'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('swap_paths', keyval('U'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('show_tab_menu', keyval('grave'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('copy_path_to_clipboard', keyval('l'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('copy_selected_path_to_clipboard', keyval('c'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('copy_path_to_command_entry', keyval('Return'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_alt_accelerator('copy_path_to_command_entry', keyval('KP_Enter'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('copy_selection_to_command_entry', keyval('Return'), gtk.gdk.CONTROL_MASK)
		group.set_alt_accelerator('copy_selection_to_command_entry', keyval('KP_Enter'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('custom_path_entry', keyval('l'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('start_quick_search', keyval('f'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('expand_directory', keyval('Right'), 0)
		group.set_accelerator('collapse_directory', keyval('Left'), 0)
		group.set_accelerator('create_link', keyval('F7'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('show_emblem_menu', keyval('e'), gtk.gdk.CONTROL_MASK)

		# create bookmark accelerators
		group.add_method('bookmark_home', _("Go to '{0}'"), self._parent.activate_bookmark, 0)
		group.set_accelerator('bookmark_home', keyval('grave'), gtk.gdk.MOD1_MASK)

		for number in range(1, 11):
			group.add_method(
						'bookmark_{0}'.format(number),
						_("Go to '{0}'"),
						self._parent.activate_bookmark,
						number
					)

			key_number = number if number < 10 else 0
			group.set_accelerator(
						'bookmark_{0}'.format(number),
						keyval(str(key_number)),
						gtk.gdk.MOD1_MASK
					)

		# add accelerator group to the list
		self._accelerator_groups.append(group)

	def _show_bookmarks(self, widget=None, data=None):
		"""Show bookmarks for current panel"""
		self._parent.show_bookmarks_menu(None, self._notebook)
		return True

	def _show_left_bookmarks(self, widget, data=None):
		"""Show left bookmarks menu"""
		self._parent.show_bookmarks_menu(None, self._parent.left_notebook)
		return True

	def _show_right_bookmarks(self, widget, data=None):
		"""Show right bookmarks menu"""
		self._parent.show_bookmarks_menu(None, self._parent.right_notebook)
		return True

	def _show_history_window(self, widget, data=None):
		"""Show history browser"""
		HistoryList(self, self._parent)
		return True

	def _history_go_back(self, widget=None, data=None):
		"""Go back in history by one entry"""
		if self.history_manager is not None:
			self.history_manager.back()
		return True

	def _history_go_forward(self, widget=None, data=None):
		"""Go forward in history by one entry"""
		if self.history_manager is not None:
			self.history_manager.forward()
		return True

	def _show_tab_menu(self, widget, data=None):
		"""Show title bar menu"""
		self._title_bar.show_menu()
		return True

	def _show_emblem_menu(self, widget, data=None):
		"""Show quick emblem selection menu."""
		if data is not None:
			# if this method is called by accelerator data is actually keyval
			self._emblem_menu.popup(None, None, self._get_popup_menu_position, 1, 0)

		else:
			# if called by mouse, we don't have the need to position the menu manually
			self._emblem_menu.popup(None, None, None, 1, 0)

		return True

	def _reorder_columns(self, order=None):
		"""Apply column order and visibility"""
		options = self._parent.plugin_options

		# order was not specified, try to restore from config
		order = order or options.section(self._name).get('columns')

		# if we still didn't manage to get order, return
		if order is None:
			return

		columns = self._item_list.get_columns()
		names = [column.get_data('name') for column in columns]

		# make sure order contains only valid names
		order = filter(lambda name: name in names, order[:])

		# block signal handler from messing up the config
		self._item_list.handler_block_by_func(self._column_changed)

		# show columns in specified order
		base_index = names.index(order[0])
		for column_name in order[1:]:
			# get column index
			index = names.index(column_name)

			# get column objects
			column = columns[index]
			base_column = columns[base_index]

			# move specified column
			self._item_list.move_column_after(column, base_column)

			# update base index
			base_index = index

		# set column visibility
		for column in columns:
			visible = column.get_data('name') in order
			column.set_visible(visible)

		# unblock signal handler
		self._item_list.handler_unblock_by_func(self._column_changed)

	def _create_default_column_sizes(self):
		"""Create default column sizes section in main configuration file"""
		options = self._parent.plugin_options
		section = options.create_section(self._name)

		# store default column sizes
		for index, column in enumerate(self._columns):
			name = 'size_{0}'.format(column.get_data('name'))
			size = self._columns_size[index]

			if not section.has(name):
				section.set(name, size)

	def _move_marker_up(self, widget, data=None):
		"""Move marker up"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# get current path
			path = item_list.get_path(selected_iter)[0]
			previous_iter = path - 1

			# if selected item is not first, move selection
			if previous_iter >= 0:
				self._item_list.set_cursor(previous_iter)

		return True

	def _move_marker_down(self, widget, data=None):
		"""Move marker down"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# get current path
			path = item_list.get_path(selected_iter)[0]
			next_iter = path + 1

			# if selected item is not last, move selection
			if next_iter < len(item_list):
				self._item_list.set_cursor(next_iter)

		return True

	def _handle_button_press(self, widget, event):
		"""Handles mouse events"""
		result = False

		right_click_select = self._parent.options.section('item_list').get('right_click_select')
		single_click_navigation = self._parent.options.section('item_list').get('single_click_navigation')

		shift_active = event.state & gtk.gdk.SHIFT_MASK
		control_active = event.state & gtk.gdk.CONTROL_MASK

		# handle single click
		if event.button is 1 and control_active and event.type in (gtk.gdk.BUTTON_PRESS, gtk.gdk.BUTTON_RELEASE):
			# we handle left mouse press and release in order to prevent
			# default widget behavior which leads to unpredictable results

			if event.type is gtk.gdk.BUTTON_PRESS:
				# focus clicked item on button press
				item = self._item_list.get_path_at_pos(int(event.x), int(event.y))

				if item is not None:
					path = item[0]
					self._item_list.set_cursor(path)
					self._item_list.scroll_to_cell(path)

			else:
				# toggle selection on button release
				self._toggle_selection(widget, event, advance=False)

			result = True

		# handle range select
		elif event.button is 1 and shift_active and event.type is gtk.gdk.BUTTON_PRESS:
			start_path = None
			end_path = None

			# get source path
			selection = self._item_list.get_selection()
			item_list, start_iter = selection.get_selected()

			if start_iter is not None:
				start_path = item_list.get_path(start_iter)

			# get destination path
			item = self._item_list.get_path_at_pos(int(event.x), int(event.y))

			if item is not None:
				end_path = item[0]

			# select items in between
			if start_path and end_path:
				self._select_range(start_path, end_path)

				# select end item
				self._item_list.set_cursor(end_path)
				self._item_list.scroll_to_cell(end_path)

			result = True

		# handle navigation with double or single click
		elif event.button is 1 and not (shift_active or control_active) \
		and ((event.type is gtk.gdk._2BUTTON_PRESS and not single_click_navigation) \
		or (event.type is gtk.gdk.BUTTON_RELEASE and single_click_navigation)):

			# make sure that clicking on empty space doesn't trigger any action
			if self._item_list.get_path_at_pos(int(event.x), int(event.y)) is not None:
				self._execute_selected_item(widget)
				result = True

		# handle middle click
		elif event.button is 2 and event.type is gtk.gdk.BUTTON_RELEASE:
			self._open_in_new_tab()
			result = True

		# handle right click
		elif event.button is 3:
			if event.type is gtk.gdk.BUTTON_PRESS:
				# record mouse down timestamp
				self._popup_timestamp = event.get_time()

				# prevent CTRL+RightClick from generating exceptions
				if control_active:
					result = True

			elif event.type is gtk.gdk.BUTTON_RELEASE:
				# button was released, depending on options call specific method
				time_valid = event.get_time() - self._popup_timestamp > 500
				if event.x and event.y:
					if not right_click_select or (right_click_select and time_valid):
						# show popup menu
						self._show_popup_menu(widget)

					else:
						# toggle item mark
						self._toggle_selection(widget, advance=False)

				result = True

		# handle back button on mouse
		elif event.button is 8:
			if event.type is gtk.gdk.BUTTON_RELEASE:
				self.history_manager.back()

			result = True

		# handle forward button on mouse
		elif event.button is 9:
			if event.type is gtk.gdk.BUTTON_RELEASE:
				self.history_manager.forward()

			result = True

		return result

	def _handle_key_press(self, widget, event):
		"""Handles key events in item list"""
		result = PluginBase._handle_key_press(self, widget, event)

		if not result:
			# retrieve human readable key representation
			key_value = gtk.gdk.keyval_to_unicode(event.keyval)

			if not result and key_value > 0:
				# generate state sting based on modifier state (control, alt, shift)
				state = "%d%d%d" % (
							bool(event.state & gtk.gdk.CONTROL_MASK),
							bool(event.state & gtk.gdk.MOD1_MASK),
							bool(event.state & gtk.gdk.SHIFT_MASK)
						)

				if state == self._parent.options.section('item_list').get('search_modifier'):
					# start quick search if modifier combination is right
					self._start_search(unichr(key_value))
					result = True

				else:
					# otherwise focus command entry
					self._focus_command_line(unichr(key_value))
					result = True

		return result

	def _handle_tab_close(self):
		"""Clean up before tab close"""
		PluginBase._handle_tab_close(self)
		self._main_object.handler_block_by_func(self._column_changed)

		# save current configuration
		self._options.set('path', self.path)
		self._options.set('sort_column', self._sort_column)
		self._options.set('sort_ascending', self._sort_ascending)

		# allow providers to clean up
		self.destroy_providers()

		return True

	def _handle_search_key_press(self, widget, event):
		"""Handle return and escape keys for quick search"""
		result = False

		if event.keyval == gtk.keysyms.Return:
			self._stop_search(widget)
			self._execute_selected_item(widget)
			result = True

		elif event.keyval == gtk.keysyms.Escape:
			self._stop_search(widget)
			result = True

		return result

	def _handle_start_search(self, widget, event):
		"""Handle pressing key combination for start search"""
		self._start_search()
		return True

	def _handle_history_click(self, widget=None, data=None, path=None):
		"""Handle clicks on bookmark menu"""
		if path is None:
			path = widget.get_data('path')

		if self.get_provider().is_dir(path):
			# path is valid
			self.change_path(path)

		else:
			# invalid path, notify user
			dialog = gtk.MessageDialog(
									self,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_OK,
									_(
										'Directory does not exist anymore or is not '
										'valid. If path is not local check if specified '
										'volume is mounted.'
									) +	'\n\n{0}'.format(path)
								)
			dialog.run()
			dialog.destroy()

	def _handle_external_data(self, operation, protocol, item_list, destination):
		"""Handle data coming from a different application"""
		result = False
		dialog_classes = {
					'copy': CopyDialog,
					'cut': MoveDialog,
					'move': MoveDialog
				}
		operation_classes = {
					'copy': CopyOperation,
					'cut': MoveOperation,
					'move': MoveOperation
				}

		# make sure operation is valid
		assert operation in dialog_classes.keys()

		# get classes
		Provider = self._parent.get_provider_by_protocol(protocol)
		Dialog = dialog_classes[operation]
		Operation = operation_classes[operation]

		if Provider is None:
			# no provider was found for specified protocol
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_OK,
									_(
										'Specified protocol ({0}) is not supported by '
										'this application. Please check for available plugins '
										'or create a feature request.'
									).format(protocol)
								)
			dialog.run()
			dialog.destroy()

			# abort handling data
			return result

		# handle data
		path = os.path.dirname(item_list[0])
		selection = [urllib.unquote(os.path.basename(item)) for item in item_list]

		# local provider is unable to handle URIs
		if protocol == 'file' and '://' in path:
			path = path.split('://', 1)[1]

		# create provider
		source_provider = Provider(self, path, selection)
		destination_provider = self.get_provider()

		# check if we actually have data to handle
		if len(source_provider.get_selection()) == 0:
			# no provider was found for specified protocol
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_OK,
									_(
										'Application is unable to handle specified data. '
										'Check if source items still exist.'
									)
								)
			dialog.run()
			dialog.destroy()

			# abort handling data
			return result

		# show operation dialog
		dialog = Dialog(
					self._parent,
					source_provider,
					destination_provider,
					destination
				)
		dialog_result = dialog.get_response()

		# check user response
		if dialog_result[0] == gtk.RESPONSE_OK:
			# user confirmed copying
			operation = Operation(
								self._parent,
								source_provider,
								destination_provider,
								dialog_result[1],
								destination# options from dialog
							)

			# set event queue
			event_queue = self.get_monitor_queue()
			if event_queue is not None:
				operation.set_destination_queue(event_queue)

			# set operation queue
			operation.set_operation_queue(dialog_result[2])

			# start the operation
			operation.set_selection(selection)
			operation.start()

			result = True

		return result

	def _handle_cursor_change(self, widget=None, data=None):
		"""Handle cursor change"""
		pass

	def _start_search(self, key=None):
		"""Shows quick search panel and starts searching"""
		self._search_panel.show()
		self._search_entry.grab_focus()

		if key is not None:
			self._search_entry.set_text(key)
			self._search_entry.set_position(len(key))

	def _stop_search(self, widget=None, data=None):
		"""Hide quick search panel and return focus to item list"""
		self._search_panel.hide()

		if widget is not None:
			self._item_list.grab_focus()

		return False

	def _execute_selected_item(self, widget=None, data=None):
		"""Execute selected item"""
		return True

	def _execute_with_application(self, widget=None, data=None):
		"""Show application selection dialog and then execute item"""
		return True

	def _open_in_new_tab(self, widget=None, data=None):
		"""Open selected directory in new tab"""
		return True

	def _open_directory(self, widget=None, data=None):
		"""Open selected directory"""
		return True

	def _expand_directory(self, widget=None, data=None):
		"""Expand currently selected directory"""
		return True

	def _collapse_directory(self, widget=None, data=None):
		"""Collapse currently selected directory"""
		return True

	def _create_directory(self, widget=None, data=None):
		"""Create directory"""
		return True

	def _create_file(self, widget=None, data=None):
		"""Create file"""
		return True

	def _create_link(self, widget=None, data=None, original_path=None, hard_link=None):
		"""Create symbolic or hard link"""
		return True

	def _delete_files(self, widget=None, force_delete=None):
		"""Delete files"""
		return True

	def _copy_files(self, widget=None, data=None):
		"""Start a copy files operation"""
		return True

	def _move_files(self, widget=None, data=None):
		"""Start a move files operation"""
		return True

	def _rename_file(self, widget=None, data=None):
		"""Rename highlighed item"""
		return True

	def _send_to(self, widget=None, data=None):
		"""Send To Nautilus integration"""
		pass

	def _cut_files_to_clipboard(self, widget=None, data=None):
		"""Cut selected files to clipboard"""
		self._copy_files_to_clipboard(operation='cut')
		return True

	def _copy_files_to_clipboard(self, widget=None, data=None, operation='copy'):
		"""Copy selected files to clipboard"""
		selected_items = self._get_selection_list(relative=False)

		# make sure list actually contains something
		if selected_items is not None:
			provider = self.get_provider()
			protocol = provider.get_protocol()

			# modify list to form URI
			selected_items = ['{0}://{1}'.format(protocol, urllib.quote(item)) for item in selected_items]

			# set clipboard data
			self._parent.set_clipboard_item_list(operation, selected_items)

		return True

	def _paste_files_from_clipboard(self, widget=None, data=None):
		"""Paste files from clipboard"""
		data = self._parent.get_clipboard_item_list()

		# clipboard data contains URI list
		if data is not None:
			operation = data[0]
			list_ = data[1]
			protocol = list_[0].split('://')[0]

			# convert URI to normal path
			list_ = [urllib.unquote(item.split('://')[1]) for item in list_]

			# call handler
			self._handle_external_data(operation, protocol, list_, self.path)

		return True

	def _item_properties(self, widget=None, data=None):
		"""Abstract method that shows file/directory properties"""
		return True

	def _get_selection(self, relative=False):
		"""Return item with path under cursor"""
		pass

	def _get_selection_list(self, under_cursor=False, relative=False):
		"""Return list of selected items

		This list is used by many other methods inside this program,
		including 'open with' handlers, execute_selected file, etc.

		"""
		pass

	def _get_popup_menu_position(self, menu, data=None):
		"""Abstract method for positioning menu properly on given row"""
		return 0, 0, True

	def _get_history_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return pos_x, pos_y, True

	def _get_other_provider(self):
		"""Return provider from opposite list.

		If opposite tab is not ItemList or does not have a provider
		return None.

		"""
		notebook = self._parent.left_notebook \
								if self._notebook is self._parent.right_notebook \
								else self._parent.right_notebook

		current_object = notebook.get_nth_page(notebook.get_current_page())

		if hasattr(current_object, "get_provider"):
			result = current_object.get_provider()
		else:
			result = None

		return result

	def _create_popup_menu(self):
		"""Create popup menu and its constant elements"""
		result = gtk.Menu()
		menu_manager = self._parent.menu_manager

		# construct menu
		item = menu_manager.create_menu_item({
								'label': _('_Open'),
								'type': 'image',
								'stock': gtk.STOCK_OPEN,
								'callback': self._execute_selected_item,
							})
		result.append(item)

		# open directory in new tab
		item = menu_manager.create_menu_item({
								'label': _('Open in new ta_b'),
								'type': 'image',
								'image': 'tab-new',
								'callback': self._open_in_new_tab,
							})
		result.append(item)
		self._open_new_tab_item = item

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# dynamic menu
		item = menu_manager.create_menu_item({
								'label': _('Open _with'),
								'type': 'image',
								'stock': gtk.STOCK_EXECUTE,
							})
		result.append(item)

		self._open_with_item = item
		self._open_with_menu = gtk.Menu()
		item.set_submenu(self._open_with_menu)

		# additional options menu
		item = menu_manager.create_menu_item({
								'label': _('Additional options'),
							})
		result.append(item)

		self._additional_options_item = item
		self._additional_options_menu = gtk.Menu()
		item.set_submenu(self._additional_options_menu)

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# create new file
		item = menu_manager.create_menu_item({
								'label': _('Create file'),
								'type': 'image',
								'stock': gtk.STOCK_NEW,
								'callback': self._parent._command_create,
								'data': 'file'
							})
		result.append(item)

		# create new directory
		item = menu_manager.create_menu_item({
								'label': _('Create directory'),
								'type': 'image',
								'image': 'folder-new',
								'callback': self._parent._command_create,
								'data': 'directory',
							})
		result.append(item)

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# cut/copy/paste
		item = menu_manager.create_menu_item({
								'label': _('Cu_t'),
								'type': 'image',
								'stock': gtk.STOCK_CUT,
								'callback': self._cut_files_to_clipboard,
							})
		result.append(item)
		self._cut_item = item

		item = menu_manager.create_menu_item({
								'label': _('_Copy'),
								'type': 'image',
								'stock': gtk.STOCK_COPY,
								'callback': self._copy_files_to_clipboard,
							})
		result.append(item)
		self._copy_item = item

		item = menu_manager.create_menu_item({
								'label': _('_Paste'),
								'type': 'image',
								'stock': gtk.STOCK_PASTE,
								'callback': self._paste_files_from_clipboard,
							})
		result.append(item)
		self._paste_item = item

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# create move and copy to other pane items
		item = menu_manager.create_menu_item({
								'label': _('Copy to other...'),
								'callback': self._copy_files
							})
		result.append(item)

		item = menu_manager.create_menu_item({
								'label': _('Move to other...'),
								'callback': self._move_files
							})
		result.append(item)

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# delete
		item = menu_manager.create_menu_item({
								'label': _('_Delete'),
								'type': 'image',
								'stock': gtk.STOCK_DELETE,
								'callback': self._delete_files,
							})
		result.append(item)
		self._delete_item = item

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# send to
		item = menu_manager.create_menu_item({
								'label': _('Send to...'),
								'callback': self._send_to,
								'type': 'image',
								'image': 'document-send',
								'visible': self._parent.NAUTILUS_SEND_TO_INSTALLED,
							})
		result.append(item)
		self._send_to_item = item

		# link/rename
		item = menu_manager.create_menu_item({
								'label': _('Ma_ke link'),
								'callback': self._create_link
							})
		result.append(item)

		item = menu_manager.create_menu_item({
								'label': _('_Rename...'),
								'callback': self._rename_file,
							})
		result.append(item)
		item.set_sensitive(False)
		self._rename_item = item

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# properties
		item = menu_manager.create_menu_item({
								'label': _('_Properties'),
								'type': 'image',
								'stock': gtk.STOCK_PROPERTIES,
								'callback': self._item_properties
							})
		result.append(item)
		self._properties_item = item

		return result

	def _prepare_popup_menu(self):
		"""Prepare popup menu contents"""
		# remove existing items
		for item in self._open_with_menu.get_children():
			self._open_with_menu.remove(item)

		# remove items from additional options menu
		for item in self._additional_options_menu.get_children():
			self._additional_options_menu.remove(item)

	def _prepare_history_menu(self):
		"""Prepare history menu contents"""
		# remove existing items
		for item in self._history_menu.get_children():
			self._history_menu.remove(item)

		# get menu data
		item_count = 10
		item_list = self.history[1:item_count]

		if len(item_list) > 0:
			# create items
			for item in item_list:
				menu_item = gtk.MenuItem(item)
				menu_item.set_data('path', item)
				menu_item.connect('activate', self._handle_history_click)

				self._history_menu.append(menu_item)

			# add entry to show complete history
			separator = gtk.SeparatorMenuItem()
			self._history_menu.append(separator)

			image = gtk.Image()
			image.set_from_icon_name('document-open-recent', gtk.ICON_SIZE_MENU)

			menu_item = gtk.ImageMenuItem()
			menu_item.set_image(image)
			menu_item.set_label(_('View complete history...'))
			menu_item.connect('activate', self._show_history_window)
			self._history_menu.append(menu_item)

		else:
			# no items to create, make blank item
			menu_item = gtk.MenuItem(_('History is empty'))
			menu_item.set_sensitive(False)

			self._history_menu.append(menu_item)

		# show all menu items
		self._history_menu.show_all()

	def _prepare_emblem_menu(self):
		"""Prepare emblem menu."""
		pass

	def _show_open_with_menu(self, widget, data=None):
		"""Show 'open with' menu"""
		# prepare elements in popup menu
		self._prepare_popup_menu()

		# if this method is called by Menu key data is actually event object
		self._open_with_menu.popup(
								None, None,
								self._get_popup_menu_position,
								1, 0
							)

	def _show_popup_menu(self, widget=None, data=None):
		"""Show item menu"""
		# prepare elements in popup menu
		self._prepare_popup_menu()

		if data is not None:
			# if this method is called by accelerator data is actually keyval
			self._popup_menu.popup(None, None, self._get_popup_menu_position, 1, 0)

		else:
			# if called by mouse, we don't have the need to position the menu manually
			self._popup_menu.popup(None, None, None, 1, 0)

		return True

	def _parent_directory(self, widget=None, data=None):
		"""Move to parent folder"""
		if self._search_panel.get_visible():
			return False  # prevent going to parent directory if quick search is active

		self.change_path(
						os.path.dirname(self.path),
						os.path.basename(self.path)
					)

		return True  # to prevent command or quick search in single key bindings

	def _root_directory(self, widget=None, data=None):
		"""Navigate to root directory"""
		self.change_path(
						os.path.sep,
						os.path.basename(self.path)
					)

		return True

	def _focus_command_line(self, key):
		"""Focus command-line control"""
		if self._parent.options.get('show_command_entry'):
			self._parent.command_edit.grab_focus()
			self._parent.command_edit.set_text(key)
			self._parent.command_edit.set_position(len(key))

		return True

	def _control_got_focus(self, widget, data=None):
		"""List focus in event"""
		PluginBase._control_got_focus(self, widget, data)
		self._parent.set_location_label(self.path)

	def _bookmarks_button_clicked(self, widget, data=None):
		"""Bookmarks button click event"""
		self._parent.show_bookmarks_menu(widget, self._notebook)

	def _history_button_clicked(self, widget, data=None):
		"""History button click event"""
		# prepare menu for drawing
		self._prepare_history_menu()

		# show the menu on calculated location
		self._history_menu.popup(
								None, None,
								self._get_history_menu_position,
								1, 0, widget
							)

	def _duplicate_tab(self, widget, data=None):
		"""Creates new tab with same path"""
		PluginBase._duplicate_tab(self, None, self.path)
		return True

	def _create_terminal(self, widget, data=None):
		"""Create terminal tab in parent notebook"""
		options = Parameters()
		options.set('path', self.path)

		self._parent.create_terminal_tab(self._notebook, options)
		return True

	def _set_sort_function(self, widget, data=None):
		"""Abstract method used for setting sort function"""
		pass

	def _column_resized(self, widget, data=None):
		"""Resize all columns accordingly"""
		column_width = widget.get_width()
		column_name = widget.get_data('name')
		option_name = 'size_{0}'.format(column_name)

		# get stored column width
		if self._parent.plugin_options.section(self._name).has(option_name):
			existing_width = self._parent.plugin_options.section(self._name).get(option_name)

		else:
			existing_width = -1

		# if current width is not the same as stored one, save
		if not column_width == existing_width:
			self._parent.plugin_options.section(self._name).set(option_name, column_width)
			self._parent.delegate_to_objects(self, 'update_column_size', column_name)

	def _column_changed(self, widget, data=None):
		"""Handle adding, removing and reordering columns"""
		columns = filter(lambda column: column.get_visible(), self._item_list.get_columns())
		column_names = map(lambda column: column.get_data('name'), columns)

		# apply column change to other objects
		self._parent.delegate_to_objects(self, '_reorder_columns', column_names)

		# save column order
		self._parent.plugin_options.section(self._name).set('columns', column_names)

	def _resize_columns(self, columns):
		"""Resize columns according to global options"""
		for column in columns:
			option_name = 'size_{0}'.format(column.get_data('name'))
			width = self._parent.plugin_options.section(self._name).get(option_name)

			if width is not None:
				column.set_fixed_width(width)

	def _sort_list(self, ascending=True):
		"""Abstract method for manual list sorting"""
		pass

	def _clear_list(self):
		"""Abstract method for clearing item list"""
		pass

	def _update_status_with_statistis(self):
		"""Set status bar text according to dir/file stats"""
		# format size
		total_text = common.format_size(self._size['total'], self._size_format)
		selected_text = common.format_size(self._size['selected'], self._size_format)

		self._status_bar.set_text(
							'{0}/{1}'.format(
								self._dirs['selected'],
								self._dirs['count']
							),
							'dirs')

		self._status_bar.set_text(
							'{0}/{1}'.format(
								self._files['selected'],
								self._files['count']
							),
							'files')

		self._status_bar.set_text(
							'{0}/{1}'.format(
								selected_text,
								total_text
							),
							'size')

	def _select_all(self, widget, data=None):
		"""Abstract proxy method for selecting all items"""
		pass

	def _deselect_all(self, widget, data=None):
		"""Abstract proxy method for deselecting all items"""
		pass

	def _toggle_selection(self, widget, data=None, advance=True):
		"""Abstract method for toggling item selection"""
		if self._parent.options.get('show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

		return True

	def _toggle_selection_up(self, widget, data=None):
		"""Toggle selection and move cursor up"""
		self._toggle_selection(widget, data, advance=False)
		self._move_marker_up(widget, data)

		return True

	def _toggle_selection_from_cursor_up(self, widget, data=None):
		"""Toggle selection from cursor to the end of the list"""
		return True

	def _toggle_selection_from_cursor_down(self, widget, data=None):
		"""Toggle selection from cursor to the end of the list"""
		return True

	def _select_range(self, start_path, end_path):
		"""Set items in range to status opposite from frist item in selection"""
		if self._parent.options.get('show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def _view_selected(self, widget=None, data=None):
		"""View currently selected item"""
		selection = self._get_selection()

		if selection is not None:
			Viewer(selection, self.get_provider(), self)

		return True

	def _edit_selected(self, widget=None, data=None):
		"""Abstract method to edit currently selected item"""
		pass

	def _inherit_left_path(self, widget, data=None):
		"""Inherit path in right list from left"""
		opposite_object = self._parent.get_opposite_object(self)

		if self._notebook is self._parent.left_notebook:
			if hasattr(opposite_object, 'change_path'):
				opposite_object.change_path(self.path)

			elif hasattr(opposite_object, 'feed_terminal'):
				opposite_object.feed_terminal(self.path)

		else:
			self.change_path(opposite_object.path)

		return True

	def _inherit_right_path(self, widget, data=None):
		"""Inherit path in left list from right"""
		opposite_object = self._parent.get_opposite_object(self)

		if self._notebook is self._parent.right_notebook:
			if hasattr(opposite_object, 'change_path'):
				opposite_object.change_path(self.path)

			elif hasattr(opposite_object, 'feed_terminal'):
				opposite_object.feed_terminal(self.path)

		else:
			self.change_path(opposite_object.path)

		return True

	def _swap_paths(self, widget, data=None):
		"""Swap left and right paths"""
		opposite_object = self._parent.get_opposite_object(self)

		if hasattr(opposite_object, 'change_path'):
			# get path from opposite object
			new_path = opposite_object.path

			# change paths
			opposite_object.change_path(self.path)
			self.change_path(new_path)

		return True

	def _add_bookmark(self, widget, data=None):
		"""Show dialog for adding current path to bookmarks"""
		self._parent._add_bookmark(widget, self)
		return True

	def _edit_bookmarks(self, widget, data=None):
		"""Open preferences window with bookmarks tab selected"""
		self._parent.preferences_window._show(widget, 'bookmarks')
		return True

	def _directory_changed(self, event, path, other_path, parent=None):
		"""Handle signal emitted by monitor"""
		pass

	def change_path(self, path=None, selected=None):
		"""Public method for safe path change """
		real_path = os.path.expanduser(path)

		# record change in history
		if self.history_manager is not None:
			self.history_manager.record(real_path)

		# hide quick search
		self._stop_search()

		# update status bar visibility
		if self._parent.options.get('show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def select_all(self, pattern=None, exclude_list=None):
		"""Select all items matching pattern"""
		if self._parent.options.get('show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def deselect_all(self, pattern=None):
		"""Deselect items matching the pattern"""
		if self._parent.options.get('show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def invert_selection(self, pattern=None):
		"""Invert selection on matching items"""
		if self._parent.options.get('show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def refresh_file_list(self, widget=None, data=None):
		"""Reload file list for current directory"""
		self.change_path(self.path)
		return True

	def copy_path_to_clipboard(self, widget=None, data=None):
		"""Copy current path to clipboard"""
		self._parent.set_clipboard_text(self.path)
		return True

	def copy_selected_path_to_clipboard(self, widget=None, data=None):
		"""Copy paths of selected items to clipboard"""
		selection = self._get_selection_list(relative=False)
		self._parent.set_clipboard_text('\n'.join(selection))
		return True

	def copy_path_to_command_entry(self, widget=None, data=None):
		"""Copy current path to command entry and focus it"""
		self._parent.set_command_entry_text(self.path, True)

	def copy_selection_to_command_entry(self, widget=None, data=None):
		"""Copy current selection to command entry and focus it"""
		selection = self._get_selection(relative=True)
		self._parent.set_command_entry_text(selection, True)

	def custom_path_entry(self, widget=None, data=None):
		"""Ask user to enter path"""
		path = self.path

		# create dialog
		dialog = PathInputDialog(self._parent)
		dialog.set_title(_('Path entry'))
		dialog.set_label(_('Navigate to:'))
		dialog.set_text(path)

		# get user response
		response = dialog.get_response()

		# try to navigate to specified path
		if response[0] == gtk.RESPONSE_OK:
			self.change_path(os.path.expanduser(response[1]))

		return True

	def update_column_size(self, name):
		"""Update column sizes"""
		pass

	def update_column_order(self, column, after):
		"""Update column order"""
		pass

	def update_column_visibility(self, column):
		"""Update column visibility"""
		pass

	def create_provider(self, path, is_archive):
		"""Preemptively create provider object."""
		result = None

		if not is_archive:
			scheme = 'file' if '://' not in path else path.split('://', 1)[0]

			# create provider
			Provider = self._parent.get_provider_by_protocol(scheme)

			if Provider is not None:
				result = Provider(self)

				# cache provider for later use
				root_path = result.get_root_path(path)
				self._providers[root_path] = result

		else:
			mime_type = self._parent.associations_manager.get_mime_type(path=path)
			current_provider = self.get_provider()

			# create archive provider
			Provider = self._parent.get_provider_for_archive(mime_type)

			if Provider is not None:
				result = Provider(self, path)

				# set archive file handle
				handle = current_provider.get_file_handle(path, FileMode.READ_APPEND)
				result.set_archive_handle(handle)

				# cache provider locally
				self._providers[path] = result

		# in case no of not supported provider, create one for users home
		if result is None:
			Provider = self._parent.get_provider_by_protocol('file')
			result = Provider(self, user.home)

			# cache provider for later use
			root_path = result.get_root_path(user.home)
			self._providers[root_path] = result

		return result

	def destroy_providers(self):
		"""Allow providers to clean up after themselves."""
		for path, provider in self._providers.items():
			provider.release_archive_handle()

	def get_provider(self, path=None):
		"""Get existing list provider or create new for specified path."""
		result = None

		# if path is not specified return current provider
		if path is None:
			return self._current_provider

		# check if there is a provider for specified path
		if path in self._providers:
			result = self._providers[path]

		else:
			# try to find provider with longest matching path
			longest_path = 0
			matching_provider = None

			for provider_path, provider in self._providers.items():
				# make sure path is valid, normally this shouldn't happen
				if provider_path is None:
					continue

				if path.startswith(provider_path) and len(provider_path) > longest_path:
					# matched provider for path, store it for later
					longest_path = len(provider_path)
					matching_provider = provider

				elif not path.startswith(provider_path):
					# provider is no longer needed as path is not contained
					provider.release_archive_handle()
					del self._providers[provider_path]

			result = matching_provider

		# no matching provider was found, create new
		if result is None:
			result = self.create_provider(path, False)

		# cache current provider
		self._current_provider = result

		return result

	def provider_exists(self, path):
		"""Check if provider for specified path exists."""
		return path in self._providers

	def get_monitor(self):
		"""Get file system monitor"""
		return self._monitor_list[0] if len(self._monitor_list) > 0 else None

	def get_monitor_queue(self):
		"""Get queue for monitors in list"""
		result = None

		if len(self._monitor_list) > 0:
			monitor = self._monitor_list[0]

			if monitor.is_manual():
				result = monitor.get_queue()

		return result

	def monitor_path(self, path, parent=None):
		"""Create new monitor for specified path"""
		if len(self._monitor_list) > 0 and self._monitor_list[0].is_manual():
			return

		if path not in [monitor.get_path() for monitor in self._monitor_list]:
			# create new monitor for specified path
			provider = self.get_provider()
			monitor = provider.get_monitor(path)
			monitor.connect('changed', self._directory_changed, parent)

			# add monitor to the list
			self._monitor_list.append(monitor)

	def cancel_monitors(self):
		"""Cancel all monitors"""
		for monitor in self._monitor_list:
			monitor.cancel()

		self._monitor_list[:] = []

	def apply_settings(self):
		"""Apply settings"""
		options = self._parent.options
		section = options.section('item_list')

		# let parent class do its work
		PluginBase.apply_settings(self)

		# update status
		self._update_status_with_statistis()

		# change headers visibility
		headers_visible = section.get('headers_visible')
		self._item_list.set_headers_visible(headers_visible)

		# apply scrollbar visibility
		hide_scrollbar = section.get('hide_horizontal_scrollbar')
		scrollbar_horizontal = self._container.get_hscrollbar()
		scrollbar_horizontal.set_child_visible(not hide_scrollbar)

		# change change sorting sensitivity
		self._sort_case_sensitive = section.get('case_sensitive_sort')
		self._sort_number_sensitive = section.get('number_sensitive_sort')

		# apply size formatting
		self._size_format = options.get('size_format')

		# apply selection
		self._selection_color = section.get('selection_color')
		self._selection_indicator = section.get('selection_indicator')

		# get support for second level of extension
		self._second_extension = section.get('second_extension')

		# change status bar visibility
		show_status_bar = options.get('show_status_bar')

		if show_status_bar == StatusVisible.ALWAYS:
			self._show_status_bar()

		elif show_status_bar == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

		elif show_status_bar == StatusVisible.NEVER:
			self._hide_status_bar()
