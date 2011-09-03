import os
import gtk
import locale
import urllib
import common

from plugin import PluginBase

from operation import CopyOperation, MoveOperation
from accelerator_group import AcceleratorGroup
from gui.input_dialog import CopyDialog, MoveDialog
from gui.preferences.display import StatusVisible
from gui.history_list import HistoryList


class ButtonText:
	BOOKMARKS = u'\u2318'
	HISTORY = u'\u2630'
	TERMINAL = u'\u2605'


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

		# list statistics
		self._dirs = {'count': 0, 'selected': 0}
		self._files = {'count': 0, 'selected': 0}
		self._size = {'total': 0L, 'selected': 0}

		# local human readable cache
		self._human_readable = self._parent.options.getboolean('main', 'human_readable_size')

		# we use this variable to prevent dead loop during column resize
		self._is_updating = False

		# sort options
		self._sort_column = sort_column
		self._sort_ascending = sort_ascending
		self._sort_column_widget = None
		self._sort_sensitive = self._parent.options.getboolean('main', 'case_sensitive_sort')
		self._columns = None

		# bookmarks button
		self._bookmarks_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			image_bookmarks = gtk.Image()
			image_bookmarks.set_from_icon_name('go-jump', gtk.ICON_SIZE_MENU)
			self._bookmarks_button.set_image(image_bookmarks)

		else:
			self._bookmarks_button.set_label(ButtonText.BOOKMARKS)

		self._bookmarks_button.set_focus_on_click(False)
		self._bookmarks_button.set_tooltip_text(_('Bookmarks'))
		self._bookmarks_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._bookmarks_button.connect('clicked', self._bookmarks_button_clicked)

		self._title_bar.add_control(self._bookmarks_button)

		# history button
		self._history_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			# set icon
			image_history = gtk.Image()
			image_history.set_from_icon_name('document-open-recent', gtk.ICON_SIZE_MENU)
			self._history_button.set_image(image_history)
		else:
			# set text
			self._history_button.set_label(ButtonText.HISTORY)

		self._history_button.set_focus_on_click(False)
		self._history_button.set_tooltip_text(_('History'))
		self._history_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._history_button.connect('clicked', self._history_button_clicked)

		self._title_bar.add_control(self._history_button)

		# terminal button
		self._terminal_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			# set icon
			image_terminal = gtk.Image()
			image_terminal.set_from_icon_name('terminal', gtk.ICON_SIZE_MENU)
			self._terminal_button.set_image(image_terminal)
		else:
			# set text
			self._terminal_button.set_label(ButtonText.TERMINAL)

		self._terminal_button.set_focus_on_click(False)
		self._terminal_button.set_tooltip_text(_('Terminal'))
		self._terminal_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
		                        )[self._parent.options.getint('main', 'button_relief')])

		self._terminal_button.connect('clicked', self._create_terminal)

		self._title_bar.add_control(self._terminal_button)

		# configure status bar
		self._status_bar.add_group_with_icon('dirs', 'folder', '0/0')
		self._status_bar.add_group_with_icon('files', 'document', '0/0')
		self._status_bar.add_group_with_icon('size', 'add', '0/0')

		# file list
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._item_list = gtk.TreeView()
		self._item_list.set_fixed_height_mode(True)

		headers_visible = self._parent.options.getboolean('main', 'headers_visible')
		self._item_list.set_headers_visible(headers_visible)

		self._item_list.connect('button-press-event', self._handle_button_press)
		self._item_list.connect('button-release-event', self._handle_button_press)
		self._item_list.connect('cursor-changed', self._handle_cursor_change)
		self._item_list.connect('columns-changed', self._column_changed)

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

		self.show_all()
		self._search_panel.hide()

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
		group.add_method('item_properties', _('Show selected item properties'), self._item_properties)
		group.add_method('add_bookmark', _('Bookmark current directory'), self._add_bookmark)
		group.add_method('edit_bookmarks', _('Edit bookmarks'), self._edit_bookmarks)
		group.add_method('cut_to_clipboard', _('Cut selection to clipboard'), self._cut_files_to_clipboard)
		group.add_method('copy_to_clipboard', _('Copy selection to clipboard'), self._copy_files_to_clipboard)
		group.add_method('paste_from_clipboard', _('Paste items from clipboard'), self._paste_files_from_clipboard)
		group.add_method('open_in_new_tab', _('Open selected directory in new tab'), self._open_in_new_tab)
		group.add_method('create_terminal', _('Create terminal tab'), self._create_terminal)
		group.add_method('parent_directory', _('Go to parent directory'), self._parent_directory)
		group.add_method('show_history', _('Show history browser'), self._show_history_window)
		group.add_method('toggle_selection', _('Toggle selection'), self._toggle_selection)
		group.add_method('delete_files', _('Delete selected items'), self._delete_files)
		group.add_method('show_left_bookmarks', _('Show bookmarks for left list'), self._show_left_bookmarks)
		group.add_method('show_right_bookmarks', _('Show bookmarks for right list'), self._show_right_bookmarks)
		group.add_method('rename_file', _('Rename selected item'), self._rename_file)
		group.add_method('edit_selected', _('Edit selected item'), self._edit_selected)
		group.add_method('copy_files', _('Copy selected items'), self._copy_files)
		group.add_method('move_files', _('Move selected items'), self._move_files)
		group.add_method('show_popup_menu', _('Show context menu'), self._show_popup_menu)
		group.add_method('show_open_with_menu', _('Show "open with" menu'), self._show_open_with_menu)
		group.add_method('inherit_left_path', _('Assign path from left list'), self._inherit_left_path)
		group.add_method('inherit_right_path', _('Assign path from right list'), self._inherit_right_path)
		group.add_method('move_marker_up', _('Move selection marker up'), self._move_marker_up)
		group.add_method('move_marker_down', _('Move selection marker down'), self._move_marker_down)

		# configure accelerators
		group.set_accelerator('execute_item', keyval('Return'), 0)
		group.set_accelerator('item_properties', keyval('Return'), gtk.gdk.MOD1_MASK)
		group.set_accelerator('add_bookmark', keyval('d'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('edit_bookmarks', keyval('b'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('cut_to_clipboard', keyval('x'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('copy_to_clipboard', keyval('c'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('paste_from_clipboard', keyval('v'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('open_in_new_tab', keyval('t'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('create_terminal', keyval('z'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('parent_directory', keyval('BackSpace'), 0)
		group.set_accelerator('show_history', keyval('BackSpace'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('toggle_selection', keyval('Insert'), 0)
		group.set_accelerator('delete_files', keyval('Delete'), 0)
		group.set_alt_accelerator('delete_files', keyval('F8'), 0)
		group.set_accelerator('show_left_bookmarks', keyval('F1'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('show_right_bookmarks', keyval('F2'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('rename_file', keyval('F2'), 0)
		group.set_alt_accelerator('rename_file', keyval('F6'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('edit_selected', keyval('F4'), 0)
		group.set_accelerator('copy_files', keyval('F5'), 0)
		group.set_accelerator('move_files', keyval('F6'), 0)
		group.set_accelerator('show_popup_menu', keyval('Menu'), 0)
		group.set_alt_accelerator('show_popup_menu', keyval('F10'), gtk.gdk.SHIFT_MASK)
		group.set_accelerator('show_open_with_menu', keyval('Menu'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('inherit_left_path', keyval('Right'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('inherit_right_path', keyval('Left'), gtk.gdk.CONTROL_MASK)

		# create bookmark accelerators
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

	def _show_left_bookmarks(self, widget, data=None):
		"""Show left bookmarks menu"""
		self._parent.show_bookmarks_menu(None, self._parent.left_notebook)

	def _show_right_bookmarks(self, widget, data=None):
		"""Show right bookmarks menu"""
		self._parent.show_bookmarks_menu(None, self._parent.right_notebook)

	def _show_history_window(self, widget, data=None):
		"""Show history browser"""
		HistoryList(self, self._parent)

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
		right_click_select = self._parent.options.getboolean('main', 'right_click_select')

		# handle single click
		if event.button is 1 \
		and event.state & gtk.gdk.CONTROL_MASK \
		and event.type in (gtk.gdk.BUTTON_PRESS, gtk.gdk.BUTTON_RELEASE):
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

		# handle double click
		elif event.button is 1 and event.type is gtk.gdk._2BUTTON_PRESS:
			self._execute_selected_item(widget)
			result = True

		# handle right click
		elif event.button is 3:
			if event.type is gtk.gdk.BUTTON_PRESS:
				# record mouse down timestamp
				self._popup_timestamp = event.get_time()

				# prevent CTRL+RightClick from generating exceptions
				if event.state & gtk.gdk.CONTROL_MASK:
					result = True

			elif event.type is gtk.gdk.BUTTON_RELEASE:
				# button was released, depending on options call specific method
				time_valid = event.get_time() - self._popup_timestamp > 500

				if not right_click_select or (right_click_select and time_valid):
					# show popup menu
					self._show_popup_menu(widget)

				else:
					# toggle item mark
					self._toggle_selection(widget, advance=False)

				result = True

		return result

	def _handle_key_press(self, widget, event):
		"""Handles key events in item list"""
		result = PluginBase._handle_key_press(self, widget, event)

		if not result:
			# retrieve human readable key representation
			key_name = gtk.gdk.keyval_name(event.keyval)

			# handle searching for hidden files
			if key_name == 'period': key_name = '.'

			if len(key_name) == 1:
				# generate state sting based on modifier state (control, alt, shift)
				state = "%d%d%d" % (
							bool(event.state & gtk.gdk.CONTROL_MASK),
							bool(event.state & gtk.gdk.MOD1_MASK),
							bool(event.state & gtk.gdk.SHIFT_MASK)
						)

				if state == self._parent.options.get('main', 'search_modifier'):
					# start quick search if modifier combination is right
					self._start_search(key_name)
					result = True

				else:
					# otherwise focus command entry
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

	def _handle_history_click(self, widget=None, data=None, path=None):
		"""Handle clicks on bookmark menu"""
		if path is None:
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
		oposite_object = self._parent.get_oposite_object(self)
		oposite_object._disable_object_block()

	def _handle_external_data(self, operation, protocol, list_):
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
		path = os.path.dirname(list_[0])
		selection = [os.path.basename(item) for item in list_]

		# create provider
		provider = Provider(self, path, selection)

		# check if we actually have data to handle
		if len(provider.get_selection()) == 0:
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
					provider,
					self.path
				)
		dialog_result = dialog.get_response()

		# check user response
		if dialog_result[0] == gtk.RESPONSE_OK:
			# user confirmed copying
			operation = Operation(
								self._parent,
								provider,
								self.get_provider(),
								dialog_result[1]  # options from dialog
							)

			# start the operation
			operation.start()

			result = True

		return result

	def _handle_cursor_change(self, widget=None, data=None):
		"""Handle cursor change"""
		pass

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

	def _cut_files_to_clipboard(self, widget=None, data=None):
		"""Cut selected files to clipboard"""
		self._copy_files_to_clipboard(operation='cut')
		return True

	def _copy_files_to_clipboard(self, widget=None, data=None, operation='copy'):
		"""Copy selected files to clipboard"""
		list_ = self._get_selection_list(relative=False)

		# make sure list actually contains something
		if list_ is not None:
			provider = self.get_provider()
			protocol = provider.protocols[0]

			# modify list to form URI
			list_ = ['{0}://{1}'.format(protocol, urllib.quote(item)) for item in list_]

			# set clipboard data
			self._parent.set_clipboard_item_list(operation, list_)

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
			self._handle_external_data(operation, protocol, list_)

		return True

	def _item_properties(self, widget=None, data=None):
		"""Abstract method that shows file/directory properties"""
		pass

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

	def _bookmarks_button_clicked(self, widget, data=None):
		"""Bookmarks button click event"""
		self._parent.show_bookmarks_menu(widget, self._notebook)

	def _history_button_clicked(self, widget, data=None):
		"""History button click event"""
		# prepare menu for drawing
		self._prepare_history_menu()

		# show the menu on calculated location
		self._enable_object_block()
		oposite_object = self._parent.get_oposite_object(self)
		oposite_object._enable_object_block()

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
		"""Resize all columns accordingly"""
		column_width = widget.get_width()
		column_name = widget.get_data('name')
		section_name = self.__class__.__name__
		option_name = 'size_{0}'.format(column_name)
		
		# get stored column width
		if self._parent.options.has_option(section_name, option_name):
			existing_width = self._parent.options.getint(section_name, option_name)
			
		else:
			existing_width = -1

		# if current width is not the same as stored one, save
		if not column_width == existing_width:
			self._parent.options.set(section_name, option_name,	column_width)
			self._parent.update_column_sizes(widget, self)
			
	def _column_changed(self, widget, data=None):
		"""Handle adding, removing and reordering columns"""
		columns = self._item_list.get_columns()
		column_names = map(lambda column: column.get_data('name'), columns)
		
		print self.__class__.__name__
		
		print column_names

	def _resize_columns(self, columns):
		"""Resize columns according to global options"""
		for column in columns:
			# set column size
			width = self._parent.options.getint(
											self.__class__.__name__,
											'size_{0}'.format(column.get_data('name'))
											)
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
		if self._human_readable:
			total_text = common.format_size(self._size['total'])
			selected_text = common.format_size(self._size['selected'])

		else:
			total_text = locale.format('%d', self._size['total'], True)
			selected_text = locale.format('%d', self._size['selected'], True)

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

	def _toggle_selection(self, widget, data=None, advance=True):
		"""Abstract method for toggling item selection"""
		if self._parent.options.getint('main', 'show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def _edit_selected(self, widget, data=None):
		"""Abstract method to edit currently selected item"""
		pass

	def _edit_filename(self, filename):
		"""Open editor with specified filename and current path"""
		pass

	def _inherit_left_path(self, widget, data=None):
		"""Inherit path in right list from left"""
		oposite_object = self._parent.get_oposite_object(self)

		if self._notebook is self._parent.left_notebook:
			if hasattr(oposite_object, 'change_path'):
				oposite_object.change_path(self.path)

			elif hasattr(oposite_object, 'feed_terminal'):
				oposite_object.feed_terminal(self.path)

		else:
			self.change_path(oposite_object.path)

	def _inherit_right_path(self, widget, data=None):
		"""Inherit path in left list from right"""
		oposite_object = self._parent.get_oposite_object(self)

		if self._notebook is self._parent.right_notebook:
			if hasattr(oposite_object, 'change_path'):
				oposite_object.change_path(self.path)

			elif hasattr(oposite_object, 'feed_terminal'):
				oposite_object.feed_terminal(self.path)

		else:
			self.change_path(oposite_object.path)

	def _add_bookmark(self, widget, data=None):
		"""Show dialog for adding current path to bookmarks"""
		self._parent._add_bookmark(widget, self)
		return True

	def _edit_bookmarks(self, widget, data=None):
		"""Open preferences window with bookmarks tab selected"""
		self._parent.preferences_window._show(widget, 'bookmarks')
		return True

	def change_path(self, path=None, selected=None):
		"""Public method for safe path change """
		real_path = os.path.expanduser(path)

		if not real_path in self.history:
			self.history.insert(0, real_path)

		else:
			i = self.history.index(real_path)
			if i != 0:
				self.history[0], self.history[i] = self.history[i], self.history[0]

		# update status bar visibility
		if self._parent.options.getint('main', 'show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def select_all(self, pattern=None, exclude_list=None):
		"""Select all items matching pattern"""
		if self._parent.options.getint('main', 'show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def unselect_all(self, pattern=None):
		"""Unselect items matching the pattern"""
		if self._parent.options.getint('main', 'show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def invert_selection(self, pattern=None):
		"""Invert selection on matching items"""
		if self._parent.options.getint('main', 'show_status_bar') == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

	def refresh_file_list(self, widget=None, data=None):
		"""Reload file list for current directory"""
		self.change_path(self.path)

	def update_column_size(self, name):
		"""Update column sizes"""
		pass

	def get_povider(self):
		"""Get list provider"""
		return self._provider

	def apply_settings(self):
		"""Apply settings"""
		# let parent class do its work
		PluginBase.apply_settings(self)

		# update status
		self._update_status_with_statistis()

		# change headers visibility
		headers_visible = self._parent.options.getboolean('main', 'headers_visible')
		self._item_list.set_headers_visible(headers_visible)

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

		# apply size formatting
		self._human_readable = self._parent.options.getboolean('main', 'human_readable_size')

		# change status bar visibility
		show_status_bar = self._parent.options.getint('main', 'show_status_bar')

		if show_status_bar == StatusVisible.ALWAYS:
			self._show_status_bar()

		elif show_status_bar == StatusVisible.WHEN_NEEDED:
			selected_items = self._dirs['selected'] + self._files['selected']
			(self._hide_status_bar, self._show_status_bar)[selected_items > 0]()

		elif show_status_bar == StatusVisible.NEVER:
			self._hide_status_bar()
