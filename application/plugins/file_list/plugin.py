import os
import gtk
import time
import user
import fnmatch
import common

from column_editor import FileList_ColumnEditor
from gio_extension import SambaExtension, FtpExtension, DavExtension, SftpExtension
from gio_provider import NetworkProvider, TrashProvider, DavProvider, DavsProvider
from gio_provider import SambaProvider, FtpProvider, SftpProvider
from gui.input_dialog import ApplicationSelectDialog
from gui.input_dialog import CopyDialog, MoveDialog, RenameDialog
from gui.input_dialog import FileCreateDialog, DirectoryCreateDialog
from gui.properties_window import PropertiesWindow
from local_provider import LocalProvider
from operation import DeleteOperation, CopyOperation, MoveOperation
from parameters import Parameters
from plugin_base.item_list import ItemList
from plugin_base.monitor import MonitorSignals, MonitorError
from plugin_base.provider import FileType, Mode as FileMode
from threading import Thread, Event
from widgets.thumbnail_view import ThumbnailView


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_class('file_list', _('Local file list'), FileList)

	# register providers
	application.register_provider(LocalProvider)
	application.register_provider(SambaProvider)
	application.register_provider(FtpProvider)
	application.register_provider(SftpProvider)
	application.register_provider(NetworkProvider)
	application.register_provider(TrashProvider)
	application.register_provider(DavProvider)
	application.register_provider(DavsProvider)

	# register mount manager extension
	application.register_mount_manager_extension(SambaExtension)
	application.register_mount_manager_extension(FtpExtension)
	application.register_mount_manager_extension(SftpExtension)
	application.register_mount_manager_extension(DavExtension)


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
	USER_ID = 14
	GROUP_ID = 15


