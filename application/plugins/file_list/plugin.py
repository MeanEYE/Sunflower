import os
import shutil
import gtk
import time
import locale
import stat
import gnomevfs
import user
import fnmatch
import urllib
import common

from provider import FileType
from local_provider import LocalProvider
from operation import DeleteOperation, CopyOperation, MoveOperation
from gui.input_dialog import FileCreateDialog, DirectoryCreateDialog
from gui.input_dialog import CopyDialog, MoveDialog, RenameDialog
from gui.properties_window import PropertiesWindow
from widgets.thumbnail_view import ThumbnailView

# try to import I/O library
try:
	import gio
except:
	gio = None

from plugin_base.item_list import ItemList


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_class('file_list', _('Local file list'), FileList)
	application.register_provider(LocalProvider)


class Column:
	NAME = 0
	FORMATED_NAME = 1
	EXTENSION = 2
	SIZE = 3
	FORMATED_SIZE = 4
	MODE = 5
	FORMATED_MODE = 6
	TIME = 7
	FORMATED_TIME = 8
	IS_DIR = 9
	IS_PARENT_DIR = 10
	COLOR = 11
	ICON = 12
	SELECTED = 13


class FileList(ItemList):
	"""General file list plugin

	This plugin was written with various usages in mind. If you need to write
	plugin that will handle files it is strongly suggested that you inherit this class
	and make your own content provider.

	"""

	def __init__(self, parent, notebook, path=None, sort_column=None, sort_ascending=True):
		ItemList.__init__(self, parent, notebook, path, sort_column, sort_ascending)

		# storage system for list items
		self._store = gtk.ListStore(
								str,	# Column.NAME
								str,	# Column.FORMATED_NAME
								str,	# Column.EXTENSION
								float,	# Column.SIZE
								str,	# Column.FORMATED_SIZE
								int,	# Column.MODE
								str,	# Column.FORMATED_MODE
								int,	# Column.DATE
								str,	# Column.FORMATED_DATE
								bool,	# Column.IS_DIR
								bool,	# Column.IS_PARENT_DIR
								str,	# Column.COLOR
								str, 	# Column.ICON
								gtk.gdk.Pixbuf  # Column.SELECTED
							)

		# set item list model
		self._item_list.set_model(self._store)

		# selection image
		image = gtk.Image()
		image.set_from_file(os.path.abspath(os.path.join(
									'images',
									'selection_arrow.png'
								)))

		self._pixbuf_selection = image.get_pixbuf()

		# create columns
		cell_selected = gtk.CellRendererPixbuf()
		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_extension = gtk.CellRendererText()
		cell_size = gtk.CellRendererText()
		cell_mode = gtk.CellRendererText()
		cell_date = gtk.CellRendererText()

		cell_selected.set_property('width', 6)
		cell_extension.set_property('size-points', 8)
		cell_size.set_property('size-points', 8)
		cell_size.set_property('xalign', 1)
		cell_mode.set_property('size-points', 8)
		cell_date.set_property('size-points', 8)

		# create columns
		col_name = gtk.TreeViewColumn(_('Name'))
		col_extension = gtk.TreeViewColumn(_('Ext'))
		col_size = gtk.TreeViewColumn(_('Size'))
		col_mode = gtk.TreeViewColumn(_('Mode'))
		col_date = gtk.TreeViewColumn(_('Date'))

		# set column names
		col_name.set_data('name', 'name')
		col_extension.set_data('name', 'extension')
		col_size.set_data('name', 'size')
		col_mode.set_data('name', 'mode')
		col_date.set_data('name', 'date')

		# add cell renderer to columns
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.pack_start(cell_selected, False)
		col_extension.pack_start(cell_extension, True)
		col_size.pack_start(cell_size, True)
		col_mode.pack_start(cell_mode, True)
		col_date.pack_start(cell_date, True)

		col_name.add_attribute(cell_name, 'foreground', Column.COLOR)
		col_extension.add_attribute(cell_extension, 'foreground', Column.COLOR)
		col_size.add_attribute(cell_size, 'foreground', Column.COLOR)
		col_mode.add_attribute(cell_mode, 'foreground', Column.COLOR)
		col_date.add_attribute(cell_date, 'foreground', Column.COLOR)

		col_name.add_attribute(cell_selected, 'pixbuf', Column.SELECTED)
		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'text', Column.FORMATED_NAME)
		col_extension.add_attribute(cell_extension, 'text', Column.EXTENSION)
		col_size.add_attribute(cell_size, 'text', Column.FORMATED_SIZE)
		col_mode.add_attribute(cell_mode, 'text', Column.FORMATED_MODE)
		col_date.add_attribute(cell_date, 'text', Column.FORMATED_TIME)

		col_name.set_resizable(True)
		col_name.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_extension.set_resizable(True)
		col_extension.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_size.set_resizable(True)
		col_size.set_alignment(1)
		col_size.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_mode.set_resizable(True)
		col_mode.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		col_date.set_resizable(True)
		col_date.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		# set default column sizes for file list
		self._columns_size = [200, 50, 70, 50, 100]
		self._create_default_column_sizes()

		# register columns
		self._columns = (col_name, col_extension, col_size, col_mode, col_date)

		# resize columns to saved values
		self._resize_columns(self._columns)

		# create a list of columns
		column_sort_data = {
					Column.NAME: col_name,
					Column.EXTENSION: col_extension,
					Column.SIZE: col_size,
					Column.MODE: col_mode,
					Column.TIME: col_date,
				}

		# block columns-changed signal while adding columns
		self._item_list.handler_block_by_func(self._column_changed)

		# configure and pack columns
		for sort_data, column in column_sort_data.items():
			# connect events
			column.connect('clicked', self._set_sort_function, sort_data)
			column.connect('notify::width', self._column_resized)
			column.set_reorderable(True)

			# add to the list
			self._item_list.append_column(column)

		# release signal block
		self._item_list.handler_unblock_by_func(self._column_changed)

		# set list behavior
		self._item_list.set_headers_clickable(True)
		self._item_list.set_enable_search(True)
		self._item_list.set_search_column(Column.NAME)

		# set row hinting
		row_hinting = self._parent.options.getboolean('main', 'row_hinting')
		self._item_list.set_rules_hint(row_hinting)

		# set grid lines
		grid_lines = (
					gtk.TREE_VIEW_GRID_LINES_NONE,
					gtk.TREE_VIEW_GRID_LINES_HORIZONTAL,
					gtk.TREE_VIEW_GRID_LINES_VERTICAL,
					gtk.TREE_VIEW_GRID_LINES_BOTH,
				)[self._parent.options.getint('main', 'grid_lines')]
		self._item_list.set_grid_lines(grid_lines)

		# change list icon
		self._title_bar.set_icon_from_name('folder')

		# set sort function
		if self._sort_column is None:
			# default sort by name
			self._sort_column = Column.NAME
			self._sort_ascending = True

		self._sort_column_widget = column_sort_data[self._sort_column]
		self._apply_sort_function()

		# directory monitor
		self._fs_monitor = None

		# thumbnail view
		self._thumbnail_view = ThumbnailView(self)
		self._enable_media_preview = self._parent.options.getboolean('main', 'media_preview')

		# variable that is used to set focus on newly created files and dirs
		self._item_to_focus = None

		# change to initial path
		try:
			self.change_path(path)

		except:
			# fail-safe jump to user home directory
			self.change_path(user.home)

	def _control_got_focus(self, widget, data=None):
		"""Handle control gaining focus"""
		ItemList._control_got_focus(self, widget, data)

		if self._enable_media_preview:
			self._handle_cursor_change()

	def _control_lost_focus(self, widget, data=None):
		"""Handle control loosing focus"""
		ItemList._control_lost_focus(self, widget, data)

		if self._enable_media_preview:
			self._thumbnail_view.hide()

	def _handle_cursor_change(self, widget=None, data=None):
		"""Handle cursor change"""
		if not self._enable_media_preview \
		or not self._item_list.has_focus(): return

		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		# we need selection for this
		if iter_ is None: return

		is_dir = list_.get_value(iter_, Column.IS_DIR)
		is_parent = list_.get_value(iter_, Column.IS_PARENT_DIR)

		# create URI from item name and protocol
		file_name = self._get_selection(relative=False)
		protocol = self.get_provider().protocols[0]
		uri = '{0}://{1}'.format(protocol, urllib.quote(file_name)) if not is_parent else None

		# show preview if thumbnail exists
		if not is_dir and not is_parent \
		and self.get_provider().exists(file_name) \
		and self._thumbnail_view.can_have_thumbnail(uri):
			# get position of popup menu, we use these coordinates to show thumbnail
			position = self._get_popup_menu_position()
			column_width = self._columns[0].get_width()

			self._thumbnail_view.show_thumbnail(uri)
			self._thumbnail_view.move(position[0] + column_width, position[1])
			self._thumbnail_view.show()

		else:
			# hide preview if item thumbnail is not available
			self._thumbnail_view.hide()

	def _execute_selected_item(self, widget=None, data=None):
		"""Execute/Open selected item/directory"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		# we need selection for this
		if iter_ is None: return

		is_dir = list_.get_value(iter_, Column.IS_DIR)
		is_parent = list_.get_value(iter_, Column.IS_PARENT_DIR)

		if is_dir:
			# selected item is directory, we need to change path
			if is_parent:
				# call specialized change path method
				self._parent_directory(widget, data)

			else:
				# just change path
				name = list_.get_value(iter_, Column.NAME)
				self.change_path(os.path.join(self.path, name))

		elif self.get_provider().is_local:
			# selected item is just a file, execute it
			selected_file = self._get_selection()
			self._parent.associations_manager.execute_file(selected_file)

		return True  # to prevent command or quick search in single key bindings

	def _open_in_new_tab(self, widget=None, data=None):
		"""Open selected directory in new tab"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		name = list_.get_value(iter_, Column.NAME)
		is_dir = list_.get_value(iter_, Column.IS_DIR)

		if is_dir:
			self._parent.create_tab(
							self._notebook,
							self.__class__,
							os.path.join(self.path, name)
						)

		return True

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
				# set this item to be focused on add
				self._item_to_focus = response[1]

				# try to create directories
				self.get_provider().create_directory(response[1], mode, relative_to=self.path)

				# add directory manually to the list in case
				# where directory monitoring is not supported
				if self._fs_monitor is None:
					show_hidden = self._parent.options.getboolean('main', 'show_hidden')
					self._add_item(response[1], show_hidden)

			except OSError as error:
				# error creating, report to user
				dialog = gtk.MessageDialog(
										self._parent,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										_(
											"There was an error creating directory. "
											"Make sure you have enough permissions. "
										) + "\n\n{0}".format(error)
									)
				dialog.run()
				dialog.destroy()

	def _create_file(self, widget=None, data=None):
		"""Prompt user and create empty file"""
		dialog = FileCreateDialog(self._parent)
		provider = self.get_provider()

		# get response
		response = dialog.get_response()
		mode = dialog.get_mode()
		edit_after = dialog.get_edit_file()
		template = dialog.get_template_file()

		# release dialog
		dialog.destroy()

		# create dialog
		if response[0] == gtk.RESPONSE_OK:
			try:
				# try to create file
				if provider.is_file(os.path.join(self.path, response[1])):
					raise OSError(_("File already exists: {0}").format(response[1]))

				if provider.is_dir(os.path.join(self.path, response[1])):
					raise OSError(_("Directory with same name exists: {0}").format(response[1]))

				# set this item to be focused on add
				self._item_to_focus = response[1]

				# create file
				provider.create_file(response[1], mode=mode, relative_to=self.path)

				# add file manually to the list in case
				# where directory monitoring is not supported
				if self._fs_monitor is None:
					show_hidden = self._parent.options.getboolean('main', 'show_hidden')
					self._add_item(response[1], show_hidden)

				# create file from template
				if template is not None:
					with open(template, 'rb') as raw_file:
						data = raw_file.read()

					new_file = provider.get_file_handle(response[1], 'wb', relative_to=self.path)
					new_file.truncate()
					new_file.write(data)
					new_file.close()

				# if specified, edit file after creating it
				if edit_after:
					self._edit_filename(response[1])

			except OSError as error:
				# error creating, report to user
				dialog = gtk.MessageDialog(
										self._parent,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										_(
											"There was an error creating file. "
											"Make sure you have enough permissions."
										) + "\n\n{0}".format(error)
										)
				dialog.run()
				dialog.destroy()

	def _delete_files(self, widget=None, data=None):
		"""Delete selected files"""
		list_ = self._get_selection_list()
		if list_ is None: return

		dialog = gtk.MessageDialog(
								self._parent,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_QUESTION,
								gtk.BUTTONS_YES_NO,
								ngettext(
									"You are about to remove {0} item.\n"
									"Are you sure about this?",
									"You are about to remove {0} items.\n"
									"Are you sure about this?",
									len(list_)
								).format(len(list_))
							)
		result = dialog.run()
		dialog.destroy()

		if result == gtk.RESPONSE_YES:
			# if user is sure about removal create operation
			operation = DeleteOperation(
									self._parent,
									self.get_provider()
								)
			operation.start()

	def _copy_files(self, widget=None, data=None):
		"""Copy selected files"""
		list_ = self._get_selection_list()
		if list_ is None: return

		dialog = CopyDialog(
						self._parent,
						self.get_provider(),
						self._get_other_provider().get_path()
						)
		result = dialog.get_response()

		if result[0] == gtk.RESPONSE_OK:
			# if user confirmed copying
			operation = CopyOperation(
									self._parent,
									self.get_provider(),
									self._get_other_provider(),
									result[1]  # options from dialog
									)
			operation.start()

	def _move_files(self, widget=None, data=None):
		"""Move selected files"""
		if self._get_selection_list() is None: return

		dialog = MoveDialog(
						self._parent,
						self.get_provider(),
						self._get_other_provider().get_path()
						)
		result = dialog.get_response()

		if result[0] == gtk.RESPONSE_OK:
			# if user confirmed copying
			operation = MoveOperation(
									self._parent,
									self.get_provider(),
									self._get_other_provider(),
									result[1]  # options from dialog
								)
			operation.start()

	def _rename_file(self, widget=None, data=None):
		"""Rename selected item"""
		selection = os.path.basename(self._get_selection())

		dialog = RenameDialog(self._parent, selection)
		result = dialog.get_response()

		if result[0] == gtk.RESPONSE_OK:
			if not self.get_provider().exists(result[1], relative_to=self.path):
				try:
					# rename selected item
					self.get_provider().rename_path(selection, result[1])

					# mark item for selection after rename
					self._item_to_focus = result[1]

				except IOError as error:
					# problem renaming item
					dialog = gtk.MessageDialog(
											self,
											gtk.DIALOG_DESTROY_WITH_PARENT,
											gtk.MESSAGE_ERROR,
											gtk.BUTTONS_OK,
											_(
												"Error renaming specified item. Make sure "
												"you have enough permissions."
											) +	"\n\n{0}".format(error)
										)
					dialog.run()
					dialog.destroy()

			else:
				# file/directory already exists
				dialog = gtk.MessageDialog(
										self._parent,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										_(
											"File or directory with specified name already "
											"exists in current directory. Item could not "
											"be renamed."
										)
									)
				dialog.run()
				dialog.destroy()

	def _send_to(self, widget=None, data=None):
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

	def _item_properties(self, widget=None, data=None):
		"""Show file/directory properties"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		is_parent = list_.get_value(iter_, Column.IS_PARENT_DIR)

		if not is_parent:
			window = PropertiesWindow(
									self._parent,
									self.get_provider(),
									self._get_selection()
								)

			window.show()

		return True

	def _get_selection(self, relative=False):
		"""Return item with path under cursor"""
		result = None
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		is_parent = list_.get_value(iter_, Column.IS_PARENT_DIR)

		if not is_parent:
			item = list_.get_value(iter_, Column.NAME)
			result = item if relative else os.path.join(self.path, item)

		return result

	def _get_selection_list(self, under_cursor=False, relative=False):
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
				if row[Column.COLOR] is not None:
					value = row[Column.NAME] if relative else os.path.join(self.path, row[Column.NAME])
					result.append(value)

		if len(result) is 0:
			selection = self._get_selection(relative=relative)
			if selection is None:
				result = None
			else:
				result.append(selection)

		return result

	def _prepare_popup_menu(self):
		"""Populate pop-up menu items"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		is_dir = list_.get_value(iter_, Column.IS_DIR)
		is_parent = list_.get_value(iter_, Column.IS_PARENT_DIR)

		# get selected item
		filename = self._get_selection()

		# call parent method which removes existing menu items
		ItemList._prepare_popup_menu(self)

		if not is_dir:
			# get associated programs
			mime_type = gnomevfs.get_mime_type(filename)
			program_list = self._parent.menu_manager.get_items_for_type(mime_type, self._get_selection_list())

			# create open with menu
			for menu_item in program_list:
				self._open_with_menu.append(menu_item)

		# disable/enable items
		has_items = len(self._open_with_menu.get_children()) > 0
		self._open_with_item.set_sensitive(has_items and self.get_provider().is_local)
		self._open_new_tab_item.set_visible(is_dir)
		self._cut_item.set_sensitive(not is_parent)
		self._copy_item.set_sensitive(not is_parent)
		self._paste_item.set_sensitive(self._parent.is_clipboard_item_list())
		self._send_to_item.set_sensitive(self.get_provider().is_local and not is_parent)
		self._rename_item.set_sensitive(not is_parent)
		self._delete_item.set_sensitive(not is_parent)
		self._properties_item.set_sensitive(not is_parent)

	def _get_popup_menu_position(self, menu=None, data=None):
		"""Positions menu properly for given row"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		# grab cell and tree rectangles
		rect = self._item_list.get_cell_area(list_.get_path(iter_), self._columns[0])
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

		self._apply_sort_function()

	def _apply_sort_function(self):
		"""Apply sort settings"""
		# set sort indicator only on one column
		for column in self._item_list.get_columns():
			selected = column is self._sort_column_widget
			column.set_sort_indicator(selected)

		# apply sorting function
		order = [gtk.SORT_DESCENDING, gtk.SORT_ASCENDING][self._sort_ascending]
		self._sort_column_widget.set_sort_order(order)

		self._store.set_sort_func(self._sort_column, self._sort_list)
		self._store.set_sort_column_id(self._sort_column, order)

		# set focus to the list, we don't need it on column
		self._item_list.grab_focus()

	def _sort_list(self, list_, iter1, iter2, data=None):
		"""Compare two items for sorting process"""
		reverse = (1, -1)[self._sort_ascending]

		value1 = list_.get_value(iter1, self._sort_column)
		value2 = list_.get_value(iter2, self._sort_column)

		if not self._sort_sensitive and self._sort_column in (Column.NAME, Column.EXTENSION):
			value1 = value1.lower()

			if value2 is not None:  # make sure we have extension to make lowercase
				value2 = value2.lower()

		item1 = (
				reverse * list_.get_value(iter1, Column.IS_PARENT_DIR),
				reverse * list_.get_value(iter1, Column.IS_DIR),
				value1
				)

		item2 = (
				reverse * list_.get_value(iter2, Column.IS_PARENT_DIR),
				reverse * list_.get_value(iter2, Column.IS_DIR),
				value2
				)

		return cmp(item1, item2)

	def _clear_list(self):
		"""Clear item list"""
		self._store.clear()

	def _directory_changed(self, monitor, file_, other_file, event):
		"""Callback method fired when contents of directory has been changed"""
		show_hidden = self._parent.options.getboolean('main', 'show_hidden')

		# node created
		if event is gio.FILE_MONITOR_EVENT_CREATED:
			# temporarily fix problem with duplicating items when file was saved with GIO
			if self._find_iter_by_name(file_.get_basename()) is None:
				self._add_item(file_.get_basename(), show_hidden)

			else:
				self._update_item_details_by_name(file_.get_basename())

		# node deleted
		elif event is gio.FILE_MONITOR_EVENT_DELETED:
			self._delete_item_by_name(file_.get_basename())

		# node changed
		elif event is gio.FILE_MONITOR_EVENT_CHANGED:
			self._update_item_details_by_name(file_.get_basename())

		self._change_title_text()
		self._update_status_with_statistis()

	def _toggle_selection(self, widget, data=None, advance=True):
		"""Toggle item selection"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		is_dir = list_.get_value(iter_, Column.IS_DIR)
		is_parent = list_.get_value(iter_, Column.IS_PARENT_DIR)
		size = list_.get_value(iter_, Column.SIZE)

		if not is_parent:
			# get current status of iter
			selected = list_.get_value(iter_, Column.COLOR) is not None

			if is_dir:
				self._dirs['selected'] += [1, -1][selected]
			else:
				self._files['selected'] += [1, -1][selected]
				self._size['selected'] += [1, -1][selected] * size

			# toggle selection
			selected = not selected

			value = (None, 'red')[selected]
			image = (None, self._pixbuf_selection)[selected]
			list_.set_value(iter_, Column.COLOR, value)
			list_.set_value(iter_, Column.SELECTED, image)

		# update status bar
		ItemList._toggle_selection(self, widget, data, advance)
		self._update_status_with_statistis()

		if advance:
			# select next item in the list
			next_iter = list_.iter_next(iter_)
			if next_iter is not None:
				path = list_.get_path(next_iter)
				self._item_list.set_cursor(path)
				self._item_list.scroll_to_cell(path)

	def _select_range(self, start_path, end_path):
		"""Set items in range to status oposite from frist item in selection"""
		if len(self._store) == 1:  # exit when list doesn't have items
			return

		# get current selection
		start_iter = self._store.get_iter(start_path)
		new_status = not (self._store.get_value(start_iter, Column.COLOR) is not None)

		# swap paths if selecting from bottom up
		if start_path[0] > end_path[0]:
			start_path, end_path = end_path, start_path

		# make sure start path is not parent
		if start_path[0] == 0:
			start_path = (1, )

		# values to be set in columns
		value = (None, 'red')[new_status]
		image = (None, self._pixbuf_selection)[new_status]

		for index in xrange(start_path[0], end_path[0] + 1):
			current_iter = self._store.get_iter((index,))

			# get current iter information
			size = self._store.get_value(current_iter, Column.SIZE)
			is_dir = self._store.get_value(current_iter, Column.IS_DIR)
			status = self._store.get_value(current_iter, Column.COLOR) is not None

			# set selection
			self._store.set_value(current_iter, Column.COLOR, value)
			self._store.set_value(current_iter, Column.SELECTED, image)

			# modify counters only when status is changed
			if new_status is not status:
				if is_dir:
					self._dirs['selected'] += [1, -1][status]
				else:
					self._files['selected'] += [1, -1][status]
					self._size['selected'] += [1, -1][status] * size

		# call parent method
		ItemList._select_range(self, start_path, end_path)

		# update status
		self._update_status_with_statistis()

	def _edit_selected(self, widget=None, data=None):
		"""Abstract method to edit currently selected item"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		is_dir = list_.get_value(iter_, Column.IS_DIR)

		if not is_dir and self.get_provider().is_local:
			self._edit_filename(list_.get_value(iter_, Column.NAME))

		return True

	def _edit_filename(self, filename):
		"""Open editor with specified filename and current path"""
		default_editor = self._parent.options.get('main', 'default_editor')
		filename = os.path.join(self.path, filename)
		command = default_editor.format(filename)

		# if we shouldn't wait for editor, add & at the end of command
		if not self._parent.options.getboolean('main', 'wait_for_editor'):
			command = '{0} &'.format(command)

		os.system(command)

	def _find_iter_by_name(self, name):
		""" Find and return item by name"""
		result = None

		for row in self._store:
			if row[Column.NAME] == name:
				result = row.iter
				break

		return result

	def _add_item(self, filename, show_hidden=False):
		"""Add item to the list"""
		file_size = 0
		file_mode = 0
		file_date = 0

		result = None
		can_add = not (filename[0] == '.' and not show_hidden)
		provider = self.get_provider()

		if can_add:
			file_stat = provider.get_stat(filename, relative_to=self.path)

			file_size = file_stat.size
			file_mode = file_stat.mode
			file_date = file_stat.time_modify
			is_dir = file_stat.type is FileType.DIRECTORY

			# directory
			if file_stat.type is FileType.DIRECTORY:
				self._dirs['count'] += 1
				icon = 'folder'

			# regular file
			elif file_stat.type is FileType.REGULAR:
				self._files['count'] += 1
				self._size['total'] += file_size
				icon = self._parent.icon_manager.get_icon_for_file(filename)

			# invalid links or files
			elif file_stat.type is FileType.INVALID:
				self._files['count'] += 1
				icon = 'image-missing'

			# add item to the list
			try:
				time_format = self._parent.options.get('main', 'time_format')

				# don't allow extension splitting on directories
				file_info = (filename, '') if is_dir else os.path.splitext(filename)

				formated_file_mode = oct(file_mode)
				formated_file_date = time.strftime(time_format, time.localtime(file_date))

				if not is_dir:
					# item is a file
					if self._human_readable:
						formated_file_size = common.format_size(file_size)

					else:
						formated_file_size = locale.format('%d', file_size, True)


				else:
					# item is a directory
					formated_file_size = '<DIR>'

				props = (
						filename,
						file_info[0],
						file_info[1][1:],
						file_size,
						formated_file_size,
						file_mode,
						formated_file_mode,
						file_date,
						formated_file_date,
						is_dir,
						False,
						None,
						icon,
						None
					)

				result = self._store.append(props)

				# focus specified item
				if self._item_to_focus == filename:
					path = self._store.get_path(result)

					# set cursor position and scroll ti make it visible
					self._item_list.set_cursor(path)
					self._item_list.scroll_to_cell(path)

					# reset local variable
					self._item_to_focus = None

			except Exception as error:
				print 'Error: {0} - {1}'.format(filename, str(error))

		return result

	def _delete_item_by_name(self, name):
		"""Removes item with 'name' from the list"""
		selection = self._item_list.get_selection()
		list_, selected_iter = selection.get_selected()

		# get currently selected name
		selected_name = None
		if selected_iter is not None:
			selected_name = list_.get_value(selected_iter, Column.NAME)

		# find iter matching 'name'
		found_iter = self._find_iter_by_name(name)

		if found_iter is not None:
			iter_name = self._store.get_value(found_iter, Column.NAME)

			# if currently hovered item was removed
			if iter_name == selected_name:
				next_iter = list_.iter_next(selected_iter)

				if next_iter is None:  # make sure we select something
					next_iter = list_[-2].iter

				self._item_list.set_cursor(list_.get_path(next_iter))

			if list_.get_value(found_iter, Column.IS_DIR):
				self._dirs['count'] -= 1

				# update selected counters
				if list_.get_value(found_iter, Column.SELECTED) is not None:
					self._dirs['selected'] -= 1

			else:
				self._files['count'] -= 1
				self._size['total'] -= list_.get_value(found_iter, Column.SIZE)

				# update selected counters
				if list_.get_value(found_iter, Column.SELECTED) is not None:
					self._files['selected'] -= 1
					self._size['selected'] -= list_.get_value(found_iter, Column.SIZE)

			# remove
			self._store.remove(found_iter)

	def _update_item_details_by_name(self, name):
		"""Update item details (size, time, etc.) on changed event"""
		found_iter = self._find_iter_by_name(name)
		provider = self.get_provider()

		if found_iter is not None:
			# get node stats
			is_dir = self._store.get_value(found_iter, Column.IS_DIR)
			file_stat = provider.get_stat(name, relative_to=self.path)

			file_size = file_stat.size
			file_mode = file_stat.mode
			file_date = file_stat.time_modify

			# time_format values
			time_format = self._parent.options.get('main', 'time_format')

			formated_file_size = locale.format('%d', file_size, True) if not is_dir else '<DIR>'
			formated_file_mode = oct(file_mode)
			formated_file_date = time.strftime(time_format, time.localtime(file_date))

			# update list store
			self._store.set_value(found_iter, Column.SIZE, file_size)
			self._store.set_value(found_iter, Column.MODE, file_mode)
			self._store.set_value(found_iter, Column.TIME, file_date)
			self._store.set_value(found_iter, Column.FORMATED_SIZE, formated_file_size)
			self._store.set_value(found_iter, Column.FORMATED_MODE, formated_file_mode)
			self._store.set_value(found_iter, Column.FORMATED_TIME, formated_file_date)

	def _change_title_text(self, text=None):
		"""Change title label text and add free space display"""
		if text is None: text = self.path
		stat = os.statvfs(self.path)

		space_free = common.format_size(stat.f_bsize * stat.f_bavail)
		space_total = common.format_size(stat.f_bsize * stat.f_blocks)

		self._title_bar.set_title(text)
		self._title_bar.set_subtitle(
									'{2} {0} - {3} {1}'.format(
															space_free,
															space_total,
															_('Free:'),
															_('Total:')
														)
								)

	def _drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
		"""Handle dropping files on file list"""
		list_ = selection_data.data.splitlines(False)

		# prepare data for copying
		protocol, path = list_[0].split('://', 1)
		list_ = [urllib.unquote(item.split('://')[1]) for item in list_]

		if os.path.dirname(path) != self.path:
			# handle data
			if drag_context.action in (gtk.gdk.ACTION_COPY, gtk.gdk.ACTION_MOVE):
				# handle copy and move operations
				operation = {
							gtk.gdk.ACTION_COPY: 'copy',
							gtk.gdk.ACTION_MOVE: 'move'
						}

				result = self._handle_external_data(
												operation[drag_context.action],
												protocol,
												list_
											)

			elif drag_context.action is gtk.gdk.ACTION_LINK:
				# handle linking
				# TODO: Finish linking code!
				result = False

			# notify source application about operation outcome
			drag_context.finish(result, False, timestamp)

		else:
			# notify user that he's trying to drag and drop items in same directory
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_WARNING,
									gtk.BUTTONS_OK,
									_(
										'Drag and drop functionality can not '
										'be used if source and destination are same!'
									)
								)
			dialog.run()
			dialog.destroy()

			# problem with paths, let source application know that
			drag_context.finish(False, False, timestamp)

	def _drag_data_get(self, widget, drag_context, selection_data, info, time):
		"""Handle data request from destination widget"""
		protocol = self.get_provider().protocols[0]

		selection = []
		for file_ in self._get_selection_list():
			selection.append('{0}://{1}'.format(protocol, urllib.quote(file_)))

		selection_data.set(selection_data.target, 8, '\n'.join(selection))
		return True

	def _get_supported_drag_types(self):
		"""Return list of supported data for drag'n'drop events"""
		return [
				('text/uri-list', 0, 0),
			]

	def _get_supported_drag_actions(self):
		"""Return integer representing supported drag'n'drop actions"""
		return gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE  # | gtk.gdk.ACTION_LINK # add later

	def change_path(self, path=None, selected=None):
		"""Change file list path"""
		# cancel current directory monitor
		if gio is not None and self._fs_monitor is not None:
			self._fs_monitor.cancel()

		# clear list
		self._clear_list()

		# hide thumbnail
		if self._enable_media_preview:
			self._thumbnail_view.hide()

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

		show_hidden = self._parent.options.getboolean('main', 'show_hidden')

		# disconnect store from widget to speed up the process
		# disabled: not required atm
#		self._item_list.set_model(None)
#		self._store.set_default_sort_func(None)

		self._dirs['count'] = 0
		self._dirs['selected'] = 0
		self._files['count'] = 0
		self._files['selected'] = 0
		self._size['total'] = 0L
		self._size['selected'] = 0

		# assign item for selection
		self._item_to_focus = selected

		# populate list
		try:
			for filename in self.get_provider().list_dir(self.path):
				self._add_item(filename, show_hidden)

			# if no errors occurred during path change,
			# call parent method which handles history
			ItemList.change_path(self, path)

		except OSError as error:
			# problem with listing directory, ask user what to do
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_YES_NO,
									_(
										"Error changing working directory. "
										"\n\n{0}\n\nWould you like to retry?"
									).format(error)
								)
			result = dialog.run()
			dialog.destroy()

			if result == gtk.RESPONSE_YES:
				self.change_path(path)

			else:
				self.change_path(self.history[0])

			return

		# update status bar
		self._update_status_with_statistis()

		# add parent option for parent directory
		self._store.insert(0, (
							os.path.pardir,
							os.path.pardir,
							'',
							-2,
							'<DIR>',
							-1,
							'',
							-1,
							'',
							True,
							True,
							None,
							'up',
							None
						))

		# restore model and sort function
		# disabled: not required atm
#		self._item_list.set_model(self._store)
#		self._set_sort_function(self._sort_column_widget)

		# if no item was specified, select first one
		if selected is None:
			path = self._store.get_path(self._store.get_iter_first())
			self._item_list.set_cursor(path)
			self._item_list.scroll_to_cell(path)

		# create file monitor
		if gio is not None and self.get_provider().is_local:
			try:
				self._fs_monitor = gio.File(self.path).monitor_directory()
				self._fs_monitor.connect('changed', self._directory_changed)

			except gio.Error:
				# monitoring is probably not supported by the backend
				self._fs_monitor = None

	def select_all(self, pattern=None, exclude_list=None):
		"""Select all items matching pattern """
		if pattern is None:
			pattern = "*"

		if exclude_list is None:
			exclude_list = ()

		dirs = 0
		files = 0
		size = 0L

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] \
			and fnmatch.fnmatch(row[Column.NAME], pattern) \
			and row[Column.NAME] not in exclude_list:
				# select item that matched out criteria
				row[Column.COLOR] = self._parent.options.get('main', 'selection_color')
				row[Column.SELECTED] = self._pixbuf_selection

			elif len(exclude_list) > 0:
				# if out exclude list has items, we need to deselect them
				row[Column.COLOR] = None
				row[Column.SELECTED] = None

			# update dir/file count
			if row[Column.COLOR] is not None:
				if row[Column.IS_DIR]:
					dirs += 1
				else:
					files += 1
					size += row[Column.SIZE]

		self._dirs['selected'] = dirs
		self._files['selected'] = files
		self._size['selected'] = size

		# update status bar
		ItemList.select_all(self, pattern, exclude_list)
		self._update_status_with_statistis()

	def unselect_all(self, pattern=None):
		"""Unselect items matching the pattern"""
		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0
		size = 0L

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] and fnmatch.fnmatch(row[Column.NAME], pattern):
				row[Column.COLOR] = None
				row[Column.SELECTED] = None

			# update dir/file count
			if row[Column.COLOR] is not None:
				if row[Column.IS_DIR]:
					dirs += 1
				else:
					files += 1
					size += row[Column.SIZE]

		self._dirs['selected'] = dirs
		self._files['selected'] = files
		self._size['selected'] = size

		# update status bar
		ItemList.select_all(self, pattern)
		self._update_status_with_statistis();

	def invert_selection(self, pattern=None):
		"""Invert selection matching the pattern"""
		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0
		size = 0L

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] and fnmatch.fnmatch(row[Column.NAME], pattern):
				if row[Column.COLOR] is None:
					row[Column.COLOR] = 'red'
					row[Column.SELECTED] = self._pixbuf_selection
				else:
					row[Column.COLOR] = None
					row[Column.SELECTED] = None

			# update dir/file count
			if row[Column.COLOR] is not None:
				if row[Column.IS_DIR]:
					dirs += 1
				else:
					files += 1
					size += row[Column.SIZE]

		self._dirs['selected'] = dirs
		self._files['selected'] = files
		self._size['selected'] = size

		# update status bar
		ItemList.select_all(self, pattern)
		self._update_status_with_statistis();

	def refresh_file_list(self, widget=None, data=None):
		"""Reload file list_ for current directory"""
		selection = self._item_list.get_selection()
		list_, iter_ = selection.get_selected()

		f_name = list_.get_value(iter_, Column.NAME) if iter_ is not None else None
		self.change_path(self.path, f_name)

		return True

	def update_column_size(self, name):
		"""Update column size with global value"""
		column = filter(lambda item: item.get_data('name') == name, self._columns)[0]
		width = self._parent.options.getint(
										self.__class__.__name__,
										'size_{0}'.format(name)
									)
		column.set_fixed_width(width)

	def get_provider(self):
		"""Get list provider object"""
		if self._provider is None:
			self._provider = LocalProvider(self)

		return self._provider

	def apply_settings(self):
		"""Apply file list settings"""
		ItemList.apply_settings(self)  # let parent apply its own settings

		# apply row hinting
		row_hinting = self._parent.options.getboolean('main', 'row_hinting')
		self._item_list.set_rules_hint(row_hinting)

		# apply grid lines
		grid_lines = (
					gtk.TREE_VIEW_GRID_LINES_NONE,
					gtk.TREE_VIEW_GRID_LINES_HORIZONTAL,
					gtk.TREE_VIEW_GRID_LINES_VERTICAL,
					gtk.TREE_VIEW_GRID_LINES_BOTH,
				)[self._parent.options.getint('main', 'grid_lines')]
		self._item_list.set_grid_lines(grid_lines)

		# reload file list in order to apply time formatting, hidden files and other
		self.refresh_file_list()

	def apply_media_preview_settings(self):
		"""Apply settings related to image_preview"""
		self._enable_media_preview = self._parent.options.getboolean('main', 'media_preview')

		if self._enable_media_preview:
			# force showing thumbnail
			self._handle_cursor_change()

		else:
			# hide thumbnail
			self._thumbnail_view.hide()
