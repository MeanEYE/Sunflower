#!/usr/bin/env python

import os
import gtk
import locale

from plugin import PluginBase

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
		self._open_with_menu = None
		self._open_with_item = None

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

		self._dirs = {'count': 0, 'selected': 0}
		self._files = {'count': 0, 'selected': 0}
		self._size = {'total': 0L, 'selected': 0}

		self._is_updating = False

		self._sort_column = sort_column
		self._sort_ascending = sort_ascending
		self._sort_column_widget = None
		self._columns = None

		# idle spinner
		self._spinner = gtk.Spinner()
		self._spinner.set_size_request(16, 16)
		self._spinner.set_property('no-show-all', True)

		self._top_hbox.pack_start(self._spinner, False, False, 3)

		# bookmarks button
		self._bookmarks_button = gtk.Button(u'\u2318')
		self._bookmarks_button.set_focus_on_click(False)
		self._bookmarks_button.set_tooltip_text('Bookmarks')
		self._bookmarks_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._bookmarks_button.connect('clicked', self._bookmarks_button_clicked)

		self._top_hbox.pack_end(self._bookmarks_button, False, False, 0)

		# history button
		self._history_button = gtk.Button(u'\u2630')
		self._history_button.set_focus_on_click(False)
		self._history_button.set_tooltip_text('History')
		self._history_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._history_button.connect('clicked', self._history_button_clicked)

		self._top_hbox.pack_end(self._history_button, False, False, 0)

		# terminal button
		self._terminal_button = gtk.Button(u'\u2605')
		self._terminal_button.set_focus_on_click(False)
		self._terminal_button.set_tooltip_text('Terminal')
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

		label = gtk.Label('Search:')

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

		# pack gui
		self.pack_start(container, True, True, 0)
		self.pack_start(self._search_panel, False, False, 0)

		self._change_top_panel_color(gtk.STATE_NORMAL)

		self.show_all()
		self._search_panel.hide()

	def _show_spinner(self):
		"""Show spinner animation"""
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
		self._spinner.hide()
		self._spinner.stop()

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
		elif event.button is 3 and event.type is gtk.gdk.BUTTON_RELEASE:
			self._show_popup_menu(widget)
			result = True

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

	def _execute_selected_item(self, widget, data=None):
		"""Abstract method for handling execution of certain item"""
		return True

	def _create_directory(self, widget, data=None):
		"""Abstract method used to create directory"""
		pass

	def _create_file(self, widget, data=None):
		"""Abstract method used to create file"""
		pass

	def _delete_files(self, widget, data=None):
		"""Abstract method used to delete files"""
		pass

	def _copy_files(self, widget, data=None):
		"""Abstract method used to copy files"""
		pass

	def _move_files(self, widget, data=None):
		"""Abstract method used to move files"""
		pass

	def _rename_file(self, widget, data=None):
		"""Abstract method used to rename selection"""
		pass

	def _send_to(self, widget, data=None):
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
								'label': '_Open',
								'type': 'image',
								'stock': gtk.STOCK_OPEN,
								'callback': self._execute_selected_item
							})
		result.append(item)

		# separator
		item = menu_manager.create_menu_item({'type': 'separator'})
		result.append(item)

		# dynamic menu
		item = menu_manager.create_menu_item({
								'label': 'Open _with',
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
								'label': 'Cu_t',
								'type': 'image',
								'stock': gtk.STOCK_CUT,
							})
		result.append(item)
		item.set_sensitive(False)

		item = menu_manager.create_menu_item({
								'label': '_Copy',
								'type': 'image',
								'stock': gtk.STOCK_COPY,
							})
		result.append(item)
		item.set_sensitive(False)

		item = menu_manager.create_menu_item({
								'label': '_Paste',
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
								'label': 'Send to...',
								'callback': self._send_to,
							})
		result.append(item)
		self._send_to_item = item

		# link/rename
		item = menu_manager.create_menu_item({
								'label': 'Ma_ke link',
							})
		result.append(item)
		item.set_sensitive(False)

		item = menu_manager.create_menu_item({
								'label': '_Rename...',
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
								'label': '_Delete',
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
								'label': '_Properties',
								'type': 'image',
								'stock': gtk.STOCK_INFO,
							})
		result.append(item)
		item.set_sensitive(False)

		return result

	def _prepare_popup_menu(self):
		"""Prepare popup menu contents"""
		# remove existing items
		for item in self._open_with_menu.get_children():
			self._open_with_menu.remove(item)

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

	def _parent_folder(self, widget, data=None):
		"""Move to parent folder"""
		self.change_path(
						os.path.dirname(self.path),
						os.path.basename(self.path)
					)

	def _focus_command_line(self, key):
		"""Focus command-line control"""
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
		PluginBase._change_top_panel_color(self, state)

		style = self._parent.get_style().copy()
		background_color = style.bg[state]
		text_color = style.text[state]

		self._bookmarks_button.modify_bg(gtk.STATE_NORMAL, background_color)
		self._history_button.modify_bg(gtk.STATE_NORMAL, background_color)
		self._terminal_button.modify_bg(gtk.STATE_NORMAL, background_color)

		self._bookmarks_button.child.modify_fg(gtk.STATE_NORMAL, text_color)
		self._history_button.child.modify_fg(gtk.STATE_NORMAL, text_color)
		self._terminal_button.child.modify_fg(gtk.STATE_NORMAL, text_color)

	def _bookmarks_button_clicked(self, widget, data=None):
		"""Bookmarks button click event"""
		self._parent.menu_bookmarks.set_data('list', self)
		self._parent.show_bookmarks_menu(widget)

	def _history_button_clicked(self, widget, data=None):
		"""History button click event"""
		pass

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
		if not path in self.history:
			self.history.insert(0, path)

		else:
			i = self.history.index(path)
			if not i == 0:
				self.history[0], self.history[i] = self.history[i], self.history[0]

	def select_all(self, pattern=None):
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
