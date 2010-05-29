#!/usr/bin/env python

import os
import shutil
import gtk
import time
import locale
import stat
import mimetypes
import user
import fnmatch

from application.provider import Provider
from application.operation import DeleteOperation, CopyOperation, MoveOperation
from gui.input_dialog import FileCreateDialog, DirectoryCreateDialog, CopyDialog

# try to import I/O library
try:
	import gio
except:
	gio = None


from plugin_base.item_list import ItemList

# constants
COL_NAME   = 0
COL_EXT    = 1
COL_SIZE   = 2
COL_MODE   = 3
COL_DATE   = 4
COL_DIR    = 5
COL_PARENT = 6
COL_COLOR  = 7

class FileList(ItemList):

	def __init__(self, parent, notebook, path=None):
		ItemList.__init__(self, parent, notebook)

		# storage system for list items
		self._store = gtk.ListStore(str, str, float, int, int,
									bool, bool, str)

		# set item list model
		self._item_list.set_model(self._store)

		# create columns
		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_extension = gtk.CellRendererText()
		cell_size = gtk.CellRendererText()
		cell_mode = gtk.CellRendererText()
		cell_date = gtk.CellRendererText()

		cell_name.set_property('font', 'Monospace')
		cell_extension.set_property('size-points', 8)
		cell_size.set_property('size-points', 8)
		cell_size.set_property('xalign', 1)
		cell_mode.set_property('size-points', 8)
		cell_date.set_property('size-points', 8)

		# create columns
		col_file = gtk.TreeViewColumn('Filename')
		col_extension = gtk.TreeViewColumn('Ext')
		col_size = gtk.TreeViewColumn('Size')
		col_mode = gtk.TreeViewColumn('Mode')
		col_date = gtk.TreeViewColumn('Date')

		# add cell renderers to columns
		col_file.pack_start(cell_icon, False)
		col_file.pack_start(cell_name, True)
		col_extension.pack_start(cell_extension, True)
		col_size.pack_start(cell_size, True)
		col_mode.pack_start(cell_mode, True)
		col_date.pack_start(cell_date, True)

		col_file.add_attribute(cell_name, 'foreground', COL_COLOR)
		col_extension.add_attribute(cell_extension, 'foreground', COL_COLOR)
		col_size.add_attribute(cell_size, 'foreground', COL_COLOR)
		col_mode.add_attribute(cell_mode, 'foreground', COL_COLOR)
		col_date.add_attribute(cell_date, 'foreground', COL_COLOR)

		col_file.set_cell_data_func(cell_icon, self._column_icon)
		col_file.set_cell_data_func(cell_name, self._column_filename)
		col_extension.set_cell_data_func(cell_extension, self._column_extension)
		col_size.set_cell_data_func(cell_size, self._column_size)
		col_mode.set_cell_data_func(cell_mode, self._column_mode)
		col_date.set_cell_data_func(cell_date, self._column_date)

		col_file.set_resizable(True)
		col_file.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_extension.set_resizable(True)
		col_extension.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_size.set_resizable(True)
		col_size.set_alignment(1)
		col_size.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_mode.set_resizable(True)
		col_mode.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_date.set_resizable(True)
		col_date.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		# register columns
		self._columns = {
					0: col_file,
					1: col_extension,
					2: col_size,
					3: col_mode,
					4: col_date
				}

		self._resize_columns(self._columns)

		# connect click events for columns
		col_file.connect('clicked',	self._set_sort_function, COL_NAME)
		col_extension.connect('clicked', self._set_sort_function, COL_EXT)
		col_size.connect('clicked',	self._set_sort_function, COL_SIZE)
		col_mode.connect('clicked',	self._set_sort_function, COL_MODE)
		col_date.connect('clicked',	self._set_sort_function, COL_DATE)

		col_file.connect('notify::width', self._column_resized)
		col_extension.connect('notify::width', self._column_resized)
		col_size.connect('notify::width', self._column_resized)
		col_mode.connect('notify::width', self._column_resized)
		col_date.connect('notify::width', self._column_resized)

		# append columns
		self._item_list.append_column(col_file)
		self._item_list.append_column(col_extension)
		self._item_list.append_column(col_size)
		self._item_list.append_column(col_mode)
		self._item_list.append_column(col_date)

		self._item_list.set_headers_clickable(True)
		self._item_list.set_enable_search(True)
		self._item_list.set_search_column(COL_NAME)

		row_hinting = self._parent.options.getboolean('main', 'row_hinting')
		self._item_list.set_rules_hint(row_hinting)

		# change list icon
		icon = self._parent.icon_manager.get_icon_from_type('folder', gtk.ICON_SIZE_LARGE_TOOLBAR)
		self._icon.set_from_pixbuf(icon)

		# set sort function
		self._set_sort_function(col_file, COL_NAME)

		# directory monitor
		self._fs_monitor = None

		# change to initial path
		try:
			self.change_path(path)
		except:
			# failsafe jump to user home directory
			self.change_path(user.home)

	def _execute_selected_item(self, widget, data=None):
		"""Execute/Open selected item/directory"""
		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		name = list.get_value(iter, COL_NAME)
		is_dir = list.get_value(iter, COL_DIR)
		is_parent = list.get_value(iter, COL_PARENT)

		if is_dir:
			if is_parent:
				self._parent_folder(widget, data)
			else:
				self.change_path(os.path.join(self.path, name))
				
		elif self.get_provider().is_local:
			# each os uses different method for opening files
			command = {
					'nt': 'start "" "{0}"',
					'posix': "gnome-open '{0}'",
				}

			# call the os-specific command
			os.system(command[os.name].format(self._get_selection()))

	def _create_directory(self, widget=None, data=None):
		"""Prompt user and create directory"""
		dialog = DirectoryCreateDialog(self._parent)

		# get response
		response = dialog.get_response()
		mode = dialog.get_mode()

		# release dialog
		dialog.destroy()

		# create dialog
		if response[0] == gtk.RESPONSE_OK:
			try:
				# try to create directories
				self.get_provider().create_directory(os.path.join(self.path, response[1]), mode)

			except OSError as error:
				# error creating, report to user
				dialog = gtk.MessageDialog(
										self._parent,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										"There was an error creating directory. "
										"Make sure you have enough permissions. "
										"\n\n{0}".format(error)
										)
				dialog.run()
				dialog.destroy()

	def _create_file(self, widget, data=None):
		"""Prompt user and create empty file"""
		dialog = FileCreateDialog(self._parent)

		# get response
		response = dialog.get_response()
		mode = dialog.get_mode()

		# release dialog
		dialog.destroy()

		# create dialog
		if response[0] == gtk.RESPONSE_OK:
			try:
				# try to create file
				# TODO: Create file through provider
				if os.path.isfile(os.path.join(self.path, response[1])):
					raise OSError("File already exists: {0}".format(response[1]))

				if os.path.isdir(os.path.join(self.path, response[1])):
					raise OSError("Directory with same name exists: {0}".format(response[1]))

				open(os.path.join(self.path, response[1]), 'w').close()

				if os.name not in ('nt',):	# we can set file mode only on posix file systems
					os.chmod(os.path.join(self.path, response[1]), mode)

			except OSError as error:
				# error creating, report to user
				dialog = gtk.MessageDialog(
										self._parent,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										"There was an error creating file. "
										"Make sure you have enough permissions. "
										"\n\n{0}".format(error)
										)
				dialog.run()
				dialog.destroy()

	def _delete_files(self, widget=None, data=None):
		"""Delete selected files"""
		list = self._get_selection_list()
		if list is None: return

		dialog = gtk.MessageDialog(
								self._parent,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_QUESTION,
								gtk.BUTTONS_YES_NO,
								"You are about to remove {0} item(s).\n"
								"Are you sure about this?".format(len(list))
								)
		result = dialog.run()
		dialog.destroy()

		if result == gtk.RESPONSE_YES:
			# if user is sure about removal create operation
			operation = DeleteOperation(
									self._parent,
									self.get_provider(),
									None
									)
			operation.start()
		
	def _copy_files(self, widget=None, data=None):
		"""Copy selected files"""
		list = self._get_selection_list()
		if list is None: return

		dialog = CopyDialog(self._parent, self.get_provider())
		result = dialog.get_response()
		
		if result[0] == gtk.RESPONSE_OK:
			# if user confirmed copying
			operation = CopyOperation(
									self._parent,
									self.get_provider(),
									None,
									result[1]  # options from dialog
									)
			operation.start()

	def _send_to(self, widget, data=None):
		"""Nautilus Send To integration"""
		selection = self._get_selection_list()

		if selection is not None and self.get_provider().is_local:
			params = " ".join(
							'"{0}"'.format(
										os.path.join(self.path, item)
										) for item in selection
							)

			command = "nautilus-sendto {0}&".format(params)
			os.system(command)

	def _get_selection(self):
		"""Return item with path under cursor"""
		result = None
		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		is_parent = list.get_value(iter, COL_PARENT)

		if not is_parent:
			result = os.path.join(self.path, list.get_value(iter, COL_NAME))

		return result

	def _get_selection_list(self, under_cursor=False):
		"""Return list of selected items

		This list is used by many other methods inside this program,
		including 'open with' handlers, execute_selected file, etc.

		"""
		result = []

		if under_cursor:
			selection = self._get_selection()
			if selection is None:
				result = None
			else:
				result.append(self._get_selection())

		else:
			for row in self._store:
				if row[COL_COLOR] is not None:
					result.append(os.path.join(self.path, row[COL_NAME]))

		if len(result) is 0:
			selection = self._get_selection()
			if selection is None:
				result = None
			else:
				result.append(self._get_selection())

		return result

	def _prepare_popup_menu(self):
		"""Populate popup menu items"""
		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		is_dir = list.get_value(iter, COL_DIR)
		is_parent = list.get_value(iter, COL_PARENT)

		# get selected item
		filename = self._get_selection()

		# call parents method which removes existing menu items
		ItemList._prepare_popup_menu(self)

		# get user configuration
		program_list = []

		if not is_dir:
			# we need to prepare menu only for files
			mime_type = mimetypes.guess_type(filename, False)[0]

			try:
				list = self._parent.associations_manager.get_user_list(mime_type)
				if list is not None:
					program_list.extend(list)

				# get default configuration
				list = self._parent.associations_manager.get_default_list(mime_type)
				if list is not None:
					program_list.extend((list_item) for list_item in list if list_item not in program_list)

				# filter out empty entrys
				program_list = filter(lambda x: x is not '', program_list)

			except:
				# sometimes config parser raises exception for god knows what reason
				# so this way we get around it just to be sure to display menu
				pass

		# add all items to menu
		for config_file in program_list:
			menu_item =	self._parent.menu_manager.get_menu_item_from_config(
																	config_file, 
																	self._get_selection_list
																	)

			# if got menu item back as result, add it to the list
			if menu_item is not None:
				self._open_with_menu.append(menu_item)

		# disable/enable items
		has_items = len(self._open_with_menu.get_children()) is not 0
		self._open_with_item.set_sensitive(has_items and self.get_provider().is_local)
		self._send_to_item.set_sensitive(self.get_provider().is_local and not is_parent)
		self._delete_item.set_sensitive(not is_parent)

	def _get_popup_menu_position(self, menu, data=None):
		"""Positions menu properly for given row"""

		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		# grab cell and tree rectangles
		rect = self._item_list.get_cell_area(list.get_path(iter), self._columns[0])
		tree_rect = self._item_list.get_visible_rect()

		# grab window coordinates
		window_x, window_y = self._parent.window.get_position()

		# relative to tree
		x, y = rect.x, rect.y + rect.height
		x, y = self._item_list.convert_tree_to_widget_coords(x, y)

		# modify coordinate by tree display rectangle vertical offset
		y += tree_rect.y

		# relative to window
		x, y = self._item_list.translate_coordinates(self._parent, x, y)

		# relative to screen
		x += window_x
		y += window_y

		return (x, y, True)

	def _set_sort_function(self, widget, data=None):
		"""Set sorting method stored in data

		If no data (sort column) is provided we just reset the sort function
		parameters using predefined column and order.

		"""

		if widget is not self._sort_column_widget:
			self._sort_column_widget = widget

		if data is not None:
			if self._sort_column == data:
				# reverse sorting if column is already sorted
				self._sort_ascending = not self._sort_ascending
				
			else:
				# set sorting column
				self._sort_column = data

		widget.set_sort_indicator(True)

		# set sort indicator only on one column
		for column in self._item_list.get_columns():
			selected = column is widget
			column.set_sort_indicator(selected)

		order = [gtk.SORT_DESCENDING, gtk.SORT_ASCENDING][self._sort_ascending]
		widget.set_sort_order(order)

		self._store.set_sort_func(self._sort_column, self._sort_list)
		self._store.set_sort_column_id(self._sort_column, order)

		# set focus to the list, we don't need it on column
		self._item_list.grab_focus()

	def _sort_list(self, list, iter1, iter2, data=None):
		"""Sort list"""
		reverse = (1, -1)[self._sort_ascending]

		item1 = [
				reverse * list.get_value(iter1, COL_PARENT),
				reverse * list.get_value(iter1, COL_DIR),
				list.get_value(iter1, self._sort_column)
				]

		item2 = [
				reverse * list.get_value(iter2, COL_PARENT),
				reverse * list.get_value(iter2, COL_DIR),
				list.get_value(iter2, self._sort_column)
				]

		return cmp(item1, item2)

	def _clear_list(self):
		"""Clear item list"""
		self._store.clear()

	def _directory_changed(self, monitor, file, other_file, event):
		"""Callback method fired when contents of directory has been changed"""

		# node created
		if event is gio.FILE_MONITOR_EVENT_CREATED:
			self._add_item(file.get_path())

		# node deleted
		elif event is gio.FILE_MONITOR_EVENT_DELETED:
			self._delete_item_by_name(file.get_basename())

		# node changed
		elif event is gio.FILE_MONITOR_EVENT_CHANGED:
			self._update_item_details_by_name(file.get_path())

	def _toggle_selection(self, widget, data=None, advance=True):
		"""Toggle item selection"""
		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		is_dir = list.get_value(iter, COL_DIR)
		is_parent = list.get_value(iter, COL_PARENT)

		if not is_parent:
			# get current status of iter
			selected = list.get_value(iter, COL_COLOR) is not None

			if is_dir:
				self._dirs['selected'] += [1, -1][selected]
			else:
				self._files['selected'] += [1, -1][selected]

			# toggle selection
			selected = not selected

			value = [None, 'red'][selected]
			list.set_value(iter, COL_COLOR, value)

		# update status bar
		self._update_status_with_statistis()

		if advance:
			# select next item in the list
			next_iter = list.iter_next(iter)
			if next_iter is not None:
				self._item_list.set_cursor(list.get_path(next_iter))

	def _column_icon(self, column, cell, list, iter):
		"""Data provider function for icon"""
		is_dir = list.get_value(iter, COL_DIR)
		is_parent = list.get_value(iter, COL_PARENT)
		name = os.path.join(self.path, list.get_value(iter, COL_NAME))

		if is_dir:
				icon = self._parent.icon_manager.get_icon_from_type(
							('folder', 'up')[is_parent]
						)
		else:
			icon = self._parent.icon_manager.get_icon_for_file(name)

		cell.set_property('pixbuf', icon)

	def _column_filename(self, column, cell, list, iter):
		"""Data provider function for filename"""
		is_dir = list.get_value(iter, COL_DIR)
		name = list.get_value(iter, COL_NAME)

		if not is_dir:
			name = os.path.splitext(name)[0]

		cell.set_property('text', name)

	def _column_extension(self, column, cell, list, iter):
		"""Data provider function for extension"""
		is_dir = list.get_value(iter, COL_DIR)
		name = os.path.splitext(
						list.get_value(iter, COL_NAME)
					)[1][1:] if not is_dir else ''

		cell.set_property('text', name)

	def _column_size(self, column, cell, list, iter):
		"""Data provider function for size"""
		is_dir = list.get_value(iter, COL_DIR)

		size = locale.format(
						'%d', list.get_value(iter, COL_SIZE), True
					) if not is_dir else '<DIR>'

		cell.set_property('text', size)

	def _column_mode(self, column, cell, list, iter):
		"""Data provider function for mode"""
		is_parent = list.get_value(iter, COL_PARENT)
		mode = oct(list.get_value(iter, COL_MODE)) if not is_parent else ''

		cell.set_property('text', mode)

	def _column_date(self, column, cell, list, iter):
		"""Data provider function for date"""
		is_parent = list.get_value(iter, COL_PARENT)
		raw_date = list.get_value(iter, COL_DATE)

		format = self._parent.options.get('main', 'time_format')
		date = time.strftime(
							format,
							time.gmtime(raw_date)
						) if not is_parent else ''

		cell.set_property('text', date)

	def _edit_selected(self, widget=None, data=None):
		"""Abstract method to edit currently selected item"""
		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		is_dir = list.get_value(iter, COL_DIR)

		if not is_dir and self.get_provider().is_local:
			filename = list.get_value(iter, COL_NAME)
			default_editor = self._parent.options.get('main', 'default_editor')
			command = default_editor.format(os.path.join(self.path, filename))

			os.system(command)

		return True

	def _find_iter_by_name(self, name):
		""" Find and return item by name"""
		result = None

		for row in self._store:
			if row[COL_NAME] == name:
				result = row.iter
				break

		return result

	def _add_item(self, full_name, show_hidden=False):
		"""Add item to the list"""
		file_size = 0
		file_mode = 0
		file_date = 0

		result = None
		file_name = os.path.basename(full_name)
		can_add = not (file_name[0] == '.' and not show_hidden)
		provider = self.get_provider()

		# TODO: Modify os.stat to be derived from provider

		if can_add:
			# directory
			if os.path.isdir(full_name):
				file_stat = provider.get_stat(full_name)

				file_size = -1
				file_mode = stat.S_IMODE(file_stat.st_mode)
				file_date = file_stat.st_mtime

				is_dir = True
				self._dirs['count'] += 1

			# regular file
			elif os.path.isfile(full_name):
				file_stat = provider.get_stat(full_name)

				file_size = file_stat.st_size
				file_mode = stat.S_IMODE(file_stat.st_mode)
				file_date = file_stat.st_mtime

				is_dir = False
				self._files['count'] += 1

			# link
			elif os.path.islink(full_name):
				# TODO: Finish!
				linked_name = os.path.join(self.path, os.readlink(full_name))
				if os.path.exists(linked_name):
					file_stat = provider.get_stat(linked_name)

					file_size = file_stat.st_size
					file_mode = stat.S_IMODE(file_stat.st_mode)
					file_date = file_stat.st_mtime

				else:
					file_size = 0
					file_mode = 0
					file_date = 0

				is_dir = False
				self._files['count'] += 1

			# add item to the list
			try:
				props = (
						file_name,
						os.path.splitext(file_name)[1],
						file_size,
						file_mode,
						file_date,
						is_dir,
						False,
						None,
					)
				result = self._store.append(props)
			except:
				print 'Error: ', props

		return result

	def _delete_item_by_name(self, name):
		"""Removes item with 'name' from the list"""
		selection = self._item_list.get_selection()
		list, selected_iter = selection.get_selected()

		# get currently selected name
		selected_name = None
		if selected_iter is not None:
			selected_name = list.get_value(selected_iter, COL_NAME)

		# find iter matching 'name'
		found_iter = self._find_iter_by_name(name)

		if found_iter is not None:
			iter_name = self._store.get_value(found_iter, COL_NAME)

			# if currently hovered item was removed
			if iter_name == selected_name:
				next_iter = list.iter_next(selected_iter)
				if next_iter is not None:
					self._item_list.set_cursor(list.get_path(next_iter))

			# remove
			self._store.remove(found_iter)

	def _update_item_details_by_name(self, name):
		"""Update item details (size, time, etc.) on changed event"""
		found_iter = self._find_iter_by_name(os.path.basename(name))

		if found_iter is not None:
			# get node stats
			file_stat = os.stat(name)

			if os.path.isdir(name):
				file_size = -1
			else:
				file_size = file_stat.st_size

			file_mode = stat.S_IMODE(file_stat.st_mode)
			file_date = file_stat.st_mtime

			# update list store
			self._store.set_value(found_iter, COL_SIZE, file_size)
			self._store.set_value(found_iter, COL_MODE, file_mode)
			self._store.set_value(found_iter, COL_DATE, file_date)

	def _change_title_text(self, text):
		"""Change title label text and add free space display"""
		stat = os.statvfs(self.path)

		space_free = self._format_size(stat.f_bsize * stat.f_bavail)
		space_total = self._format_size(stat.f_bsize * stat.f_blocks)

		self._title_label.set_label(
									'{0}\n<span size="x-small">'
									'Free: {1} - Total: {2}</span>'.format(text, space_free, space_total)
								)

	def _format_size(self, size):
		"""Convert size to more human readable format"""
		for x in ['B','kB','MB','GB','TB']:
			if size < 1024.0:
				return "%3.1f %s" % (size, x)
			size /= 1024.0

	def change_path(self, path=None, selected=None):
		"""Change file list path"""

		# cancel current directory monitor
		if gio is not None and self._fs_monitor is not None:
			self._fs_monitor.cancel()

		self._clear_list()
		ItemList.change_path(self, path)

		# change path
		if path is not None:
			self.path = os.path.abspath(path)
		else:
			self.path = user.home

		path_name = os.path.basename(self.path)
		if path_name == "": path_name = os.path.abspath(self.path)

		self._change_tab_text(path_name)
		self._change_title_text(self.path)
		self._parent.path_label.set_text(self.path)

		to_select = None
		show_hidden = self._parent.options.getboolean('main', 'show_hidden')

		# disconnect store from widget to speed up the process
		# disabled: not required atm
		#~self._item_list.set_model(None)
		#~self._store.set_default_sort_func(None)

		self._dirs['count'] = 0
		self._dirs['selected'] = 0
		self._files['count'] = 0
		self._files['selected'] = 0

		# populate list
		# TODO: Use provider
		for file_name in self.get_provider().list_dir(self.path):
			full_name = os.path.join(self.path, file_name)

			new_item = self._add_item(full_name, show_hidden)

			if selected is not None and file_name == selected:
				to_select = new_item

		# update status bar
		self._update_status_with_statistis()

		# add parent option for parent directory
		self._store.insert(0, (
							os.path.pardir,
							'',
							-2,
							-1,
							-1,
							True,
							True,
							None,
						))

		# restore model and sort function
		# disabled: not required atm
		#~self._item_list.set_model(self._store)
		#~self._set_sort_function(self._sort_column_widget)

		# select either first or previous item
		if to_select is not None:
			path = self._store.get_path(to_select)
		else:
			path = self._store.get_path(self._store.get_iter_first())

		# select item
		self._item_list.set_cursor(path)

		# register file monitor
		if gio is not None and self.get_provider().is_local:
			self._fs_monitor = gio.File(self.path).monitor_directory()
			self._fs_monitor.connect('changed', self._directory_changed)

	def select_all(self, pattern=None):
		"""Select all items matching pattern """

		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0

		for row in self._store:
			# set selection
			if not row[COL_PARENT] and fnmatch.fnmatch(row[COL_NAME], pattern):
				row[COL_COLOR] = 'red'

			# update dir/file count
			if row[COL_COLOR] is not None:
				if row[COL_DIR]:
					dirs += 1
				else:
					files += 1

		self._dirs['selected'] = dirs
		self._files['selected'] = files

		self._update_status_with_statistis()

	def unselect_all(self, pattern=None):
		"""Unselect items matching the pattern"""

		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0

		for row in self._store:
			# set selection
			if not row[COL_PARENT] and fnmatch.fnmatch(row[COL_NAME], pattern):
				row[COL_COLOR] = None

			# update dir/file count
			if row[COL_COLOR] is not None:
				if row[COL_DIR]:
					dirs += 1
				else:
					files += 1

		self._dirs['selected'] = dirs
		self._files['selected'] = files

		self._update_status_with_statistis();

	def invert_selection(self, pattern=None):
		"""Invert selection matching the pattern"""
		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0

		for row in self._store:
			# set selection
			if not row[COL_PARENT] and fnmatch.fnmatch(row[COL_NAME], pattern):
				if row[COL_COLOR] is None:
					row[COL_COLOR] = 'red'
				else:
					row[COL_COLOR] = None

			# update dir/file count
			if row[COL_COLOR] is not None:
				if row[COL_DIR]:
					dirs += 1
				else:
					files += 1

		self._dirs['selected'] = dirs
		self._files['selected'] = files

		self._update_status_with_statistis();

	def refresh_file_list(self, widget=None, data=None):
		"""Reload file list for current directory"""
		selection = self._item_list.get_selection()
		list, iter = selection.get_selected()

		f_name = list.get_value(iter, COL_NAME)
		self.change_path(self.path, f_name)

		return True

	def update_column_size(self, size_id):
		"""Update column size with global value"""

		column = self._columns[size_id]
		width = self._parent.options.getint(
										self.__class__.__name__,
										'size_{0}'.format(size_id)
										)
		column.set_fixed_width(width)

	def get_provider(self):
		"""Get list provider object"""
		if self._provider is None:
			self._provider = LocalProvider(self)
			
		return self._provider


class LocalProvider(Provider):
	"""Content provider for local files"""
	is_local = True
	
	def _is_file(self, path):
		"""Test if given path is file"""
		return os.path.isfile(path)

	def _is_dir(self, path):
		"""Test if given path is directory"""
		return os.path.isdir(path)

	def _is_link(self, path):
		"""Test if given path is a link"""
		return os.path.islink(path)

	def _unlink(self, path):
		"""Unlink given path"""
		os.remove(path)

	def _remove_directory(self, path, recursive):
		"""Remove directory and optionally its contents"""
		if recursive:
			shutil.rmtree(path)
		else:
			os.rmdir(path)

	def _remove_file(self, path):
		"""Remove file"""
		os.remove(path)
		
	def create_file(self, path, mode=None):
		"""Create empty file with specified mode set"""
		pass
	
	def create_directory(self, path, mode=None):
		"""Create directory with specified mode set"""
		os.makedirs(path, mode if mode is not None else 0755)

	def get_file_handle(self, path, mode):
		"""Open path in specified mode and return its handle"""
		pass
	
	def get_stat(self, path):
		"""Return file statistics"""
		return os.stat(path)

	def list_dir(self, path):
		"""Get directory list"""
		return os.listdir(path)
