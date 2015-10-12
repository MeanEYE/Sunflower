import os
import gtk
import gobject
import fnmatch

from threading import Thread, Event
from gui.input_dialog import OverwriteFileDialog, OverwriteDirectoryDialog, OperationError, QuestionOperationError
from gui.operation_dialog import CopyDialog, MoveDialog, DeleteDialog, RenameDialog
from gui.error_list import ErrorList
from plugin_base.provider import Mode as FileMode, TrashError, Support as ProviderSupport
from plugin_base.monitor import MonitorSignals
from common import format_size
from queue import OperationQueue

# import constants
from gui.input_dialog import OverwriteOption


class BufferSize:
	LOCAL = 4096 * 1024
	REMOTE = 100 * 1024


class Option:
	FILE_TYPE = 0
	DESTINATION = 1
	SET_OWNER = 2
	SET_MODE = 3
	SET_TIMESTAMP = 4
	SILENT = 5
	SILENT_MERGE = 6
	SILENT_OVERWRITE = 7


class Skip:
	TRASH = 0
	REMOVE = 1
	WRITE = 2
	CREATE = 3
	MODE_SET = 4
	MOVE = 5
	RENAME = 6
	READ = 7


class OperationType:
	COPY = 0
	MOVE = 1
	DELETE = 2
	RENAME = 3
	LINK = 4


