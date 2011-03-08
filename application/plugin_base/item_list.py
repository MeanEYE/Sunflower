#!/usr/bin/env python

import os
import gtk
import locale
import threading

from plugin import PluginBase

# button text constants
BUTTON_TEXT_BOOKMARKS	= u'\u2318'
BUTTON_TEXT_HISTORY 	= u'\u2630'
BUTTON_TEXT_TERMINAL	= u'\u2605'


class ItemList(PluginBase):
	"""General item list

	Abstract class for all list based plugins. It provides basic
	user interface elements as well as some predefined methods.

	You are strongly encouraged to use predefined methods rather than
	defining your own.

	"""

	def __init__(self, parent, notebook, path=None, sort_column=None, sort_ascending=True):
		global _icon_theme

		self._provider = None
		self._menu_timer = None

		self.history = []

		# call parent constructor
		PluginBase.__init__(self, parent, notebook, path)

		# global key event handlers with modifier switches (control, alt, shift)
		self._key_handlers = {
			'Tab': {
					'000': self._parent.focus_oposite_list,
					'100': self._notebook_next_tab,
					'101': self._notebook_previous_tab,
				},
			'ISO_Left_Tab': {  # CTRL+SHIFT+Tab produces ISO_Left_Tab
					'101': self._notebook_previous_tab,
				},
			'Return': {
					'000': self._execute_selected_item,
#					'100': pass
				},
			't': {
					'100': self._duplicate_tab,
					'101': self._open_in_new_tab,
				},
			'w': {
					'100': self._close_tab,
				},
			'z': {
					'100': self._create_terminal,
				},
			'BackSpace': {
					'000': self._parent_folder,
				},
			'Insert': {
					'000': self._toggle_selection,
				},
			'Delete': {
					'000': self._delete_files,
				},
			'F1': {
					'100': self._show_left_bookmarks,
				},
			'F2': {
					'000': self._rename_file,
					'100': self._show_right_bookmarks,
				},
			'F4': {
					'000': self._edit_selected,
				},
			'F5': {
					'000': self._copy_files,
				},
			'F6': {
					'000': self._move_files,
					'001': self._rename_file,
				},
			'F8': {
					'000': self._delete_files,
				},
			'Menu': {
					'000': self._show_popup_menu,
					'100': self._show_open_with_menu,
				},
			'Left': {
					'000': self._parent_folder,
					'100': self._handle_path_inheritance,
				},
			'Right': {
					'100': self._handle_path_inheritance,
					'000': self._execute_selected_item,
				},
			}

		# if enabled bind VIM keys
		if self._parent.options.getboolean('main', 'vim_movement'):
			self._key_handlers.update({
						'h': { '000': self._parent_folder, },
						'l': { '000': self._execute_selected_item, },
						'j': { '000': self._move_marker_down, },
						'k': { '000': self._move_marker_up, }
					})

		# list statistics
		self._dirs = {'count': 0, 'selected': 0}
		self._files = {'count': 0, 'selected': 0}
		self._size = {'total': 0L, 'selected': 0}

		# we use this variable to prevent dead loop during column resize
		self._is_updating = False

		# sort options
		self._sort_column = sort_column
		self._sort_ascending = sort_ascending
		self._sort_column_widget = None
		self._sort_sensitive = self._parent.options.getboolean('main', 'case_sensitive_sort')
		self._columns = None

		# idle spinner
		try:
			# try to create spinner element
			self._spinner = gtk.Spinner()

			self._spinner.set_size_request(16, 16)
			self._spinner.set_property('no-show-all', True)

			self._top_hbox.pack_start(self._spinner, False, False, 3)

		except:
			# spinner is not required part of the program
			self._spinner = None

		# bookmarks button
		self._bookmarks_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			image_bookmarks = gtk.Image()
			image_bookmarks.set_from_icon_name('go-jump', gtk.ICON_SIZE_MENU)
			self._bookmarks_button.set_image(image_bookmarks)

		else:
			self._bookmarks_button.set_label(BUTTON_TEXT_BOOKMARKS)

		self._bookmarks_button.set_focus_on_click(False)
		self._bookmarks_button.set_tooltip_text(_('Bookmarks'))
		self._bookmarks_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._bookmarks_button.connect('clicked', self._bookmarks_button_clicked)

		self._top_hbox.pack_end(self._bookmarks_button, False, False, 0)

		# history button
		self._history_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			# set icon
			image_history = gtk.Image()
			image_history.set_from_icon_name('document-open-recent', gtk.ICON_SIZE_MENU)
			self._history_button.set_image(image_history)
		else:
			# set text
			self._history_button.set_label(BUTTON_TEXT_HISTORY)

		self._history_button.set_focus_on_click(False)
		self._history_button.set_tooltip_text(_('History'))
		self._history_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._history_button.connect('clicked', self._history_button_clicked)

		self._top_hbox.pack_end(self._history_button, False, False, 0)

		# terminal button
		self._terminal_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			# set icon
			image_terminal = gtk.Image()
			image_terminal.set_from_icon_name('terminal', gtk.ICON_SIZE_MENU)
			self._terminal_button.set_image(image_terminal)
		else:
			# set text
			self._terminal_button.set_label(BUTTON_TEXT_TERMINAL)

		self._terminal_button.set_focus_on_click(False)
		self._terminal_button.set_tooltip_text(_('Terminal'))
		self._terminal_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._terminal_button.connect('clicked', self._create_terminal)

		self._top_hbox.pack_end(self._terminal_button, False, False, 0)

		# file list
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._item_list = gtk.TreeView()
		self._item_list.set_fixed_height_mode(True)

		self._item_list.connect('button-press-event', self._handle_button_press)
		self._item_list.connect('button-release-event', self._handle_button_press)

		self._connect_main_object(self._item_list)

		container.add(self._item_list)

		# quick search
		self._search_panel = gtk.HBox(False, 0)

		label = gtk.Label(_('Search:'))

		self._search_entry = gtk.Entry()
		self._search_entry.connect('key-press-event', self._handle_search_key_press)
		self._search_entry.connect('focus-out-event', self._stop_search)
		self._item_list.set_search_entry(self._search_entry)

		self._search_panel.pack_start(label, False, False, 3)
		self._search_panel.pack_start(self._search_entry, True, True, 0)

		# popup menu
		self._open_with_item = None
		self._open_with_menu = None
		self._popup_menu = self._create_popup_menu()

		# history menu
		self._history_menu = gtk.Menu()
		self._history_menu.connect('hide', self._handle_history_hide)

		# pack gui
		self.pack_start(container, True, True, 0)
		self.pack_start(self._search_panel, False, False, 0)

		self._change_top_panel_color(gtk.STATE_NORMAL)

		self.show_all()
		self._search_panel.hide()

	def _show_spinner(self):
		"""Show spinner animation"""
		if self._spinner is not None:
			self._spinner.start()
			self._spinner.show()

	def _show_left_bookmarks(self, widget, data=None):
		"""Show left bookmarks menu"""
		self._parent.show_bookmarks_menu(None, self._parent.left_notebook)

	def _show_right_bookmarks(self, widget, data=None):
		"""Show right bookmarks menu"""
		self._parent.show_bookmarks_menu(None, self._parent.right_notebook)

	def _hide_spinner(self):
		"""Hide spinner animation"""
		if self._spinner is not None:
			self._spinner.hide()
			self._spinner.stop()

	def _create_default_column_sizes(self):
		"""Create default column sizes section in main configuration file"""
		options = self._parent.options
		section = self.__class__.__name__

		if not options.has_section(section):
			# section doesn't exist, create one
			options.add_section(section)

			# store default column sizes
			for i, size in enumerate(self._columns_size):
				options.set(section, 'size_{0}'.format(i), size)

	def _move_marker_up(self, widget, data=None):
		"""Move marker up"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get current path
			path = list_.get_path(iter_)[0]
			previous = path - 1

			# if selected item is not first, move selection
			if previous >= 0:
				self._item_list.set_cursor(previous)

		return True

	def _move_marker_down(self, widget, data=None):
		"""Move marker down"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get current path
			path = list_.get_path(iter_)[0]
			next_ = path + 1

			# if selected item is not last, move selection
			if next_ < len(list_):
				self._item_list.set_cursor(next_)

		return True

	def _handle_button_press(self, widget, event):
		"""Handles mouse events"""
		result = False

		# handle single click
		if event.button is 1 and event.type is gtk.gdk.BUTTON_RELEASE and \
		event.state & gtk.gdk.CONTROL_MASK:
			self._toggle_selection(widget, event, advance=False)
			result = True

		# handle double click
		elif event.button is 1 and event.type is gtk.gdk._2BUTTON_PRESS:
			self._execute_selected_item(widget)
			result = True

		# handle right click
		elif event.button is 3:
			if event.type is gtk.gdk.BUTTON_RELEASE:
				# button was released, depending on options call specific method
				if not self._parent.options.getboolean('main', 'right_click_select'):
					# show popup menu
					self._show_popup_menu(widget)

				else:
					# toggle item mark
					self._toggle_selection(widget, advance=False)

					# if exists, cancel schedule
					if self._menu_timer is not None:
						self._menu_timer.cancel()

				result = True

			elif self._parent.options.getboolean('main', 'right_click_select'):
				# in case where right click selects, we need to schedule menu popup
				self._menu_timer = threading.Timer(1, self._show_popup_menu, [widget,])
				self._menu_timer.start()

		return result

	def _handle_key_press(self, widget, event):
		"""Handles key events in item list"""
		result = PluginBase._handle_key_press(self, widget, event)

		if not result:
			# generate state sting based on modifier state (control, alt, shift)
			state = "%d%d%d" % (
						bool(event.state & gtk.gdk.CONTROL_MASK),
						bool(event.state & gtk.gdk.MOD1_MASK),
						bool(event.state & gtk.gdk.SHIFT_MASK)
					)

			# retrieve human readable key representation
			key_name = gtk.gdk.keyval_name(event.keyval)

			# make letters lowercase for easier handling
			if len(key_name) == 1: key_name = key_name.lower()

			# handle searching for hidden files
			if key_name == 'period': key_name = '.'

			# give other handlers chance to process event
			if state == self._parent.options.get('main', 'search_modifier'):
				self._start_search(key_name)
				result = True

			else:
				result = False

				if len(key_name) == 1:
					self._focus_command_line(key_name)
					result = True

		return result

	def _handle_search_key_press(self, widget, event):
		"""Handle return and escape keys for quick search"""
		result = False
		key_name = gtk.gdk.keyval_name(event.keyval)

		if key_name == 'Escape':
			self._stop_search()
			result = True

		if key_name == 'Return':
			self._stop_search()
			self._execute_selected_item(widget)
			result = True

		return result

	def _handle_history_click(self, widget, data=None):
		"""Handle clicks on bookmark menu"""
		path = widget.get_data('path')

		if os.path.isdir(path):
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
										"Directory does not exist anymore or is not "
										"valid. If path is not local check if specified "
										"volume is mounted."
									) +	"\n\n{0}".format(path)
								)
			dialog.run()
			dialog.destroy()

	def _handle_history_hide(self, widget, data=None):
		"""Handle history menu hide event"""
		self._disable_object_block()
		oposite_list = self._parent.get_oposite_list(self)
		oposite_list._disable_object_block()

	def _start_search(self, key):
		"""Shows quick search panel and starts searching"""
		self._search_panel.show()
		self._search_entry.grab_focus()
		self._search_entry.set_text(key)
		self._search_entry.set_position(len(key))

	def _stop_search(self, widget=None, data=None):
		"""Hide quick search panel and return focus to item list"""
		self._search_panel.hide()
		self._item_list.grab_focus()
		return False

	def _execute_selected_item(self, widget=None, data=None):
		"""Abstract method for handling execution of certain item"""
		return True

	def _open_in_new_tab(self, widget=None, data=None):
		"""Open selected directory in new tab"""
		return True

	def _create_directory(self, widget=None, data=None):
		"""Abstract method used to create directory"""
		pass

	def _create_file(self, widget=None, data=None):
		"""Abstract method used to create file"""
		pass

	def _delete_files(self, widget=None, data=None):
		"""Abstract method used to delete files"""
		pass

	def _copy_files(self, widget=None, data=None):
		"""Abstract method used to copy files"""
		pass

	def _move_files(self, widget=None, data=None):
		"""Abstract method used to move files"""
		pass

	def _rename_file(self, widget=None, data=None):
		"""Abstract method used to rename selection"""
		pass

	def _send_to(self, widget=None, data=None):
		"""Abstract method for Send To Nautilus integration"""
		pass

	def _get_selection(self):
		"""Return item with path under cursor"""
		pass

	def _get_selection_list(self):
		"""Return list of selected items

		This list is used by many other methods inside this program,
		including 'open with' handlers, execute_selected file, etc.

		"""
		pass

	def _get_popup_menu_position(self, menu, data=None):
		"""Abstract method for positioning menu properly on given row"""
		return (0, 0, True)

	def _get_history_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def _get_other_provider(self):
		"""Return provider from oposite list.

		If oposite tab is not ItemList or does not have a provider
		return None.

		"""
		notebook = self._parent.left_notebook \
								if self._notebook is self._parent.right_notebook \
								else self._parent.right_notebook

		object = notebook.get_nth_page(notebook.get_current_page())

		if hasattr(object, "get_provider"):
			result = object.get_provider()
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
								'callback': self._execute_selected_item
							})
		result.append(item)

		# open directory in new tab
		item = menu_manager.create_menu_item({
								'label': _('Open in new ta_b'),
								'type': 'image',
								'stock': gtk.STOCK_OPEN,
								'callback': self._open_in_new_tab
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

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# cut/copy/paste
		item = menu_manager.create_menu_item({
								'label': _('Cu_t'),
								'type': 'image',
								'stock': gtk.STOCK_CUT,
							})
		result.append(item)
		item.set_sensitive(False)

		item = menu_manager.create_menu_item({
								'label': _('_Copy'),
								'type': 'image',
								'stock': gtk.STOCK_COPY,
							})
		result.append(item)
		item.set_sensitive(False)

		item = menu_manager.create_menu_item({
								'label': _('_Paste'),
								'type': 'image',
								'stock': gtk.STOCK_PASTE,
							})
		result.append(item)
		item.set_sensitive(False)

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# send to
		item = menu_manager.create_menu_item({
								'label': _('Send to...'),
								'callback': self._send_to,
								'type': 'image',
								'image': 'document-send'
							})
		result.append(item)
		self._send_to_item = item

		# link/rename
		item = menu_manager.create_menu_item({
								'label': _('Ma_ke link'),
							})
		result.append(item)
		item.set_sensitive(False)

		item = menu_manager.create_menu_item({
								'label': _('_Rename...'),
								'callback': self._rename_file
							})
		result.append(item)
		item.set_sensitive(False)
		self._rename_item = item

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# delete
		item = menu_manager.create_menu_item({
								'label': _('_Delete'),
								'type': 'image',
								'stock': gtk.STOCK_DELETE,
								'callback': self._delete_files
							})
		result.append(item)
		self._delete_item = item

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# properties
		item = menu_manager.create_menu_item({
								'label': _('_Properties'),
								'type': 'image',
								'stock': gtk.STOCK_PROPERTIES,
							})
		result.append(item)
		item.set_sensitive(False)

		return result

	def _prepare_popup_menu(self):
		"""Prepare popup menu contents"""
		# remove existing items
		for item in self._open_with_menu.get_children():
			self._open_with_menu.remove(item)

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

		else:
			# no items to create, make blank item
			menu_item = gtk.MenuItem(_('History is empty'))
			menu_item.set_sensitive(False)

			self._history_menu.append(menu_item)

		# show all menu items
		self._history_menu.show_all()

	def _show_open_with_menu(self, widget, data=None):
		"""Show 'open with' menu"""
		# prepare elements in popup menu
		self._prepare_popup_menu()

		# if this method is called by Menu key data is actually event object
		self._open_with_menu.popup(
								None,
								None,
								self._get_popup_menu_position,
								1,
								data.time
							)

	def _show_popup_menu(self, widget, data=None):
		"""Show item menu"""

		# prepare elements in popup menu
		self._prepare_popup_menu()

		if data is not None:
			# if this method is called by Menu key data is actually event object
			self._popup_menu.popup(None, None, self._get_popup_menu_position, 1, data.time)

		else:
			# if called by mouse, we don't have the need to position the menu manually
			self._popup_menu.popup(None, None, None, 1, 0)

		return True

	def _parent_folder(self, widget=None, data=None):
		"""Move to parent folder"""
		self.change_path(
						os.path.dirname(self.path),
						os.path.basename(self.path)
					)

		return True  # to prevent command or quick search in single key bindings

	def _focus_command_line(self, key):
		"""Focus command-line control"""
		if self._parent.options.getboolean('main', 'show_command_entry'):
			# focus command entry only if it's visible
			self._parent.command_edit.grab_focus()
			self._parent.command_edit.set_text(key)
			self._parent.command_edit.set_position(len(key))

		return True

	def _control_got_focus(self, widget, data=None):
		"""List focus in event"""
		PluginBase._control_got_focus(self, widget, data)
		self._parent.path_label.set_text(self.path)

	def _change_top_panel_color(self, state):
		"""Modify coloring of top panel"""
		# call parent class method first
		PluginBase._change_top_panel_color(self, state)

		# get color style from parent
		style = self._parent.get_style().copy()
		background_color = style.bg[state]
		text_color = style.text[state]

		# change button background colors for normal state
		self._bookmarks_button.modify_bg(gtk.STATE_NORMAL, background_color)
		self._history_button.modify_bg(gtk.STATE_NORMAL, background_color)
		self._terminal_button.modify_bg(gtk.STATE_NORMAL, background_color)

		# change button text colors for normal state
		self._bookmarks_button.child.modify_fg(gtk.STATE_NORMAL, text_color)
		self._history_button.child.modify_fg(gtk.STATE_NORMAL, text_color)
		self._terminal_button.child.modify_fg(gtk.STATE_NORMAL, text_color)

	def _bookmarks_button_clicked(self, widget, data=None):
		"""Bookmarks button click event"""
		self._parent.menu_bookmarks.set_data('list', self)
		self._parent.show_bookmarks_menu(widget)

	def _history_button_clicked(self, widget, data=None):
		"""History button click event"""
		# prepare menu for drawing
		self._prepare_history_menu()

		# show the menu on calculated location
		self._enable_object_block()
		oposite_list = self._parent.get_oposite_list(self)
		oposite_list._enable_object_block()

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
		self._parent.create_terminal_tab(self._notebook, self.path)
		return True

	def _set_sort_function(self, widget, data=None):
		"""Abstract method used for setting sort function"""
		pass

	def _column_resized(self, widget, data=None):
		"""Resize all columns acordingly"""
		new_width = widget.get_width()
		existing_width = self._parent.options.getint(
												self.__class__.__name__,
												'size_{0}'.format(widget.size_id)
												)

		if not new_width == existing_width:
			self._parent.options.set(
									self.__class__.__name__,
									'size_{0}'.format(widget.size_id),
									new_width
									)
			self._parent.update_column_sizes(widget, self)

	def _resize_columns(self, columns):
		"""Resize columns acording to global options"""
		for index, column in columns.items():
			# register column resize id
			if not hasattr(column, 'size_id'):
				column.size_id = index

			# set column size
			width = self._parent.options.getint(
											self.__class__.__name__,
											'size_{0}'.format(index)
											)
			column.set_fixed_width(width)

	def _sort_list(self, ascending=True):
		"""Abstract method for manual list sorting"""
		pass

	def _clear_list(self):
		"""Abstract method for clearing item list"""
		pass

	def _update_status_with_statistis(self):
		"""Set status bar text acording to dir/file stats"""
		status = self._parent.options.get('main', 'status_text')

		status = status.replace('%dir_count', str(self._dirs['count']))
		status = status.replace('%dir_sel', str(self._dirs['selected']))
		status = status.replace('%file_count', str(self._files['count']))
		status = status.replace('%file_sel', str(self._files['selected']))
		status = status.replace('%size_total', locale.format('%d', self._size['total'], True))
		status = status.replace('%size_sel', locale.format('%d', self._size['selected'], True))

		self.update_status(status)

	def _toggle_selection(self, widget, data=None, advance=True):
		"""Abstract method for toggling item selection"""
		pass

	def _edit_selected(self, widget, data=None):
		"""Abstract method to edit currently selected item"""
		pass

	def _edit_filename(self, filename):
		"""Open editor with specified filename and current path"""
		pass

	def _handle_path_inheritance(self, widget, event):
		"""Handle inheriting or setting paths from/to other lists"""
		result = False
		key_name = gtk.gdk.keyval_name(event.keyval)

		if self._notebook is self._parent.left_notebook:
			# handle if we are on the left side
			oposite_object = self._parent.right_notebook.get_nth_page(
												self._parent.right_notebook.get_current_page()
											)

			if key_name == 'Right':
				if hasattr(oposite_object, 'feed_terminal'):
					oposite_object.feed_terminal(os.path.basename(self._get_selection()))
				else:
					oposite_object.change_path(self.path)

				result = True

			elif key_name == 'Left':
				self.change_path(oposite_object.path)
				result = True

		else:
			# handle if we are on the right side
			oposite_object = self._parent.left_notebook.get_nth_page(
												self._parent.left_notebook.get_current_page()
											)

			if key_name == 'Right':
				self.change_path(oposite_object.path)
				result = True

			elif key_name == 'Left':
				if hasattr(oposite_object, 'feed_terminal'):
					oposite_object.feed_terminal(os.path.basename(self._get_selection()))
				else:
					oposite_object.change_path(self.path)

				result = True

		return result

	def change_path(self, path=None):
		"""Public method for safe path change """
		real_path = os.path.expanduser(path)

		if not real_path in self.history:
			self.history.insert(0, real_path)

		else:
			i = self.history.index(real_path)
			if i != 0:
				self.history[0], self.history[i] = self.history[i], self.history[0]

	def select_all(self, pattern=None, exclude_list=None):
		"""Select all items matching pattern"""
		pass

	def unselect_all(self, pattern=None):
		"""Unselect items matching the pattern"""
		pass

	def invert_selection(self, pattern=None):
		"""Invert selection on matching items"""
		pass

	def refresh_file_list(self, widget=None, data=None):
		"""Reload file list for current directory"""
		self.change_path(self.path)

	def update_column_size(self, size_id):
		"""Update column sizes"""
		pass

	def get_povider(self):
		"""Get list provider"""
		return self._provider

	def apply_settings(self):
		"""Apply settings"""
		# update status
		self._update_status_with_statistis()

		# change change sorting sensitivity
		self._sort_sensitive = self._parent.options.getboolean('main', 'case_sensitive_sort')

		# change button relief
		self._bookmarks_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])
		self._history_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])
		self._terminal_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])