class FileList(ItemList):
	"""General file list plugin

	This plugin was written with various usages in mind. If you need to write
	plugin that will handle files it is strongly suggested that you inherit this class
	and make your own content provider.

	"""
	column_editor = None

	def __init__(self, parent, notebook, options):
		ItemList.__init__(self, parent, notebook, options)

		self.scheme = 'file'

		self.path = self._options.get('path', user.home)
		self._sort_column = self._options.get('sort_column', 0)
		self._sort_ascending = self._options.get('sort_ascending', True)

		# event object controlling path change thread
		self._thread_active = Event()
		self._main_thread_lock = Event()

		# preload variables
		self._preload_count = 0
		self._preload_size = 0

		# storage system for list items
		self._store = gtk.TreeStore(
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
								str,	# Column.ICON
								bool,	# Column.SELECTED
								int,	# Column.USER_ID
								int,	# Column.GROUP_ID
							)

		# set item list model
		self._item_list.set_model(self._store)

		# create columns
		cell_selected = gtk.CellRendererText()
		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_extension = gtk.CellRendererText()
		cell_size = gtk.CellRendererText()
		cell_mode = gtk.CellRendererText()
		cell_date = gtk.CellRendererText()

		cell_selected.set_property('width', 30)  # leave enough room for various characters
		cell_selected.set_property('xalign', 1)
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
		col_name.set_cell_data_func(cell_selected, self._selected_data_func)
		col_extension.add_attribute(cell_extension, 'foreground', Column.COLOR)
		col_size.add_attribute(cell_size, 'foreground', Column.COLOR)
		col_mode.add_attribute(cell_mode, 'foreground', Column.COLOR)
		col_date.add_attribute(cell_date, 'foreground', Column.COLOR)

		# col_name.add_attribute(cell_selected, 'pixbuf', Column.SELECTED)
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
		self._columns = [col_name, col_extension, col_size, col_mode, col_date]

		# create column editor if needed
		if self.column_editor is None:
			self.__class__.column_editor = FileList_ColumnEditor(self, parent.plugin_options)
			parent.register_column_editor_extension(self.column_editor)

		# set default column sizes for file list
		self._columns_size = (200, 50, 70, 50, 90)
		self._create_default_column_sizes()

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

		# create extension columns
		class_list = self._parent.get_column_extension_classes(self.__class__)

		for ExtensionClass in class_list:
			extension = ExtensionClass(self, self._store)
			column = extension.get_column()

			if column is not None:
				sort_data = extension.get_sort_column()

				# configure column
				column.set_reorderable(True)
				column.set_resizable(True)
				column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

				# connect signals
				column.connect('notify::width', self._column_resized)
				column.connect('clicked', self._set_sort_function, sort_data)

				# add new column to lists for proper handling
				column_sort_data[sort_data] = column
				self._columns.append(column)
				self._item_list.append_column(column)

		# resize columns to saved values
		self._resize_columns(self._columns)

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

		# set visibility of tree expanders
		self._item_list.set_show_expanders(self._parent.options.section('item_list').get('show_expanders'))

		# set grid lines
		grid_lines = (
					gtk.TREE_VIEW_GRID_LINES_NONE,
					gtk.TREE_VIEW_GRID_LINES_HORIZONTAL,
					gtk.TREE_VIEW_GRID_LINES_VERTICAL,
					gtk.TREE_VIEW_GRID_LINES_BOTH,
				)[self._parent.options.section('item_list').get('grid_lines')]
		self._item_list.set_grid_lines(grid_lines)

		# set sort function
		if self._sort_column is None \
		or self._sort_column not in column_sort_data:
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

		plugin_options = self._parent.plugin_options
		if plugin_options.has_section(self._name) \
		and plugin_options.section(self._name).has('columns'):
			self._show_full_name = 'extension' not in plugin_options.section(self._name).get('columns')

		else:
			self._show_full_name = False;

		# change to initial path
		try:
			self.change_path(self.path)

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
		file_name = self._get_selection(relative=False)
		protocol = self.get_provider().protocol
		uri = '{0}://{1}'.format(protocol, file_name) if not is_parent else None

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

	def _handle_tab_close(self):
		"""Handle tab closing"""
		ItemList._handle_tab_close(self)

		# cancel current directory monitor
		if self._fs_monitor is not None:
			self._fs_monitor.cancel()

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

		else:
			# selected item is just a file, execute it
			selected_file = self._get_selection()
			self._parent.associations_manager.execute_file(selected_file, provider=self.get_provider())

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
			options = Parameters()
			options.set('path', os.path.join(self.path, name))

			self._parent.create_tab(
							self._notebook,
							self.__class__,
							options
						)

		return True

	def _open_directory(self, widget=None, data=None):
		"""Open selected directory"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# we need selection for this
		if selected_iter is None:
			return True

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

	def _expand_directory(self, widget=None, data=None):
		"""Expand currently selected directory"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# we need selection for this
		if selected_iter is None:
			return True

		# get needed data for operation
		name = item_list.get_value(selected_iter, Column.NAME)
		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		# don't allow expanding parent directory
		if is_parent:
			return True

		# start loader thread and expand directory
		if is_dir:
			self._load_directory(os.path.join(self.path, name), selected_iter)
			self._item_list.expand_row(item_list.get_path(selected_iter), False)

		return True

	def _collapse_directory(self, widget=None, data=None):
		"""Collapse currently selected directory"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# we need selection for this
		if selected_iter is None:
			return True

		# get parent iter
		if item_list.iter_has_child(selected_iter):
			parent = selected_iter

		else:
			parent = item_list.iter_parent(selected_iter)

		# collapse directory and remove its children
		if parent is not None:
			# remove children
			child = item_list.iter_children(parent)
			while child:
				old_child = child
				child = item_list.iter_next(old_child)
				item_list.remove(old_child)

			# collapse row
			self._item_list.collapse_row(item_list.get_path(parent))

			# select parent row
			path = item_list.get_path(parent)
			self._item_list.set_cursor(path)
			self._item_list.scroll_to_cell(path)

		return True

	def _create_directory(self, widget=None, data=None):
		"""Prompt user and create directory"""
		dialog = DirectoryCreateDialog(self._parent)
		show_hidden = self._parent.options.section('item_list').get('show_hidden')

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
				is_hidden = response[1][0] == '.'

				if self._fs_monitor is None:
					if is_hidden and show_hidden \
					or not is_hidden:
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
		show_hidden = self._parent.options.section('item_list').get('show_hidden')

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
				is_hidden = response[1][0] == '.'

				if self._fs_monitor is None:
					if is_hidden and show_hidden \
					or not is_hidden:
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
					self._parent.association_manager.edit_file((response[1], ))

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

	def _delete_files(self, widget=None, force_delete=None):
		"""Delete selected files"""
		selection = self._get_selection_list(relative=True)

		# return if there is no selection
		if selection is None:
			return

		# check if user has disabled dialog
		show_dialog = self._parent.options.section('confirmations').get('delete_items')
		trash_items = self._parent.options.section('operations').get('trash_files')

		if show_dialog:
			# get context sensitive message
			if force_delete or not trash_items:
				message = ngettext(
						 	"You are about to delete {0} item.\n"
						 	"Are you sure about this?",
						 	"You are about to delete {0} items.\n"
						 	"Are you sure about this?",
						 	len(selection)
						 ) 

			else:
				message = ngettext(
						 	"You are about to move {0} item to trash.\n"
						 	"Are you sure about this?",
						 	"You are about to move {0} items to trash.\n"
						 	"Are you sure about this?",
						 	len(selection)
						 ) 

			# user has confirmation dialog enabled
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_QUESTION,
									gtk.BUTTONS_YES_NO,
									message.format(len(selection))
								)
			dialog.set_default_response(gtk.RESPONSE_YES)
			result = dialog.run()
			dialog.destroy()

			can_continue = result == gtk.RESPONSE_YES

		else:
			# user has confirmation dialog disabled
			can_continue = True

		# if user is sure about removal create operation
		if can_continue:
			operation = DeleteOperation(
									self._parent,
									self.get_provider()
								)
			if force_delete:
				operation.set_force_delete(True)

			operation.set_selection(selection)
			operation.start()

		return True

	def _copy_files(self, widget=None, data=None):
		"""Copy selected files"""
		selection = self._get_selection_list(relative=True)

		# return if there is no selection
		if selection is None:
			return

		# get providers
		opposite_object = self._parent.get_opposite_object(self)
		source_provider = self.get_provider()
		destination_provider = None

		if hasattr(opposite_object, 'get_provider'):
			destination_provider = opposite_object.get_provider()
		
		# ask confirmation from user
		dialog = CopyDialog(
						self._parent,
						source_provider,
						destination_provider,
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
			operation.set_selection(selection)
			operation.start()

		return True

	def _move_files(self, widget=None, data=None):
		"""Move selected files"""
		selection = self._get_selection_list(relative=True)

		# return if there is no selection
		if selection is None:
			return

		# get providers
		opposite_object = self._parent.get_opposite_object(self)
		source_provider = self.get_provider()
		destination_provider = None

		if hasattr(opposite_object, 'get_provider'):
			destination_provider = opposite_object.get_provider()

		# ask confirmation from user
		dialog = MoveDialog(
						self._parent,
						source_provider,
						destination_provider,
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
			operation.set_selection(selection)
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

	def _get_selection(self, relative=False, files_only=False):
		"""Return item with path under cursor"""
		result = None
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		if not is_parent and ((not files_only) or (files_only and not is_dir)):
			item = item_list.get_value(selected_iter, Column.NAME)
			result = item if relative else os.path.join(self.path, item)

		return result

	def _get_selection_list(self, under_cursor=False, relative=False, files_only=False, starting_iter=None):
		"""Return list of selected items

		This list is used by many other methods inside this program,
		including 'open with' handlers, execute_selected file, etc.

		"""
		result = []

		if under_cursor:
			selection = self._get_selection(relative=relative, files_only=files_only)
			if selection is None:
				result = None
			else:
				result.append(self._get_selection())

		else:
			list_iter = starting_iter or self._store.get_iter_first()

			while list_iter:
				is_dir = self._store.get_value(list_iter, Column.IS_DIR)
				is_selected = self._store.get_value(list_iter, Column.SELECTED)
				name = self._store.get_value(list_iter, Column.NAME)

				# only add to the result list if item matches selection
				if is_selected and ((not files_only) or (files_only and not is_dir)):
					result.append(name if relative else os.path.join(self.path, name))

				# if iter has children check them too
				if self._store.iter_has_child(list_iter):
					sublist = self._get_selection_list(
									under_cursor,
									relative,
									files_only,
									self._store.iter_children(list_iter)
								)

					if sublist is not None:
						result.extend(sublist)

				list_iter = self._store.iter_next(list_iter)

			if len(result) == 0:
				selection = self._get_selection(relative=relative, files_only=files_only)
				if selection is None:
					result = None
				else:
					result.append(selection)

		return result

	def _prepare_popup_menu(self):
		"""Populate pop-up menu items"""
		selection = self._item_list.get_selection()
		item_list, selected_iter = selection.get_selected()
		associations_manager = self._parent.associations_manager
		menu_manager = self._parent.menu_manager

		is_dir = item_list.get_value(selected_iter, Column.IS_DIR)
		is_parent = item_list.get_value(selected_iter, Column.IS_PARENT_DIR)

		# get selected item
		filename = self._get_selection()
		selection = self._get_selection_list()

		# detect mime type
		if is_dir:
			mime_type = 'inode/directory'

		else:
			mime_type = associations_manager.get_mime_type(filename)

			# try to detect by content
			if associations_manager.is_mime_type_unknown(mime_type):
				data = associations_manager.get_sample_data(filename, self.get_provider())
				mime_type = associations_manager.get_mime_type(data=data)

		# call parent method which removes existing menu items
		ItemList._prepare_popup_menu(self)

		# update additional options menu
		additional_options = menu_manager.get_additional_options_for_type(mime_type, selection, self.get_provider())
		for menu_item in additional_options:
			self._additional_options_menu.append(menu_item)

		# get associated applications
		program_list = menu_manager.get_items_for_type(mime_type, selection)
		custom_list = menu_manager.get_custom_items_for_type(mime_type, selection)

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
		self._open_with_item.set_sensitive(not is_parent)
		self._open_new_tab_item.set_visible(is_dir)
		self._additional_options_item.set_sensitive(len(additional_options) > 0)
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
		for column in self._columns:
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

	def _select_all(self, widget, data=None):
		"""Proxy method for selecting all items"""
		if self._dirs['selected'] < self._dirs['count'] or self._files['selected'] < self._files['count']:
			self.select_all()

		else:
			self._deselect_all(widget, data=None)

		return True

	def _deselect_all(self, widget, data=None):
		"""Proxy method for deselecting all items"""
		self.deselect_all()
		return True

	def _invert_selection(self, widget, data=None):
		"""Proxy method for selecting all items"""
		self.invert_selection()
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
			selected = not item_list.get_value(selected_iter, Column.SELECTED)
			color = (None, self._selection_color)[selected]

			if is_dir:
				self._dirs['selected'] += [-1, 1][selected]
			else:
				self._files['selected'] += [-1, 1][selected]
				self._size['selected'] += [-1, 1][selected] * size

			item_list.set_value(selected_iter, Column.COLOR, color)
			item_list.set_value(selected_iter, Column.SELECTED, selected)

		# update status bar
		ItemList._toggle_selection(self, widget, data, advance)
		self._update_status_with_statistis()

		if advance:
			# select next item in the list
			next_iter = item_list.iter_next(selected_iter)
			if next_iter is not None:
				# iter is not last in the list
				path = item_list.get_path(next_iter)
				self._item_list.set_cursor(path)
				self._item_list.scroll_to_cell(path)

			elif item_list.iter_parent(selected_iter) is not None:
				# if iter is part of expanded directory advance through parent
				next_iter = item_list.iter_next(item_list.iter_parent(selected_iter))

				if next_iter is not None:
					path = item_list.get_path(next_iter)
					self._item_list.set_cursor(path)
					self._item_list.scroll_to_cell(path)

		return True

	def _select_range(self, start_path, end_path):
		"""Set items in range to status opposite from first item in selection"""
		if len(self._store) == 1:  # exit when list doesn't have items
			return

		# get current selection
		current_iter = self._store.get_iter(start_path)

		# swap paths if selecting from bottom up
		if start_path[0] > end_path[0]:
			start_path, end_path = end_path, start_path

		# make sure start path is not parent
		if start_path[0] == 0:
			start_path = (1, )

		# values to be set in columns
		selected = not self._store.get_value(current_iter, Column.SELECTED)
		color = (None, self._selection_color)[selected]

		for index in xrange(start_path[0], end_path[0] + 1):
			current_iter = self._store.get_iter((index, ))

			# get current iter information
			size = self._store.get_value(current_iter, Column.SIZE)
			is_dir = self._store.get_value(current_iter, Column.IS_DIR)
			status = self._store.get_value(current_iter, Column.SELECTED)

			# set selection
			self._store.set_value(current_iter, Column.COLOR, color)
			self._store.set_value(current_iter, Column.SELECTED, selected)

			# modify counters only when status is changed
			if selected is not status:
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
		selection_list = self._get_selection_list(relative=False, files_only=True)

		if len(selection_list) > 0:
			self._parent.associations_manager.edit_file(selection_list)

		return True

	def _selected_data_func(self, column, cell, store, selected_iter, data=None):
		"""Handle setting selected identifier"""
		selected = store.get_value(selected_iter, Column.SELECTED)
		cell.set_property('text', (None, self._selection_indicator)[selected])

	def _find_iter_by_name(self, name):
		""" Find and return item by name"""
		result = None

		for row in self._store:
			if row[Column.NAME] == name:
				result = row.iter
				break

		return result

	def _add_item(self, filename, parent=None, parent_path=None):
		"""Add item to the list"""
		result = None
		provider = self.get_provider()
		full_path = os.path.join(self.path, parent_path) if parent_path else self.path

		file_stat = provider.get_stat(filename, relative_to=full_path)

		file_size = file_stat.size
		file_mode = file_stat.mode
		file_date = file_stat.time_modify
		is_dir = file_stat.type is FileType.DIRECTORY

		# directory
		if file_stat.type is FileType.DIRECTORY:
			icon = 'folder'

			if parent is None:
				self._dirs['count'] += 1

		# regular file
		elif file_stat.type is FileType.REGULAR:
			icon = self._parent.icon_manager.get_icon_for_file(filename)

			if parent is None:
				self._files['count'] += 1
				self._size['total'] += file_size

		# invalid links or files
		elif file_stat.type is FileType.INVALID:
			icon = 'image-missing'

			if parent is None:
				self._files['count'] += 1

		# add item to the list
		try:
			# don't allow extension splitting on directories
			formated_file_mode = common.format_mode(file_mode, self._mode_format)
			formated_file_date = time.strftime(self._time_format, time.localtime(file_date))

			if not is_dir:
				# item is a file
				file_info = os.path.splitext(filename)
				if self._show_full_name:
					file_info = (filename, file_info[1])

				formated_file_size = common.format_size(file_size, self._size_format, False)

			else:
				# item is a directory
				file_info = (filename, '')
				formated_file_size = '<DIR>'

			props = (
					os.path.join(parent_path, filename) if parent_path else filename,
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
					None,
					file_stat.user_id,
					file_stat.group_id
				)

			result = self._store.append(parent, props)

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
				if item_list.get_value(found_iter, Column.SELECTED):
					self._dirs['selected'] -= 1

			else:
				self._files['count'] -= 1
				self._size['total'] -= item_list.get_value(found_iter, Column.SIZE)

				# update selected counters
				if item_list.get_value(found_iter, Column.SELECTED):
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
				formated_file_size = common.format_size(file_size, self._size_format, False)

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
		if text is None:
			text = self.path

		# get system information
		system_size = self.get_provider().get_system_size(self.path)

		# format numbers
		size_available = common.format_size(system_size.size_available, self._size_format)
		size_total = common.format_size(system_size.size_total, self._size_format)

		# calculate percent available
		if system_size.size_total > 0:
			percent_available = 100.0 * system_size.size_available / system_size.size_total

		else:
			percent_available = 0

		# set title and subtitle
		self._title_bar.set_title(text)
		self._title_bar.set_subtitle('{3} {0} - {4} {1} - {2:.2f}%'.format(
							size_available, 
							size_total, 
							percent_available,
							_('Free:'), 
							_('Total:')
						))

	def _drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
		"""Handle dropping files on file list"""
		item_list = selection_data.data.splitlines(False)

		# prepare data for copying
		protocol, path = item_list[0].split('://', 1)

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

	def _drag_data_get(self, widget, drag_context, selection_data, info, time):
		"""Handle data request from destination widget"""
		protocol = self.get_provider().get_protocol()

		selection = []
		for file_name in self._get_selection_list():
			selection.append('{0}://{1}'.format(protocol, file_name))

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

	def _load_directory(self, path, parent=None, clear_store=False):
		"""Load directory content into store"""
		# if there is already active thread, stop it
		if self._thread_active.is_set():
			self._main_thread_lock.set()
			self._thread_active.clear()

			while self._main_thread_lock.is_set():
				gtk.main_iteration(block=False)

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
		if clear_store:
			self._clear_list()

		# default value for parent path
		parent_path = None

		# cache objects and settings
		show_hidden = self._parent.options.section('item_list').get('show_hidden')

		# get list of items to add
		item_list = self._provider.list_dir(path)

		# remove hidden files if we don't need them
		item_list = filter(
						lambda item_name: show_hidden or (item_name[0] != '.' and item_name[-1] != '~'),
						item_list
					)

		# sort list to prevent messing up list while
		# adding items from a separate thread
		item_list.sort()

		# assign item for selection
		if not self._item_to_focus in item_list:
			self._item_to_focus = None

		# split items among lists
		preload_list = item_list[:self._preload_count]
		item_list = item_list[self._preload_count:]

		if path != os.path.sep \
		and path != '{0}://'.format(self.scheme) \
		and parent is None:
			# add parent option for parent directory
			self._store.append(parent, (
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
							None,
							0,
							0
						))
		else:
			# prepare full parent path
			parent_path = self._store.get_value(parent, Column.NAME)

		# preload items
		for item_name in preload_list:
			self._add_item(item_name, parent, parent_path)

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
					with gtk.gdk.lock:
						self._add_item(item_name, parent, parent_path)

				# hide spinner animation
				with gtk.gdk.lock:
					self._title_bar.hide_spinner()

					# update status bar
					self._update_status_with_statistis()

				self._thread_active.clear()
				self._main_thread_lock.clear()

			self._change_path_thread = Thread(target=thread_method)
			self._change_path_thread.start()

	def change_path(self, path=None, selected=None):
		"""Change file list path"""
		# cancel current directory monitor
		if self._fs_monitor is not None:
			self._fs_monitor.cancel()

		# make sure path is actually string and not unicode object
		# we still handle unicode strings properly, just avoid issues
		# with file names that have names in bad encoding
		path = str(path)

		# hide thumbnail
		if self._enable_media_preview:
			self._thumbnail_view.hide()

		# get provider for specified URI
		provider = None
		self.path = path 

		if '://' not in path:
			scheme = 'file'

		else:
			data = path.split('://', 1)
			scheme = data[0]
			
			# for local storage, use path without scheme
			if scheme == 'file':
				self.path = data[1]

		if scheme == self.scheme:
			# we are working with same provider
			provider = self.get_provider()

		else:
			# different provider, we need to get it
			ProviderClass = self._parent.get_provider_by_protocol(scheme)

			if ProviderClass is not None:
				provider = ProviderClass(self)

				self.scheme = scheme
				self._provider = provider

		# in case we can't handle specified URI show home directory
		if provider is None:
			provider = LocalProvider(self)
			self._provider = provider
			self.path = user.home

		# update options container
		self._options.set('path', self.path)

		# update GTK controls
		path_name = os.path.basename(self.path)
		if path_name == "":
			path_name = self.path

		self._change_tab_text(path_name)
		self._change_title_text(self.path)

		if self._parent.get_active_object() == self:
			self._parent.set_location_label(self.path)

		# change list icon
		self._title_bar.set_icon_from_name(provider.get_protocol_icon())

		# reset directory statistics
		self._dirs['count'] = 0
		self._dirs['selected'] = 0
		self._files['count'] = 0
		self._files['selected'] = 0
		self._size['total'] = 0L
		self._size['selected'] = 0

		try:
			# populate list
			self._item_to_focus = selected
			self._load_directory(self.path, clear_store=True)

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
										"Error changing working directory to:"
										"\n{1}\n\n{0}\n\nWould you like to retry?"
									).format(error, path)
								)
			dialog.set_default_response(gtk.RESPONSE_YES)
			result = dialog.run()
			dialog.destroy()

			# remove invalid paths from history so we don't end up in a dead loop
			self.history = filter(lambda history_path: path != history_path, self.history)

			# make sure we have something in history list
			if len(self.history) == 0:
				self.history.append(user.home)

			if result == gtk.RESPONSE_YES:
				# retry loading path again
				self.change_path(path)

			else:
				# load previous valid path
				self.change_path(self.history[0], os.path.basename(path))

			return

		else:
			# with or without exception we need to handle few things
			self._title_bar.hide_spinner()

		# update status bar
		self._update_status_with_statistis()

		# if no item was specified, select first one
		if selected is None \
		and len(self._store) > 0:
			path = self._store.get_path(self._store.get_iter_first())
			self._item_list.set_cursor(path)
			self._item_list.scroll_to_cell(path)

		# create file monitor
		try:
			self._fs_monitor = provider.get_monitor(self.path)

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

		for row in self._store:
			# set selection
			if not row[Column.IS_PARENT_DIR] \
			and fnmatch.fnmatch(row[Column.NAME], pattern) \
			and row[Column.NAME] not in exclude_list:
				# select item that matched out criteria
				row[Column.COLOR] = self._selection_color
				row[Column.SELECTED] = True

				result += 1

			elif len(exclude_list) > 0:
				# if out exclude list has items, we need to deselect them
				row[Column.COLOR] = None
				row[Column.SELECTED] = False

			# update dir/file count
			if row[Column.SELECTED]:
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

	def deselect_all(self, pattern=None):
		"""Deselect items matching the pattern"""
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
				row[Column.SELECTED] = False

				result += 1

			# update dir/file count
			if row[Column.SELECTED]:
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
				if not row[Column.SELECTED]:
					row[Column.COLOR] = self._selection_color
					row[Column.SELECTED] = True
				else:
					row[Column.COLOR] = None
					row[Column.SELECTED] = False

			# update dir/file count
			if row[Column.SELECTED]:
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
		width = self._parent.plugin_options.section(self._name).get('size_{0}'.format(name))

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
		plugin_options = self._parent.plugin_options

		# apply column visibility and sizes
		self._reorder_columns()
		self._resize_columns(self._columns)

		# apply row hinting
		row_hinting = section.get('row_hinting')
		self._item_list.set_rules_hint(row_hinting)

		# apply expander visibility
		self._item_list.set_show_expanders(section.get('show_expanders'))

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

		if plugin_options.has_section(self._name) \
		and plugin_options.section(self._name).has('columns'):
			self._show_full_name = 'extension' not in plugin_options.section(self._name).get('columns')

		else:
			self._show_full_name = False;

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