class Operation(Thread):
	"""Parent class for all operation threads"""

	def __init__(self, application, source, destination=None, options=None, destination_path=None):
		Thread.__init__(self, target=self)
		self._can_continue = Event()
		self._abort = Event()
		self._application = application
		self._source = source
		self._destination = destination
		self._options = options
		self._source_queue = None
		self._destination_queue = None
		self._merge_all = None
		self._overwrite_all = None
		self._response_cache = {}

		# operation queue
		self._operation_queue = None
		self._operation_queue_name = None

		# daemonize
		self.daemon = True

		# create operation dialog
		self._dialog = None
		self._create_dialog()

		self._dir_list = []
		self._file_list = []
		self._error_list = []
		self._selection_list = []

		# store initial paths
		self._source_path = self._source.get_path()
		if self._destination is not None:
			self._destination_path = destination_path or self._destination.get_path()

		self._can_continue.set()

	def _create_dialog(self):
		"""Create operation dialog"""
		pass

	def _destroy_ui(self):
		"""Destroy user interface"""
		if self._dialog is not None:
			with gtk.gdk.lock:
				self._dialog.destroy()

	def _get_free_space_input(self, needed, available):
		"""Get user input when there is not enough space"""
		size_format = self._application.options.get('size_format')
		space_needed = format_size(needed, size_format)
		space_available = format_size(available, size_format)

		if self._options is not None and self._options[Option.SILENT]:
			# silent option is enabled, we skip operation by default
			self._error_list.append(_(
							'Aborted. Not enough free space on target file system.\n'
							'Needed: {0}\n'
							'Available: {1}'
						).format(space_needed, space_available))
			should_continue = False

		else:
			# ask user what to do
			with gtk.gdk.lock:
				dialog = gtk.MessageDialog(
										self._dialog.get_window(),
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_WARNING,
										gtk.BUTTONS_YES_NO,
										_(
											'Target file system does not have enough '
											'free space for this operation to continue.\n\n'
											'Needed: {0}\n'
											'Available: {1}\n\n'
											'Do you wish to continue?'
										).format(space_needed, space_available)
									)
				dialog.set_default_response(gtk.RESPONSE_YES)
				result = dialog.run()
				dialog.destroy()

				should_continue = result == gtk.RESPONSE_YES

		return should_continue

	def _get_merge_input(self, path):
		"""Get merge confirmation"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, do what user specified
			merge = self._options[Option.SILENT_MERGE]
			self._merge_all = merge

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OverwriteDirectoryDialog(self._application, self._dialog.get_window())

				title_element = os.path.basename(path)
				message_element = os.path.basename(os.path.dirname(os.path.join(self._destination.get_path(), path)))

				dialog.set_title_element(title_element)
				dialog.set_message_element(message_element)
				dialog.set_rename_value(title_element)
				dialog.set_source(
								self._source,
								path,
								relative_to=self._source_path
							)
				dialog.set_original(
								self._destination,
								path,
								relative_to=self._destination_path
							)

				result = dialog.get_response()
				merge = result[0] == gtk.RESPONSE_YES

			if result[1][OverwriteOption.APPLY_TO_ALL]:
				self._merge_all = merge

			# in case user canceled operation
			if result[0] == gtk.RESPONSE_CANCEL:
				self.cancel()

		return merge  # return only response for current directory

	def _get_overwrite_input(self, path):
		"""Get overwrite confirmation"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, do what user specified
			overwrite = self._options[Option.SILENT_OVERWRITE]
			self._overwrite_all = overwrite
			options = (False, '', True)  # no rename, apply to all

		else:
			# we are not in silent mode, ask user what to do
			with gtk.gdk.lock:
				dialog = OverwriteFileDialog(self._application, self._dialog.get_window())

				title_element = os.path.basename(path)
				message_element = os.path.basename(os.path.dirname(os.path.join(self._destination.get_path(), path)))

				dialog.set_title_element(title_element)
				dialog.set_message_element(message_element)
				dialog.set_rename_value(title_element)
				dialog.set_source(
								self._source,
								path,
								relative_to=self._source_path
								)
				dialog.set_original(
								self._destination,
								path,
								relative_to=self._destination_path
								)

				result = dialog.get_response()
				overwrite = result[0] == gtk.RESPONSE_YES

			if result[1][OverwriteOption.APPLY_TO_ALL]:
				self._overwrite_all = overwrite

			# in case user canceled operation
			if result[0] == gtk.RESPONSE_CANCEL:
				self.cancel()

			# pass options from input dialog
			options = result[1]

		return overwrite, options

	def _get_write_error_input(self, error):
		"""Get user response for write error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = OperationError.RESPONSE_SKIP

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				dialog.set_message(_(
						'There is a problem writing data to destination '
						'file. What would you like to do?'
					))
				dialog.set_error(str(error))

				# get users response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.WRITE] = response

				# abort operation if user requested
				if response == OperationError.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_create_error_input(self, error, is_directory=False):
		"""Get user response for create error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = OperationError.RESPONSE_SKIP

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				if not is_directory:
					# set message for file
					dialog.set_message(_(
						'An error occurred while trying to create specified '
						'file. What would you like to do?'
					))

				else:
					# set message for directory
					dialog.set_message(_(
						'An error occurred while trying to create specified '
						'directory. What would you like to do?'
					))

				dialog.set_error(str(error))

				# get user response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.CREATE] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_mode_set_error_input(self, error):
		"""Get user response for mode set error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = OperationError.RESPONSE_SKIP

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				dialog.set_message(_(
						'Problem with setting path parameter for '
						'specified path. What would you like to do?'
					))

				dialog.set_error(str(error))

				# get user response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.MODE_SET] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_remove_error_input(self, error):
		"""Get user response for remove error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = OperationError.RESPONSE_SKIP

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				dialog.set_message(_(
						'There was a problem removing specified path. '
						'What would you like to do?'
					))
				dialog.set_error(str(error))

				# get users response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.REMOVE] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_trash_error_input(self, error):
		"""Get user response for remove error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = gtk.RESPONSE_NO

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = QuestionOperationError(self._application)

				dialog.set_message(_(
						'There was a problem trashing specified path. '
						'Would you like to try removing it instead?'
					))
				dialog.set_error(str(error))

				# get users response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.TRASH] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_move_error_input(self, error):
		"""Get user response for move error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = gtk.RESPONSE_NO

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				dialog.set_message(_(
						'There was a problem moving specified path. '
						'What would you like to do?'
					))
				dialog.set_error(str(error))

				# get users response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.MOVE] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_rename_error_input(self, error):
		"""Get user response for rename error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = gtk.RESPONSE_NO

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				dialog.set_message(_(
						'There was a problem renaming specified path. '
						'What would you like to do?'
					))
				dialog.set_error(str(error))

				# get users response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.RENAME] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def _get_read_error_input(self, error):
		"""Get user response for directory listing error"""
		if self._options is not None and self._options[Option.SILENT]:
			# we are in silent mode, set response and log error
			self._error_list.append(str(error))
			response = gtk.RESPONSE_NO

		else:
			# we are not in silent mode, ask user
			with gtk.gdk.lock:
				dialog = OperationError(self._application)

				dialog.set_message(_(
						'There was a problem with reading specified directory. '
						'What would you like to do?'
					))
				dialog.set_error(str(error))

				# get users response
				response = dialog.get_response()

				# check if this response applies to future errors
				if response == OperationError.RESPONSE_SKIP_ALL:
					response = OperationError.RESPONSE_SKIP
					self._response_cache[Skip.READ] = response

				# abort operation if user requested
				if response == gtk.RESPONSE_CANCEL:
					self.cancel()

		return response

	def set_selection(self, item_list):
		"""Set list of selected items"""
		self._selection_list.extend(item_list)

	def set_operation_queue(self, queue_name):
		"""Set operation to wait for queue."""
		if queue_name is None:
			return

		# create new queue
		self._operation_queue = Event()
		self._operation_queue_name = queue_name

		# schedule operation
		OperationQueue.add(queue_name, self._operation_queue)

	def set_source_queue(self, queue):
		"""Set event queue for fall-back monitor support"""
		self._source_queue = queue

	def set_destination_queue(self, queue):
		"""Set event queue for fall-back monitor support"""
		self._destination_queue = queue

	def pause(self):
		"""Pause current operation"""
		self._can_continue.clear()

	def resume(self):
		"""Resume current operation"""
		self._can_continue.set()

	def cancel(self):
		"""Set an abort switch"""
		self._abort.set()

		# release lock set by the pause
		if not self._can_continue.is_set():
			self.resume()


class CopyOperation(Operation):
	"""Operation thread used for copying files"""

	def __init__(self, application, source, destination, options, destination_path=None):
		Operation.__init__(self, application, source, destination, options, destination_path)

		self._merge_all = None
		self._overwrite_all = None
		self._dir_list_create = []

		self._total_count = 0
		self._total_size = 0
		self._buffer_size = 0

		# cache settings
		should_reserve = self._application.options.section('operations').get('reserve_size')
		supported_by_provider = ProviderSupport.RESERVE_SIZE in self._destination.get_support()
		self._reserve_size = should_reserve and supported_by_provider

		# detect buffer size
		if self._source.is_local and self._destination.is_local:
			system_stat = self._destination.get_system_size(self._destination_path)

			if system_stat.block_size:
				self._buffer_size = system_stat.block_size * 1024
			else:
				self._buffer_size = BufferSize.LOCAL
		else:
			self._buffer_size = BufferSize.REMOTE

	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = CopyDialog(self._application, self)

	def _update_status(self, status):
		"""Set status and reset progress bars"""
		self._dialog.set_status(status)
		self._dialog.set_current_file("")
		self._dialog.set_current_file_fraction(0)

	def _get_lists(self):
		"""Find all files for copying"""
		gobject.idle_add(self._update_status, _('Searching for files...'))

		# exclude files already selected with parent directory
		for file_name in self._selection_list:
			self._selection_list = filter(
					lambda item: not item.startswith(file_name + os.path.sep),
					self._selection_list
				)

		# traverse through the rest of the items
		for item in self._selection_list:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			# update current file label
			gobject.idle_add(self._dialog.set_current_file, item)
			gobject.idle_add(self._dialog.pulse)

			if os.path.sep in item:
				relative_path, item = os.path.split(item)
				source_path = os.path.join(self._source_path, relative_path)
			else:
				relative_path = None
				source_path = self._source_path

			if self._source.is_dir(item, relative_to=source_path):
				# item is directory
				can_procede = True
				can_create = True

				# check if directory exists on destination
				if self._destination.exists(item, relative_to=self._destination_path):
					can_create = False

					if self._merge_all is not None:
						can_procede = self._merge_all
					else:
						can_procede = self._get_merge_input(item)

				# if user didn't skip directory, scan and update lists
				if can_procede:
					self._dir_list.append((item, relative_path))
					if can_create: self._dir_list_create.append((item, relative_path))
					self._scan_directory(item, relative_path)

			elif fnmatch.fnmatch(item, self._options[Option.FILE_TYPE]):
				# item is a file, get stats and update lists
				item_stat = self._source.get_stat(item, relative_to=source_path)

				gobject.idle_add(self._dialog.increment_total_size, item_stat.size)
				gobject.idle_add(self._dialog.increment_total_count, 1)

				self._total_count += 1
				self._total_size += item_stat.size

				self._file_list.append((item, relative_path))

	def _set_mode(self, path, mode):
		"""Set mode for specified path"""
		if not self._options[Option.SET_MODE]: return

		try:
			# try to set mode for specified path
			self._destination.set_mode(
				                    path,
				                    mode,
				                    relative_to=self._destination_path
				                )

			# push event to the queue
			if self._destination_queue is not None:
				event = (MonitorSignals.ATTRIBUTE_CHANGED, path, None)
				self._destination_queue.put(event, False)

		except StandardError as error:
			# problem setting mode, ask user
			if Skip.MODE_SET in self._response_cache:
				response = self._response_cache[Skip.MODE_SET]
			else:
				response = self._get_mode_set_error_input(error)

			# try to set mode again
			if response == OperationError.RESPONSE_RETRY:
				self._set_mode(path, mode)

			return

	def _set_owner(self, path, user_id, group_id):
		"""Set owner and group for specified path"""
		if not self._options[Option.SET_OWNER]: return

		try:
			# try set owner of specified path
			self._destination.set_owner(
				                    path,
				                    user_id,
				                    group_id,
				                    relative_to=self._destination_path
				                )

			# push event to the queue
			if self._destination_queue is not None:
				event = (MonitorSignals.ATTRIBUTE_CHANGED, path, None)
				self._destination_queue.put(event, False)

		except StandardError as error:
			# problem with setting owner, ask user
			if Skip.MODE_SET in self._response_cache:
				response = self._response_cache[Skip.MODE_SET]
			else:
				response = self._get_mode_set_error_input(error)

			# try to set owner again
			if response == OperationError.RESPONSE_RETRY:
				self._set_owner(path, user_id, group_id)

			return

	def _set_timestamp(self, path, access_time, modify_time, change_time):
		"""Set timestamps for specified path"""
		if not self._options[Option.SET_TIMESTAMP]: return

		try:
			# try setting timestamp
			self._destination.set_timestamp(
									path,
									access_time,
									modify_time,
									change_time,
									relative_to=self._destination_path
								)

			# push event to the queue
			if self._destination_queue is not None:
				event = (MonitorSignals.ATTRIBUTE_CHANGED, path, None)
				self._destination_queue.put(event, False)

		except StandardError as error:
			# problem with setting owner, ask user
			if Skip.MODE_SET in self._response_cache:
				response = self._response_cache[Skip.MODE_SET]
			else:
				response = self._get_mode_set_error_input(error)

			# try to set timestamp again
			if response == OperationError.RESPONSE_RETRY:
				self._set_timestamp(path, access_time, modify_time, change_time)

			return

	def _scan_directory(self, directory, relative_path=None):
		"""Recursively scan directory and populate list"""
		source_path = self._source_path if relative_path is None else os.path.join(self._source_path, relative_path)
		try:
			# try to get listing from directory
			item_list = self._source.list_dir(directory, relative_to=source_path)

		except StandardError as error:
			# problem with reading specified directory, ask user
			if Skip.READ in self._response_cache:
				response = self._response_cache[Skip.READ]
			else:
				response = self._get_read_error_input(error)

			# try to scan specified directory again
			if response == OperationError.RESPONSE_RETRY:
				self._scan_directory(directory, relative_path)

			return

		for item in item_list:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, os.path.join(directory, item))
			gobject.idle_add(self._dialog.pulse)

			full_name = os.path.join(directory, item)

			# item is a directory, scan it
			if self._source.is_dir(full_name, relative_to=source_path):
				can_procede = True
				can_create = True

				if self._destination.exists(full_name, relative_to=self._destination_path):
					can_create = False

					if self._merge_all is not None:
						can_procede = self._merge_all
					else:
						can_procede = self._get_merge_input(full_name)

				if can_procede:
					# allow processing specified directory
					self._dir_list.append((full_name, source_path))
					if can_create: self._dir_list_create.append((full_name, source_path))
					self._scan_directory(full_name, relative_path)

			elif fnmatch.fnmatch(item, self._options[Option.FILE_TYPE]):
				# item is a file, update global statistics
				item_stat = self._source.get_stat(full_name, relative_to=source_path)

				gobject.idle_add(self._dialog.increment_total_size, item_stat.size)
				gobject.idle_add(self._dialog.increment_total_count, 1)

				self._total_count += 1
				self._total_size += item_stat.size

				self._file_list.append((full_name, relative_path))

	def _create_directory(self, directory, relative_path=None):
		"""Create specified directory"""
		source_path = self._source_path if relative_path is None else os.path.join(self._source_path, relative_path)
		file_stat = self._source.get_stat(directory, relative_to=source_path)
		mode = file_stat.mode if self._options[Option.SET_MODE] else 0755

		try:
			# try to create a directory
			if self._destination.exists(directory, relative_to=self._destination_path):
				if not self._destination.is_dir(directory, relative_to=self._destination_path):
					raise StandardError(_(
							'Unable to create directory because file with the same name '
							'already exists in target directory.'
						))

			else:
				# inode with specified name doesn't exist, create directory
				self._destination.create_directory(
												directory,
												mode,
												relative_to=self._destination_path
											)
			# push event to the queue
			if self._destination_queue is not None:
				event = (MonitorSignals.CREATED, directory, None)
				self._destination_queue.put(event, False)

		except StandardError as error:
			# there was a problem creating directory
			if Skip.CREATE in self._response_cache:
				response = self._response_cache[Skip.CREATE]
			else:
				response = self._get_create_error_input(error, True)

			# try to create directory again
			if response == OperationError.RESPONSE_RETRY:
				self._create_directory(directory)

			# exit method
			return

		# set owner
		self._set_owner(directory, file_stat.user_id, file_stat.group_id)

	def _copy_file(self, file_name, relative_path=None):
		"""Copy file content"""
		can_procede = True
		source_path = self._source_path if relative_path is None else os.path.join(self._source_path, relative_path)
		dest_file = file_name
		sh = None
		dh = None

		# check if destination file exists
		if self._destination.exists(file_name, relative_to=self._destination_path):
			if self._overwrite_all is not None:
				can_procede = self._overwrite_all

			else:
				can_procede, options = self._get_overwrite_input(file_name)

				# get new name if user specified
				if options[OverwriteOption.RENAME]:
					dest_file = os.path.join(
					                    os.path.dirname(file_name),
					                    options[OverwriteOption.NEW_NAME]
					                )

				elif source_path == self._destination_path:
					can_procede = False

		# if user skipped this file return
		if not can_procede:
			self._file_list.pop(self._file_list.index((file_name, relative_path)))

			# update total size
			file_stat = self._source.get_stat(file_name, relative_to=source_path)
			gobject.idle_add(self._dialog.increment_current_size, file_stat.size)
			return

		try:
			# get file stats
			destination_size = 0L
			file_stat = self._source.get_stat(file_name, relative_to=source_path, extended=True)

			# get file handles
			sh = self._source.get_file_handle(file_name, FileMode.READ, relative_to=source_path)
			dh = self._destination.get_file_handle(dest_file, FileMode.WRITE, relative_to=self._destination_path)

			# report error properly
			if sh is None:
				raise StandardError('Unable to open source file in read mode.')

			if dh is None:
				raise StandardError('Unable to open destination file in write mode.')

			# reserve file size
			if self._reserve_size:
				# try to reserve file size in advance,
				# can be slow on memory cards and network
				try:
					dh.truncate(file_stat.size)

				except:
					dh.truncate()

			else:
				# just truncate file to 0 size in case source file is smaller
				dh.truncate()

			dh.seek(0)

			# push event to the queue
			if self._destination_queue is not None:
				event = (MonitorSignals.CREATED, dest_file, None)
				self._destination_queue.put(event, False)

		except StandardError as error:
			# close handles if they exist
			if hasattr(sh, 'close'): sh.close()
			if hasattr(dh, 'close'): sh.close()

			if Skip.CREATE in self._response_cache:
				response = self._response_cache[Skip.CREATE]
			else:
				response = self._get_create_error_input(error)

			# try to create file again and copy contents
			if response == OperationError.RESPONSE_RETRY:
				self._copy_file(dest_file)

			else:
				# user didn't want to retry, remove file from list
				self._file_list.pop(self._file_list.index((file_name, relative_path)))

			# remove amount of copied bytes from total size
			gobject.idle_add(self._dialog.increment_current_size, -destination_size)

			# exit method
			return

		while True:
			if self._abort.is_set(): break
			self._can_continue.wait()  # pause lock

			data = sh.read(self._buffer_size)

			if data:
				try:
					# try writing data to destination
					dh.write(data)

				except IOError as error:
					# handle error
					if Skip.WRITE in self._response_cache:
						response = self._response_cache[Skip.WRITE]
					else:
						response = self._get_write_error_input(error)

					# try to write data again
					if response == OperationError.RESPONSE_RETRY:
						gobject.idle_add(self._dialog.increment_current_size, -dh.tell())
						if hasattr(sh, 'close'): sh.close()
						if hasattr(dh, 'close'): sh.close()

						self._copy_file(dest_file)

					return

				destination_size += len(data)
				gobject.idle_add(self._dialog.increment_current_size, len(data))
				if file_stat.size > 0:  # ensure we don't end up with error on 0 size files
					gobject.idle_add(
									self._dialog.set_current_file_fraction,
									destination_size / float(file_stat.size)
								)
				else:
					gobject.idle_add(self._dialog.set_current_file_fraction, 1)

				# push event to the queue
				if self._destination_queue is not None:
					event = (MonitorSignals.CHANGED, dest_file, None)
					self._destination_queue.put(event, False)

			else:
				sh.close()
				dh.close()

				# set file parameters
				self._set_mode(dest_file, file_stat.mode)
				self._set_owner(dest_file, file_stat.user_id, file_stat.group_id)
				self._set_timestamp(
								dest_file,
								file_stat.time_access,
								file_stat.time_modify,
								file_stat.time_change
							)

				break

	def _create_directory_list(self):
		"""Create all directories in list"""
		gobject.idle_add(self._update_status, _('Creating directories...'))

		for number, directory in enumerate(self._dir_list_create, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, directory[0])
			self._create_directory(directory[0], directory[1])  # create directory

			gobject.idle_add(
						self._dialog.set_current_file_fraction,
						float(number) / len(self._dir_list)
					)

	def _copy_file_list(self):
		"""Copy list of files to destination path"""
		# update status
		gobject.idle_add(self._update_status, _('Copying files...'))

		item_list = self._file_list[:]

		# copy all the files in list
		for file_name, source_path in item_list:
			# abort operation if requested
			if self._abort.is_set(): break
			self._can_continue.wait()  # pause lock

			# copy file
			gobject.idle_add(self._dialog.set_current_file, file_name)
			self._copy_file(file_name, source_path)
			gobject.idle_add(self._dialog.increment_current_count, 1)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		# set dialog info
		with gtk.gdk.lock:
			self._dialog.set_source(self._source_path)
			self._dialog.set_destination(self._destination_path)

		# wait for operation queue if needed
		if self._operation_queue is not None:
			self._operation_queue.wait()

		# get list of items to copy
		self._get_lists()

		# check for available free space
		system_info = self._destination.get_system_size(self._destination_path)

		if ProviderSupport.SYSTEM_SIZE in self._destination.get_support() \
		and self._total_size > system_info.size_available:
			should_continue = self._get_free_space_input(self._total_size, system_info.size_available)

			# exit if user chooses to
			if not should_continue:
				self.cancel()

		# clear selection on source directory
		with gtk.gdk.lock:
			parent = self._source.get_parent()
			if self._source_path == parent.path:
				parent.deselect_all()

		# perform operation
		self._create_directory_list()
		self._copy_file_list()

		# notify user if window is not focused
		with gtk.gdk.lock:
			if not self._dialog.is_active() and not self._application.is_active() and not self._abort.is_set():
				notify_manager = self._application.notification_manager

				title = _('Copy Operation')
				message = ngettext(
								'Copying of {0} item from "{1}" to "{2}" is completed!',
								'Copying of {0} items from "{1}" to "{2}" is completed!',
								len(self._file_list) + len(self._dir_list)
							).format(
								len(self._file_list) + len(self._dir_list),
								os.path.basename(self._source_path),
								os.path.basename(self._destination_path)
							)

				# queue notification
				notify_manager.notify(title, message)

			# show error list if needed
			if len(self._error_list) > 0:
				error_list = ErrorList(self._dialog)
				error_list.set_operation_name(_('Copy Operation'))
				error_list.set_source(self._source_path)
				error_list.set_destination(self._destination_path)
				error_list.set_errors(self._error_list)
				error_list.show()

		# destroy dialog
		self._destroy_ui()

		# start next operation
		if self._operation_queue is not None:
			OperationQueue.start_next(self._operation_queue_name)


class MoveOperation(CopyOperation):
	"""Operation thread used for moving files"""

	def _remove_path(self, path, item_list, relative_path=None):
		"""Remove path specified path."""
		source_path = self._source_path if relative_path is None else os.path.join(self._source_path, relative_path)

		try:
			# try removing specified path
			self._source.remove_path(path, relative_to=source_path)

			# push event to the queue
			if self._source_queue is not None:
				event = (MonitorSignals.DELETED, path, None)
				self._source_queue.put(event, False)

		except StandardError as error:
			# problem removing path, ask user what to do
			if Skip.REMOVE in self._response_cache:
				response = self._response_cache[Skip.REMOVE]
			else:
				response = self._get_remove_error_input(error)

			# try removing path again
			if response == OperationError.RESPONSE_RETRY:
				self._remove_path(path, item_list)

			else:
				# user didn't want to retry, remove path from item_list
				item_list.pop(item_list.index(path))

	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = MoveDialog(self._application, self)

	def _move_file(self, file_name, relative_path=None):
		"""Move specified file using provider rename method"""
		can_procede = True
		source_path = self._source_path if relative_path is None else os.path.join(self._source_path, relative_path)
		dest_file = file_name

		# check if destination file exists
		if self._destination.exists(file_name, relative_to=self._destination_path):
			if self._overwrite_all is not None:
				can_procede = self._overwrite_all
			else:
				can_procede, options = self._get_overwrite_input(file_name)

				# get new name if user specified
				if options[OverwriteOption.RENAME]:
					dest_file = os.path.join(
					                    os.path.dirname(file_name),
					                    options[OverwriteOption.NEW_NAME]
					                )

		# if user skipped this file return
		if not can_procede:
			self._file_list.pop(self._file_list.index((file_name, relative_path)))
			return

		# move file
		try:
			self._source.move_path(
								file_name,
								os.path.join(self._destination_path, dest_file),
								relative_to=source_path
							)

			# push events to the queue
			if self._source_queue is not None:
				event = (MonitorSignals.DELETED, file_name, None)
				self._source_queue.put(event, False)

			if self._destination_queue is not None:
				event = (MonitorSignals.CREATED, dest_file, None)
				self._destination_queue.put(event, False)

		except StandardError as error:
			# problem with moving file, ask user what to do
			if Skip.MOVE in self._response_cache:
				response = self._response_cache[Skip.MOVE]
			else:
				response = self._get_move_error_input(error)

			# try moving file again
			if response == OperationError.RESPONSE_RETRY:
				self._move_file(dest_file)

			else:
				# user didn't want to retry, remove file from list
				self._file_list.pop(self._file_list.index((file_name, relative_path)))

			# exit method
			return

	def _move_file_list(self):
		"""Move files from the list"""
		gobject.idle_add(self._update_status, _('Moving files...'))

		item_list = self._file_list[:]
		for file_name, source_path in item_list:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			# move file
			gobject.idle_add(self._dialog.set_current_file, file_name)
			self._move_file(file_name, source_path)
			gobject.idle_add(self._dialog.increment_current_count, 1)

	def _delete_file_list(self):
		"""Remove files from source list"""
		gobject.idle_add(self._update_status, _('Deleting source files...'))

		item_list = self._file_list[:]

		for number, item in enumerate(item_list, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			# remove path
			gobject.idle_add(self._dialog.set_current_file, item[0])
			self._remove_path(item[0], self._file_list, item[1])

			# update current count
			gobject.idle_add(
						self._dialog.set_current_file_fraction,
						float(number) / len(item_list)
					)

		self._delete_directories()

	def _delete_directories(self):
		"""Remove empty directories after moving files"""
		gobject.idle_add(self._update_status, _('Deleting source directories...'))

		dir_list = self._dir_list[:]
		dir_list.reverse()  # remove deepest directories first

		for number, directory in enumerate(dir_list, 0):
			source_path = self._source_path if directory[1] is None else os.path.join(self._source_path, directory[1])
			directory = directory[0]
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			if self._source.exists(directory, relative_to=source_path):
				gobject.idle_add(self._dialog.set_current_file, directory)

				# try to get a list of items inside of directory
				try:
					item_list = self._source.list_dir(directory, relative_to=source_path)

				except:
					item_list = None

				# remove directory if empty
				if item_list is not None and len(item_list) == 0:
					self._remove_path(directory, dir_list, relative_path=source_path)

				# update current count
				if len(dir_list) > 0:
					gobject.idle_add(
								self._dialog.set_current_file_fraction,
								float(number) / len(dir_list)
							)

				else:
					# prevent division by zero
					gobject.idle_add(self._dialog.set_current_file_fraction, 1)

	def _check_devices(self):
		"""Check if source and destination are on the same file system"""
		dev_source = self._source.get_stat(self._source.get_path(), extended=True).device
		dev_destination = self._destination.get_stat(self._destination.get_path(), extended=True).device

		return dev_source == dev_destination

	def run(self):
		"""Main thread method

		We override this method from CopyDialog in order to provide
		a bit smarter move operation.

		"""
		# set dialog info
		with gtk.gdk.lock:
			self._dialog.set_source(self._source_path)
			self._dialog.set_destination(self._destination_path)

		# wait for operation queue if needed
		if self._operation_queue is not None:
			self._operation_queue.wait()

		# get list of items
		self._get_lists()

		# check for available free space
		system_info = self._destination.get_system_size(self._destination_path)

		if self._total_size > system_info.size_available and not self._check_devices():
			should_continue = self._get_free_space_input(self._total_size, system_info.size_available)

			# exit if user chooses to
			if not should_continue:
				self.cancel()

		# clear selection on source directory
		with gtk.gdk.lock:
			parent = self._source.get_parent()
			if self._source_path == parent.path:
				parent.deselect_all()

		# create directories
		self._create_directory_list()

		# copy/move files
		if self._check_devices():
			# both paths are on the same file system, move instead of copy
			self._move_file_list()
			self._delete_directories()

		else:
			# paths are located on different file systems, copy and remove
			self._copy_file_list()
			self._delete_file_list()

		# notify user if window is not focused
		with gtk.gdk.lock:
			if not self._dialog.is_active() and not self._application.is_active() and not self._abort.is_set():
				notify_manager = self._application.notification_manager

				title = _('Move Operation')
				message = ngettext(
								'Moving of {0} item from "{1}" to "{2}" is completed!',
								'Moving of {0} items from "{1}" to "{2}" is completed!',
								len(self._file_list) + len(self._dir_list)
							).format(
								len(self._file_list) + len(self._dir_list),
								os.path.basename(self._source_path),
								os.path.basename(self._destination_path)
							)

				# queue notification
				notify_manager.notify(title, message)

			# shop error list if needed
			if len(self._error_list) > 0:
				error_list = ErrorList(self._dialog)
				error_list.set_operation_name(_('Move Operation'))
				error_list.set_source(self._source_path)
				error_list.set_destination(self._destination_path)
				error_list.set_errors(self._error_list)
				error_list.show()

		# destroy dialog
		self._destroy_ui()

		# start next operation
		if self._operation_queue is not None:
			OperationQueue.start_next(self._operation_queue_name)


class DeleteOperation(Operation):
	"""Operation thread used for deleting files"""

	def __init__(self, application, provider):
		Operation.__init__(self, application, provider)

		# allow users to force deleting items
		self._force_delete = False

	def _create_dialog(self):
		"""Create operation dialog"""
		self._dialog = DeleteDialog(self._application, self)

	def _remove_path(self, path):
		"""Remove path"""
		try:
			# try removing specified path
			self._source.remove_path(path, relative_to=self._source_path)

			# push event to the queue
			if self._source_queue is not None:
				event = (MonitorSignals.DELETED, path, None)
				self._source_queue.put(event, False)

		except StandardError as error:
			# problem removing path, ask user what to do
			if Skip.REMOVE in self._response_cache:
				response = self._response_cache[Skip.REMOVE]
			else:
				response = self._get_remove_error_input(error)

			# try removing path again
			if response == OperationError.RESPONSE_RETRY:
				self._remove_path(path)

	def _trash_path(self, path):
		"""Move path to the trash"""
		try:
			# try trashing specified path
			self._source.trash_path(path, relative_to=self._source_path)

			# push event to the queue
			if self._source_queue is not None:
				event = (MonitorSignals.DELETED, path, None)
				self._source_queue.put(event, False)

		except TrashError as error:
			# problem removing path, ask user what to do
			if Skip.TRASH in self._response_cache:
				response = self._response_cache[Skip.TRASH]
			else:
				response = self._get_trash_error_input(error)

			# try moving path to trash again
			if response == OperationError.RESPONSE_RETRY:
				self._remove_path(path)

	def set_force_delete(self, force):
		"""Set forced deletion instead of trashing files"""
		self._force_delete = force

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._file_list = self._selection_list[:]  # use predefined selection list

		# wait for operation queue if needed
		if self._operation_queue is not None:
			self._operation_queue.wait()

		with gtk.gdk.lock:
			# clear selection on source directory
			parent = self._source.get_parent()
			if self._source_path == parent.path:
				parent.deselect_all()

		# select removal method
		trash_files = self._application.options.section('operations').get('trash_files')
		trash_available = ProviderSupport.TRASH in self._source.get_support()

		if self._force_delete:
			remove_method = self._remove_path

		else:
			remove_method = (
					self._remove_path,
					self._trash_path
				)[trash_files and trash_available]

		# remove them
		for index, item in enumerate(self._file_list, 1):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, item)
			remove_method(item)

			# update current count
			if len(self._file_list) > 0:
				gobject.idle_add(
							self._dialog.set_current_file_fraction,
							float(index) / len(self._file_list)
						)

			else:
				# prevent division by zero
				gobject.idle_add(self._dialog.set_current_file_fraction, 1)

		# notify user if window is not focused
		with gtk.gdk.lock:
			if not self._dialog.is_active() and not self._application.is_active() and not self._abort.is_set():
				notify_manager = self._application.notification_manager

				title = _('Delete Operation')
				message = ngettext(
								'Removal of {0} item from "{1}" is completed!',
								'Removal of {0} items from "{1}" is completed!',
								len(self._file_list)
							).format(
				        len(self._file_list),
				        os.path.basename(self._source_path)
				    )

				# queue notification
				notify_manager.notify(title, message)

		# destroy dialog
		self._destroy_ui()

		# start next operation
		if self._operation_queue is not None:
			OperationQueue.start_next(self._operation_queue_name)


class RenameOperation(Operation):
	"""Thread used for rename of large number of files"""

	def __init__(self, application, provider, path, file_list):
		Operation.__init__(self, application, provider)

		self._destination = provider
		self._destination_path = path
		self._source_path = path
		self._file_list = file_list

	def _create_dialog(self):
		"""Create operation dialog"""
		self._dialog = RenameDialog(self._application, self)

	def _rename_path(self, old_name, new_name, index):
		"""Rename specified path"""
		can_procede = True

		try:
			# check if specified path already exists
			if self._destination.exists(new_name, relative_to=self._source_path):
				can_procede, options = self._get_overwrite_input(new_name)

				# get new name if user specified
				if options[OverwriteOption.RENAME]:
					new_name = os.path.join(
					                    os.path.dirname(new_name),
					                    options[OverwriteOption.NEW_NAME]
					                )

			if not can_procede:
				# user canceled overwrite, skip the file
				self._file_list.pop(index)
				return

			else:
				# rename path
				self._source.rename_path(old_name, new_name, relative_to=self._source_path)

				# push event to the queue
				if self._source_queue is not None:
					delete_event = (MonitorSignals.DELETE, old_name, None)
					create_event = (MonitorSignals.CREATED, new_name, None)

					self._source_queue.put(delete_event, False)
					self._source_queue.put(create_event, False)

		except StandardError as error:
			# problem renaming path, ask user what to do
			if Skip.RENAME in self._response_cache:
				response = self._response_cache[Skip.RENAME]
			else:
				response = self._get_rename_error_input(error)

			# try renaming path again
			if response == OperationError.RESPONSE_RETRY:
				self._remove_path(old_name, new_name, index)

			else:
				# user didn't want to retry, remove path from list
				self._file_list.pop(index)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		# wait for operation queue if needed
		if self._operation_queue is not None:
			self._operation_queue.wait()

		for index, item in enumerate(self._file_list, 1):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, item[0])
			self._rename_path(item[0], item[1], index-1)

			# update current count
			if len(self._file_list) > 0:
				gobject.idle_add(
							self._dialog.set_current_file_fraction,
							float(index) / len(self._file_list)
						)

			else:
				# prevent division by zero
				gobject.idle_add(self._dialog.set_current_file_fraction, 1)

		# notify user if window is not focused
		with gtk.gdk.lock:
			if not self._dialog.is_active() and not self._application.is_active() and not self._abort.is_set():
				notify_manager = self._application.notification_manager

				title = _('Rename Operation')
				message = ngettext(
								'Rename of {0} item from "{1}" is completed!',
								'Rename of {0} items from "{1}" is completed!',
								len(self._file_list)
							).format(
				        len(self._file_list),
				        os.path.basename(self._source_path)
				    )

				# queue notification
				notify_manager.notify(title, message)

		# destroy dialog
		self._destroy_ui()

		# start next operation
		if self._operation_queue is not None:
			OperationQueue.start_next(self._operation_queue_name)
