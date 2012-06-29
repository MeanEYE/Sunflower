import os
import gtk
import time
import locale
import user
import fnmatch
import urllib
import urlparse
import common

from plugin_base.monitor import MonitorSignals, MonitorError
from local_provider import LocalProvider
from gio_provider import SambaProvider, FtpProvider
from gio_extension import SambaExtension
from operation import DeleteOperation, CopyOperation, MoveOperation
from gui.input_dialog import FileCreateDialog, DirectoryCreateDialog
from gui.input_dialog import CopyDialog, MoveDialog, RenameDialog
from gui.input_dialog import ApplicationSelectDialog
from gui.properties_window import PropertiesWindow
from widgets.thumbnail_view import ThumbnailView
from threading import Thread, Event
from plugin_base.item_list import ItemList
from plugin_base.provider import FileType, Mode as FileMode


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_class('file_list', _('Local file list'), FileList)

	# register providers
	application.register_provider(LocalProvider)
	application.register_provider(SambaProvider)
	application.register_provider(FtpProvider)

	# register mount manager extension
	application.register_mount_manager_extension(SambaExtension)


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

		self.scheme = 'file'

		# event object controlling path change thread
		self._thread_active = Event()

		# preload variables
		self._preload_count = 0
		self._preload_size = 0

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

		# register columns
		self._columns = (col_name, col_extension, col_size, col_mode, col_date)

		# set default column sizes for file list
		self._columns_size = (200, 50, 70, 50, 90)
		self._create_default_column_sizes()

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

		# set column order
		self._reorder_columns()

		# release signal block
		self._item_list.handler_unblock_by_func(self._column_changed)

		# set list behavior
		self._item_list.set_headers_clickable(True)
		self._item_list.set_enable_search(True)
		self._item_list.set_search_column(Column.NAME)

		# set row hinting
		row_hinting = self._parent.options.section('item_list').get('row_hinting')
		self._item_list.set_rules_hint(row_hinting)

		# set grid lines
		grid_lines = (
					gtk.TREE_VIEW_GRID_LINES_NONE,
					gtk.TREE_VIEW_GRID_LINES_HORIZONTAL,
					gtk.TREE_VIEW_GRID_LINES_VERTICAL,
					gtk.TREE_VIEW_GRID_LINES_BOTH,
				)[self._parent.options.section('item_list').get('grid_lines')]
		self._item_list.set_grid_lines(grid_lines)

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
		self._enable_media_preview = self._parent.options.get('media_preview')

		# variable that is used to set focus on newly created files and dirs
		self._item_to_focus = None

		# cache configuration locally
		self._time_format = self._parent.options.section('item_list').get('time_format')
		self._mode_format = self._parent.options.section('item_list').get('mode_format')

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
		item_list, selected_iter = selection.get_selected()

		# we need selection for this
		if selected_iter is None: return

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		# create URI from item name and protocol
		# TODO: Use URLLIB for creating URI instead of formatting a string
		file_name = self._get_selection(relative=False)
		protocol = self.get_provider().protocol
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
		"""Execute/Open selected item"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# we need selection for this
		if selected_iter is None: return

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		if is_dir:
			# selected item is directory, we need to change path
			if is_parent:
				# call specialized change path method
				self._parent_directory(widget, data)

			else:
				# just change path
				name = item_list.get_value(selected_iter, Column.NAME)
				self.change_path(os.path.join(self.path, name))

		elif self.get_provider().is_local:
			# selected item is just a file, execute it
			selected_file = self._get_selection()
			self._parent.associations_manager.execute_file(selected_file)

		return True  # to prevent command or quick search in single key bindings

	def _execute_with_application(self, widget=None, data=None):
		"""Execute/Open selected item with application user selects from the list"""
		selection = self._get_selection_list()

		if selection is not None and len(selection) > 0:
			dialog = ApplicationSelectDialog(self._parent, selection[0])
			response = dialog.get_response()

			if response[0] == gtk.RESPONSE_OK:
				self._parent.associations_manager.open_file(
														selection,
														exec_command=response[2]
													)

		else:
			# invalid selection, warn user
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_WARNING,
									gtk.BUTTONS_OK,
									_('Invalid selection!')
								)
			dialog.run()
			dialog.destroy()

		return True

	def _open_in_new_tab(self, widget=None, data=None):
		"""Open selected directory in new tab"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		name = item_list.get_value(selected_iter, Column.NAME)
		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)

		if is_dir:
			self._parent.create_tab(
							self._notebook,
							self.__class__,
							os.path.join(self.path, name)
						)

		return True

	def _open_directory(self, widget=None, data=None):
		"""Open selected directory"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# we need selection for this
		if selected_iter is None: return

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		if is_dir:
			# selected item is directory, we need to change path
			if is_parent:
				# call specialized change path method
				self._parent_directory(widget, data)

			else:
				# just change path
				name = item_list.get_value(selected_iter, Column.NAME)
				self.change_path(os.path.join(self.path, name))

		return True

	def _create_directory(self, widget=None, data=None):
		"""Prompt user and create directory"""
		dialog = DirectoryCreateDialog(self._parent)

		# get response
		response = dialog.get_response()
		mode = dialog.get_mode()

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
					self._add_item(response[1])

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

		return True

	def _create_file(self, widget=None, data=None):
		"""Prompt user and create empty file"""
		dialog = FileCreateDialog(self._parent)
		provider = self.get_provider()

		# get response
		response = dialog.get_response()
		mode = dialog.get_mode()
		edit_after = dialog.get_edit_file()
		template = dialog.get_template_file()

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
					self._add_item(response[1])

				# create file from template
				if template is not None:
					with open(template, 'rb') as raw_file:
						data = raw_file.read()

					new_file = provider.get_file_handle(response[1], FileMode.WRITE, relative_to=self.path)
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

		return True

	def _delete_files(self, widget=None, data=None):
		"""Delete selected files"""
		item_list = self._get_selection_list()
		if item_list is None: return

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
									len(item_list)
								).format(len(item_list))
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

		return True

	def _copy_files(self, widget=None, data=None):
		"""Copy selected files"""
		item_list = self._get_selection_list()
		if item_list is None: return

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

		return True

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

		return True

	def _rename_file(self, widget=None, data=None):
		"""Rename selected item"""
		selection = self._get_selection()

		# return if there is no selection
		if selection is None:
			return

		# get base name from selection
		selection = os.path.basename(selection)

		dialog = RenameDialog(self._parent, selection)
		result = dialog.get_response()

		if result[0] == gtk.RESPONSE_OK:
			if not self.get_provider().exists(result[1], relative_to=self.path):
				try:
					# rename selected item
					self.get_provider().rename_path(selection, result[1], relative_to=self.path)

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

		return True

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
		item_list, selected_iter = selection.get_selected()

		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

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
		item_list, selected_iter = selection.get_selected()

		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		if not is_parent:
			item = item_list.get_value(selected_iter, Column.NAME)
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
		item_list, selected_iter = selection.get_selected()

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		# get selected item
		filename = self._get_selection()

		# call parent method which removes existing menu items
		ItemList._prepare_popup_menu(self)

		if not is_dir:
			# get associated programs
			selection = self._get_selection_list()
			mime_type = self._parent.associations_manager.get_mime_type(filename)
			program_list = self._parent.menu_manager.get_items_for_type(mime_type, selection)
			custom_list = self._parent.menu_manager.get_custom_items_for_type(mime_type, selection)

			# create open with menu
			for menu_item in program_list:
				self._open_with_menu.append(menu_item)

			# add separator if there are other menu items
			if len(program_list) > 0:
				separator = gtk.SeparatorMenuItem()
				separator.show()
				self._open_with_menu.append(separator)

			# add custom menu items if needed
			if len(custom_list) > 0:
				for menu_item in custom_list:
					self._open_with_menu.append(menu_item)

				# add separator if needed
				if len(program_list) > 0:
					separator = gtk.SeparatorMenuItem()
					separator.show()
					self._open_with_menu.append(separator)

			# create an option for opening selection with custom command
			open_with_other = gtk.MenuItem(_('Other application...'))
			open_with_other.connect('activate', self._execute_with_application)
			open_with_other.show()

			self._open_with_menu.append(open_with_other)

		# disable/enable items
		self._open_with_item.set_sensitive(self.get_provider().is_local and not is_dir)
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
		item_list, selected_iter = selection.get_selected()

		# grab cell and tree rectangles
		rect = self._item_list.get_cell_area(item_list.get_path(selected_iter), self._columns[0])
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

	def _sort_list(self, item_list, iter1, iter2, data=None):
		"""Compare two items for sorting process"""
		reverse = (1, -1)[self._sort_ascending]

		value1 = item_list.get_value(iter1, self._sort_column)
		value2 = item_list.get_value(iter2, self._sort_column)

		if not self._sort_sensitive and self._sort_column in (Column.NAME, Column.EXTENSION):
			value1 = value1.lower()

			if value2 is not None:  # make sure we have extension to make lowercase
				value2 = value2.lower()

		item1 = (
				reverse * item_list.get_value(iter1, Column.IS_PARENT_DIR),
				reverse * item_list.get_value(iter1, Column.IS_DIR),
				value1
				)

		item2 = (
				reverse * item_list.get_value(iter2, Column.IS_PARENT_DIR),
				reverse * item_list.get_value(iter2, Column.IS_DIR),
				value2
				)

		return cmp(item1, item2)

	def _clear_list(self):
		"""Clear item list"""
		self._store.clear()

	def _directory_changed(self, monitor, event, path, other_path):
		"""Callback method fired when contents of directory has been changed"""
		show_hidden = self._parent.options.section('item_list').get('show_hidden')

		# node created
		if event is MonitorSignals.CREATED:
			# temporarily fix problem with duplicating items when file was saved with GIO
			if self._find_iter_by_name(path) is None:
				if (not show_hidden) and (path[0] == '.' or path[-1] == '~'):
					return

				self._add_item(path)

			else:
				self._update_item_details_by_name(path)

		# node deleted
		elif event is MonitorSignals.DELETED:
			self._delete_item_by_name(path)

		# node changed
		elif event is MonitorSignals.CHANGED:
			self._update_item_details_by_name(path)

		# attributes changes
		elif event is MonitorSignals.ATTRIBUTE_CHANGED:
			self._update_item_attributes_by_name(path)

		self._change_title_text()
		self._update_status_with_statistis()

		return True

	def _toggle_selection(self, widget, data=None, advance=True):
		"""Toggle item selection"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)
		size = item_list.get_value(selected_iter, Column.SIZE)

		if not is_parent:
			# get current status of iter
			selected = item_list.get_value(selected_iter, Column.COLOR) is not None

			if is_dir:
				self._dirs['selected'] += [1, -1][selected]
			else:
				self._files['selected'] += [1, -1][selected]
				self._size['selected'] += [1, -1][selected] * size

			# toggle selection
			selected = not selected

			value = (None, self._selection_color)[selected]
			image = (None, self._pixbuf_selection)[selected]
			item_list.set_value(selected_iter, Column.COLOR, value)
			item_list.set_value(selected_iter, Column.SELECTED, image)

		# update status bar
		ItemList._toggle_selection(self, widget, data, advance)
		self._update_status_with_statistis()

		if advance:
			# select next item in the list
			next_iter = item_list.iter_next(selected_iter)
			if next_iter is not None:
				path = item_list.get_path(next_iter)
				self._item_list.set_cursor(path)
				self._item_list.scroll_to_cell(path)

		return True

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
		value = (None, self._selection_color)[new_status]
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
		item_list, selected_iter = selection.get_selected()

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)

		if not is_dir and self.get_provider().is_local:
			self._edit_filename(item_list.get_value(selected_iter, Column.NAME))

		return True

	def _edit_filename(self, filename):
		"""Open editor with specified filename and current path"""
		section = self._parent.options.section('editor')
		default_editor = section.get('default_editor')
		filename = os.path.join(self.path, filename)
		command = default_editor.format(filename)

		# if we shouldn't wait for editor, add & at the end of command
		if not section.get('wait_for_editor'):
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

	def _add_item(self, filename):
		"""Add item to the list"""
		result = None
		provider = self.get_provider()

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
			# don't allow extension splitting on directories
			file_info = (filename, '') if is_dir else os.path.splitext(filename)

			formated_file_mode = common.format_mode(file_mode, self._mode_format)
			formated_file_date = time.strftime(self._time_format, time.localtime(file_date))

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
		item_list, selected_iter = selection.get_selected()

		# get currently selected name
		selected_name = None
		if selected_iter is not None:
			selected_name = item_list.get_value(selected_iter, Column.NAME)

		# find iter matching 'name'
		found_iter = self._find_iter_by_name(name)

		if found_iter is not None:
			iter_name = self._store.get_value(found_iter, Column.NAME)

			# if currently hovered item was removed
			if iter_name == selected_name:
				next_iter = item_list.iter_next(selected_iter)

				if next_iter is None:  # make sure we select something
					next_iter = item_list[-2].iter

				self._item_list.set_cursor(item_list.get_path(next_iter))

			if item_list.get_value(found_iter, Column.IS_DIR):
				self._dirs['count'] -= 1

				# update selected counters
				if item_list.get_value(found_iter, Column.SELECTED) is not None:
					self._dirs['selected'] -= 1

			else:
				self._files['count'] -= 1
				self._size['total'] -= item_list.get_value(found_iter, Column.SIZE)

				# update selected counters
				if item_list.get_value(found_iter, Column.SELECTED) is not None:
					self._files['selected'] -= 1
					self._size['selected'] -= item_list.get_value(found_iter, Column.SIZE)

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

			if not is_dir:
				# format file size
				if self._human_readable:
					formated_file_size = common.format_size(file_size)

				else:
					formated_file_size = locale.format('%d', file_size, True)

			else:
				# item is a directory
				formated_file_size = '<DIR>'

			formated_file_mode = common.format_mode(file_mode, self._mode_format)
			formated_file_date = time.strftime(self._time_format, time.localtime(file_date))

			# update list store
			self._store.set_value(found_iter, Column.SIZE, file_size)
			self._store.set_value(found_iter, Column.MODE, file_mode)
			self._store.set_value(found_iter, Column.TIME, file_date)
			self._store.set_value(found_iter, Column.FORMATED_SIZE, formated_file_size)
			self._store.set_value(found_iter, Column.FORMATED_MODE, formated_file_mode)
			self._store.set_value(found_iter, Column.FORMATED_TIME, formated_file_date)

	def _update_item_attributes_by_name(self, name):
		"""Update item attributes column by name"""
		found_iter = self._find_iter_by_name(name)
		provider = self.get_provider()

		if found_iter is not None:
			# get node stats
			file_stat = provider.get_stat(name, relative_to=self.path)

			file_mode = file_stat.mode
			formated_file_mode = common.format_mode(file_mode, self._mode_format)

			self._store.set_value(found_iter, Column.MODE, file_mode)
			self._store.set_value(found_iter, Column.FORMATED_MODE, formated_file_mode)

	def _change_title_text(self, text=None):
		"""Change title label text and add free space display"""
		if text is None: text = self.path

		system_size = self.get_provider().get_system_size(self.path)

		self._title_bar.set_title(text)
		self._title_bar.set_subtitle(
									'{2} {0} - {3} {1}'.format(
															common.format_size(system_size.size_available),
															common.format_size(system_size.size_total),
															_('Free:'),
															_('Total:')
														)
								)

	def _drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
		"""Handle dropping files on file list"""
		item_list = selection_data.data.splitlines(False)

		# prepare data for copying
		protocol, path = item_list[0].split('://', 1)
		item_list = [urllib.unquote(item.split('://')[1]) for item in item_list]

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
												item_list
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
		protocol = self.get_provider().get_protocol()

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
		if self._fs_monitor is not None:
			self._fs_monitor.cancel()

		# if there is already active thread, stop it
		if self._thread_active.is_set():
			self._thread_active.clear()

		# get number of items to preload
		if len(self._store) > 0 and self._item_list.allocation.height != self._preload_size:
			cell_area = self._item_list.get_cell_area(
										self._store.get_path(self._store.get_iter_first()),
										self._columns[0]
									)
			tree_size = self._item_list.allocation.height

			# calculate number of items to preload
			if len(cell_area) >= 4 and cell_area[3] > 0:
				self._preload_count = (tree_size / cell_area[3]) + 1
				self._preload_size = tree_size

		# clear list
		self._clear_list()

		# cache objects and settings
		show_hidden = self._parent.options.section('item_list').get('show_hidden')

		# hide thumbnail
		if self._enable_media_preview:
			self._thumbnail_view.hide()

		# make sure we don't have trailing directory separator
		if len(path) > 1 and path[-1] == os.path.sep:
			path = path[:-1]

		# get provider for specified URI
		uri = urlparse.urlparse(path)
		provider = None
		scheme = uri.scheme if uri.scheme != '' else 'file'
		self.path = path if scheme != 'file' else uri.path

		if scheme == self.scheme:
			# we are working with same provider
			provider = self.get_provider()

		else:
			# different provider, we need to get it
			Provider = self._parent.get_provider_by_protocol(scheme)

			if Provider is not None:
				provider = Provider(self)

				self.scheme = scheme
				self._provider = provider

		if provider is None:
			provider = LocalProvider(self)
			self._provider = provider
			self.path = user.home

		# change list icon
		self._title_bar.set_icon_from_name(provider.get_protocol_icon())

		# update GTK controls
		path_name = os.path.basename(self.path)
		if path_name == "":
			path_name = uri.path

		self._change_tab_text(path_name)
		self._change_title_text(self.path)
		self._parent.path_label.set_text(self.path)

		# reset directory statistics
		self._dirs['count'] = 0
		self._dirs['selected'] = 0
		self._files['count'] = 0
		self._files['selected'] = 0
		self._size['total'] = 0L
		self._size['selected'] = 0

		# populate list
		try:
			item_list = provider.list_dir(self.path)

			# remove hidden files if we don't need them
			item_list = filter(
			               lambda item_name: show_hidden or (item_name[0] != '.' and item_name[-1] != '~'),
			               item_list
			             )

			# sort list to prevent messing up list while
			# adding items from a separate thread
			item_list.sort()

			# assign item for selection
			if not selected in item_list:
				selected = None

			self._item_to_focus = selected

			# split items among lists
			preload_list = item_list[:self._preload_count]
			item_list = item_list[self._preload_count:]

			if uri.path != os.path.sep and uri.path != '':
				# add parent option for parent directory
				self._store.append((
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

			# preload items
			for item_name in preload_list:
				self._add_item(item_name)

			# let the rest of items load in a separate thread
			if len(item_list) > 0:
				def thread_method():
					# set event to active
					self._thread_active.set()

					# show spinner animation
					with gtk.gdk.lock:
						self._title_bar.show_spinner()

					for item_name in item_list:
						# check if we are allowed to continue
						if not self._thread_active.is_set():
							break;

						# add item to the list
						self._add_item(item_name)

					# hide spinner animation
					with gtk.gdk.lock:
						self._title_bar.hide_spinner()

						# update status bar
						self._update_status_with_statistis()

				self._change_path_thread = Thread(target=thread_method)
				self._change_path_thread.start()

			# if no errors occurred during path change,
			# call parent method which handles history
			ItemList.change_path(self, self.path)

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
				# retry loading path again
				self.change_path(path)

			else:
				# load previous valid path
				self.change_path(self.history[0], os.path.basename(path))

			return

		# update status bar
		self._update_status_with_statistis()

		# if no item was specified, select first one
		if selected is None:
			path = self._store.get_path(self._store.get_iter_first())
			self._item_list.set_cursor(path)
			self._item_list.scroll_to_cell(path)

		# create file monitor
		try:
			self._fs_monitor = self.get_provider().get_monitor(self.path)

			if self._fs_monitor is not None:
				self._fs_monitor.connect('changed', self._directory_changed)

		except MonitorError:
			# monitoring is probably not supported by the provider
			self._fs_monitor = None

	def select_all(self, pattern=None, exclude_list=None):
		"""Select all items matching pattern"""
		if pattern is None:
			pattern = "*"

		if exclude_list is None:
			exclude_list = ()

		dirs = 0
		files = 0
		size = 0L
		result = 0
		color = self._selection_color

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] \
			and fnmatch.fnmatch(row[Column.NAME], pattern) \
			and row[Column.NAME] not in exclude_list:
				# select item that matched out criteria
				row[Column.COLOR] = color
				row[Column.SELECTED] = self._pixbuf_selection

				result += 1

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

		return result

	def unselect_all(self, pattern=None):
		"""Unselect items matching the pattern"""
		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0
		size = 0L
		result = 0

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] and fnmatch.fnmatch(row[Column.NAME], pattern):
				row[Column.COLOR] = None
				row[Column.SELECTED] = None

				result += 1

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

		return result

	def invert_selection(self, pattern=None):
		"""Invert selection matching the pattern"""
		if pattern is None:
			pattern = "*"

		dirs = 0
		files = 0
		size = 0L
		result = 0

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] and fnmatch.fnmatch(row[Column.NAME], pattern):
				if row[Column.COLOR] is None:
					row[Column.COLOR] = self._selection_color
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

				result += 1

		self._dirs['selected'] = dirs
		self._files['selected'] = files
		self._size['selected'] = size

		# update status bar
		ItemList.select_all(self, pattern)
		self._update_status_with_statistis();

		return result

	def refresh_file_list(self, widget=None, data=None):
		"""Reload file list for current directory"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# get current selection
		f_name = None
		if selected_iter is not None:
			f_name = item_list.get_value(selected_iter, Column.NAME)

		# reload path
		self.change_path(self.path, f_name)

		return True

	def update_column_size(self, name):
		"""Update column size with global value"""
		column = filter(lambda item: item.get_data('name') == name, self._columns)[0]
		width = self._parent.plugin_options.section(self.__class__.__name__).get('size_{0}'.format(name))

		if width is not None:
			column.set_fixed_width(width)

	def get_provider(self):
		"""Get list provider object"""
		if self._provider is None:
			Provider = self._parent.get_provider_by_protocol(self.scheme)

			if Provider is not None:
				self._provider = Provider(self)

		return self._provider

	def apply_settings(self):
		"""Apply file list settings"""
		ItemList.apply_settings(self)  # let parent apply its own settings
		section = self._parent.options.section('item_list')

		# apply row hinting
		row_hinting = section.get('row_hinting')
		self._item_list.set_rules_hint(row_hinting)

		# apply grid lines
		grid_lines = (
					gtk.TREE_VIEW_GRID_LINES_NONE,
					gtk.TREE_VIEW_GRID_LINES_HORIZONTAL,
					gtk.TREE_VIEW_GRID_LINES_VERTICAL,
					gtk.TREE_VIEW_GRID_LINES_BOTH,
				)[section.get('grid_lines')]
		self._item_list.set_grid_lines(grid_lines)

		# cache settings
		self._time_format = section.get('time_format')
		self._mode_format = section.get('mode_format')

		# reload file list in order to apply time formatting, hidden files and other
		self.refresh_file_list()

	def apply_media_preview_settings(self):
		"""Apply settings related to image_preview"""
		self._enable_media_preview = self._parent.options.get('media_preview')

		if self._enable_media_preview:
			# force showing thumbnail
			self._handle_cursor_change()

		else:
			# hide thumbnail
			self._thumbnail_view.hide()
