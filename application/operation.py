import os
import gtk
import gobject
import fnmatch

from threading import Thread, Event
from gui.input_dialog import OverwriteFileDialog, OverwriteDirectoryDialog, OperationError
from gui.operation_dialog import CopyDialog, MoveDialog, DeleteDialog, RenameDialog

# import constants
from gui.input_dialog import OverwriteOption

# constants
COPY_BUFFER = 100 * 1024

class Option:
	FILE_TYPE = 0
	DESTINATION = 1
	SET_OWNER = 2
	SET_MODE = 3


class Operation(Thread):
	"""Parent class for all operation threads"""

	def __init__(self, application, source, destination=None):
		Thread.__init__(self, target=self)

		self._can_continue = Event()
		self._abort = Event()
		self._application = application
		self._source = source
		self._destination = destination

		# create operation dialog
		self._dialog = None
		self._create_dialog()

		self._dir_list = []
		self._file_list = []

		# store initial paths
		self._source_path = self._source.get_path()
		if self._destination is not None:
			self._destination_path = self._destination.get_path()

		self._can_continue.set()
		
	def _create_dialog(self):
		"""Create operation dialog"""
		pass

	def _destroy_ui(self):
		"""Destroy user interface"""
		if self._dialog is not None:
			with gtk.gdk.lock:
				self._dialog.destroy()

	def _get_merge_input(self, path):
		"""Get merge confirmation"""
		with gtk.gdk.lock:
			dialog = OverwriteDirectoryDialog(self._application, self._dialog)
	
			title_element = os.path.basename(path)
			message_element = os.path.basename(os.path.dirname(
								os.path.join(self._destination.get_path(), path)))
	
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
		with gtk.gdk.lock:
			dialog = OverwriteFileDialog(self._application, self._dialog)
	
			title_element = os.path.basename(path)
			message_element = os.path.basename(os.path.dirname(
								os.path.join(self._destination.get_path(), path)))
	
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

		return overwrite, result[1]

	def _get_write_error_input(self, error):
		"""Get user response for write error"""
		with gtk.gdk.lock:
			dialog = OperationError(self._application)
	
			dialog.set_message(_(
			        'There is a problem writing data to destination '
			        'file. What would you like to do?'
			    ))
			dialog.set_error(str(error))
	
			response = dialog.get_response()
	
			# abort operation if user requested
			if response == gtk.RESPONSE_CANCEL:
				self.cancel()

		return response

	def _get_create_error_input(self, error, is_directory=False):
		"""Get user response for create error"""
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
	
			# abort operation if user requested
			if response == gtk.RESPONSE_CANCEL:
				self.cancel()

		return response

	def _get_mode_set_error_input(self, error):
		"""Get user response for mode set error"""
		with gtk.gdk.lock:
			dialog = OperationError(self._application)
	
			dialog.set_message(_(
		            'Problem with setting mode and/or owner for '
		            'specified path. What would you like to do?'
		        ))
	
			dialog.set_error(str(error))
	
			# get user response
			response = dialog.get_response()
	
			# abort operation if user requested
			if response == gtk.RESPONSE_CANCEL:
				self.cancel()

		return response

	def _get_remove_error_input(self, error):
		"""Get user response for remove error"""
		with gtk.gdk.lock:
			dialog = OperationError(self._application)
	
			dialog.set_message(_(
			        'There was a problem removing specified path. '
			        'What would you like to do?'
			    ))
			dialog.set_error(str(error))
	
			response = dialog.get_response()
	
			# abort operation if user requested
			if response == gtk.RESPONSE_CANCEL:
				self.cancel()

		return response

	def _get_move_error_input(self, error):
		"""Get user response for move error"""
		with gtk.gdk.lock:
			dialog = OperationError(self._application)
	
			dialog.set_message(_(
			        'There was a problem moving specified path. '
			        'What would you like to do?'
			    ))
			dialog.set_error(str(error))
	
			response = dialog.get_response()
	
			# abort operation if user requested
			if response == gtk.RESPONSE_CANCEL:
				self.cancel()

		return response

	def _get_rename_error_input(self, error):
		"""Get user response for rename error"""
		with gtk.gdk.lock:
			dialog = OperationError(self._application)
	
			dialog.set_message(_(
			        'There was a problem renaming specified path. '
			        'What would you like to do?'
			    ))
			dialog.set_error(str(error))
	
			response = dialog.get_response()
	
			# abort operation if user requested
			if response == gtk.RESPONSE_CANCEL:
				self.cancel()

		return response

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

	def __init__(self, application, source, destination, options):
		Operation.__init__(self, application, source, destination)

		self._options = options
		self._merge_all = None
		self._overwrite_all = None
		self._dir_list_create = []

		# cache settings
		self._reserve_size = self._application.options.getboolean('main', 'reserve_size')

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
		
		# safely get selection list from parent
		with gtk.gdk.lock:
			item_list = self._source.get_selection(relative=True)

		# traverse through the rest of the items
		for item in item_list:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			# update current file label
			gobject.idle_add(self._dialog.set_current_file, item)
			gobject.idle_add(self._dialog.pulse)

			if self._source.is_dir(item, relative_to=self._source_path):
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
					self._dir_list.append(item)
					if can_create: self._dir_list_create.append(item)
					self._scan_directory(item)

			elif fnmatch.fnmatch(item, self._options[Option.FILE_TYPE]):
				# item is a file, get stats and update lists
				item_stat = self._source.get_stat(item, relative_to=self._source_path)
				gobject.idle_add(self._dialog.increment_total_size, item_stat.size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				self._file_list.append(item)

		# clear selection on source directory
		parent = self._source.get_parent()
		if self._source_path == parent.path:
			parent.unselect_all()

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

		except StandardError as error:
			# problem setting mode, ask user
			response = self._get_mode_set_error_input(error)

			if response == gtk.RESPONSE_YES:
				self._set_mode(path, mode)  # try to set mode again

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

		except StandardError as error:
			# problem with setting owner, ask user
			response = self._get_mode_set_error_input(error)

			if response == gtk.RESPONSE_YES:
				self._set_owner(path, user_id, group_id)  # try to set owner again

			return

	def _scan_directory(self, directory):
		"""Recursively scan directory and populate list"""
		for item in self._source.list_dir(directory, relative_to=self._source_path):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, os.path.join(directory, item))
			gobject.idle_add(self._dialog.pulse)

			full_name = os.path.join(directory, item)

			if self._source.is_dir(full_name, relative_to=self._source_path):
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
					self._dir_list.append(full_name)
					if can_create: self._dir_list_create.append(full_name)
					self._scan_directory(full_name)

			elif fnmatch.fnmatch(item, self._options[Option.FILE_TYPE]):
				item_stat = self._source.get_stat(full_name, relative_to=self._source_path)
				gobject.idle_add(self._dialog.increment_total_size, item_stat.size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				self._file_list.append(full_name)

	def _create_directory(self, directory):
		"""Create specified directory"""
		file_stat = self._source.get_stat(directory, relative_to=self._source_path)
		mode = file_stat.mode if self._options[Option.SET_MODE] else 0755

		try:
			# try to create a directory
			self._destination.create_directory(
			                                directory,
			                                mode,
			                                relative_to=self._destination_path
			                            )

		except StandardError as error:
			# there was a problem creating directory
			response = self._get_create_error_input(error, True)

			# handle user response
			if response == gtk.RESPONSE_YES:
				self._create_directory(directory)

			# exit method
			return

		# set owner
		self._set_owner(directory, file_stat.user_id, file_stat.group_id)

	def _copy_file(self, file_):
		"""Copy file content"""
		can_procede = True
		dest_file = file_
		sh = None
		dh = None

		# check if destination file exists
		if self._destination.exists(file_, relative_to=self._destination_path):
			if self._overwrite_all is not None:
				can_procede = self._overwrite_all

			else:
				can_procede, options = self._get_overwrite_input(file_)

				# get new name if user specified
				if options[OverwriteOption.RENAME]:
					dest_file = os.path.join(
					                    os.path.dirname(file_),
					                    options[OverwriteOption.NEW_NAME]
					                )

		# if user skipped this file return
		if not can_procede:
			self._file_list.pop(self._file_list.index(file_))

			# update total size
			file_stat = self._source.get_stat(file_, relative_to=self._source_path)
			gobject.idle_add(self._dialog.increment_current_size, file_stat.size)
			return

		try:
			# get file stats
			destination_size = 0L
			file_stat = self._source.get_stat(file_, relative_to=self._source_path)

			# get file handles
			sh = self._source.get_file_handle(file_, 'rb', relative_to=self._source_path)
			dh = self._destination.get_file_handle(dest_file, 'wb', relative_to=self._destination_path)

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

		except StandardError as error:
			# close handles if they exist
			if hasattr(sh, 'close'): sh.close()
			if hasattr(dh, 'close'): sh.close()

			response = self._get_create_error_input(error)

			# handle user response
			if response == gtk.RESPONSE_YES:
				self._copy_file(dest_file)  # retry copying this file

			else:
				# user didn't want to retry, remove file from list
				self._file_list.pop(self._file_list.index(file_))

			# remove amount of copied bytes from total size
			gobject.idle_add(self._dialog.increment_current_size, -destination_size)

			# exit method
			return

		while True:
			if self._abort.is_set(): break
			self._can_continue.wait()  # pause lock

			buffer_ = sh.read(COPY_BUFFER)

			if (buffer_):
				dh.write(buffer_)

				destination_size += len(buffer_)
				gobject.idle_add(self._dialog.increment_current_size, len(buffer_))
				if file_stat.size > 0:  # ensure we don't end up with error on 0 size files
					gobject.idle_add(
									self._dialog.set_current_file_fraction,
									destination_size / float(file_stat.size)
								)
				else:
					gobject.idle_add(self._dialog.set_current_file_fraction, 1)

			else:
				sh.close()
				dh.close()

				# set mode if required
				self._set_mode(dest_file, file_stat.mode)

				# set owner if required
				self._set_owner(dest_file, file_stat.user_id, file_stat.group_id)
				break

	def _create_directory_list(self):
		"""Create all directories in list"""
		gobject.idle_add(self._update_status, _('Creating directories...'))

		for number, dir_ in enumerate(self._dir_list_create, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, dir_)
			self._create_directory(dir_)  # create directory

			gobject.idle_add(
						self._dialog.set_current_file_fraction,
						float(number) / len(self._dir_list)
					)

	def _copy_file_list(self):
		"""Copy list of files to destination path"""
		# update status
		gobject.idle_add(self._update_status, _('Copying files...'))

		list_ = self._file_list[:]

		# copy all the files in list
		for file_ in list_:
			# abort operation if requested
			if self._abort.is_set(): break
			self._can_continue.wait()  # pause lock

			# copy file
			gobject.idle_add(self._dialog.set_current_file, file_)
			self._copy_file(file_)
			gobject.idle_add(self._dialog.increment_current_count, 1)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		# set dialog info
		with gtk.gdk.lock:
			self._dialog.set_source(self._source_path)
			self._dialog.set_destination(self._destination_path)

		# get list of items to copy
		self._get_lists()

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

		# destroy dialog
		self._destroy_ui()


class MoveOperation(CopyOperation):
	"""Operation thread used for moving files"""

	def _remove_path(self, path, item_list):
		"""Remove path"""
		try:
			# try removing specified path
			self._source.remove_path(path, relative_to=self._source_path)

		except StandardError as error:
			# problem removing path, ask user what to do
			response = self._get_remove_error_input(error)

			# handle user response
			if response == gtk.RESPONSE_YES:
				self._remove_path(path, item_list)  # retry removing path

			else:
				# user didn't want to retry, remove path from item_list
				item_list.pop(item_list.index(path))

	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = MoveDialog(self._application, self)

	def _move_file(self, file_):
		"""Move specified file using provider rename method"""
		can_procede = True
		dest_file = file_

		# check if destination file exists
		if self._destination.exists(file_, relative_to=self._destination_path):
			if self._overwrite_all is not None:
				can_procede = self._overwrite_all
			else:
				can_procede, options = self._get_overwrite_input(file_)

				# get new name if user specified
				if options[OverwriteOption.RENAME]:
					dest_file = os.path.join(
					                    os.path.dirname(file_),
					                    options[OverwriteOption.NEW_NAME]
					                )

		# if user skipped this file return
		if not can_procede:
			self._file_list.pop(self._file_list.index(file_))
			return

		# move file
		try:
			self._source.rename_path(
								file_,
								os.path.join(self._destination_path, dest_file),
								relative_to=self._source_path
							)

		except StandardError as error:
			# problem with moving file, ask user what to do
			response = self._get_move_error_input(error)

			# handle user response
			if response == gtk.RESPONSE_YES:
				self._move_file(dest_file)  # retry copying this file

			else:
				# user didn't want to retry, remove file from list
				self._file_list.pop(self._file_list.index(file_))

			# exit method
			return

	def _move_file_list(self):
		"""Move files from the list"""
		gobject.idle_add(self._update_status, _('Moving files...'))

		list_ = self._file_list[:]

		for file_ in list_:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			# move file
			gobject.idle_add(self._dialog.set_current_file, file_)
			self._move_file(file_)
			gobject.idle_add(self._dialog.increment_current_count, 1)

	def _delete_file_list(self):
		"""Remove files from source list"""
		gobject.idle_add(self._update_status, _('Deleting source files...'))

		list_ = self._file_list[:]

		for number, item in enumerate(list_, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			# remove path
			gobject.idle_add(self._dialog.set_current_file, item)
			self._remove_path(item, self._file_list)

			# update current count
			gobject.idle_add(
						self._dialog.set_current_file_fraction,
						float(number) / len(list_)
					)

		self._delete_directories()

	def _delete_directories(self):
		"""Remove empty directories after moving files"""
		gobject.idle_add(self._update_status, _('Deleting source directories...'))

		dir_list = self._dir_list[:]
		dir_list.reverse()  # remove deepest directories first

		for number, directory in enumerate(dir_list, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			if self._source.exists(directory, relative_to=self._source_path):
				gobject.idle_add(self._dialog.set_current_file, directory)

				# remove directory only if it's empty
				if len(self._source.list_dir(directory, relative_to=self._source_path)) == 0:
					self._remove_path(directory, dir_list)

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

		self._get_lists()

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

		# destroy dialog
		self._destroy_ui()


class DeleteOperation(Operation):
	"""Operation thread used for deleting files"""

	def __init__(self, application, provider):
		Operation.__init__(self, application, provider)
		
	def _create_dialog(self):
		"""Create operation dialog"""
		self._dialog = DeleteDialog(self._application, self)

	def _remove_path(self, path):
		"""Remove path"""
		try:
			# try removing specified path
			self._source.remove_path(path, relative_to=self._source_path)

		except StandardError as error:
			# problem removing path, ask user what to do
			response = self._get_remove_error_input(error)

			# handle user response
			if response == gtk.RESPONSE_YES:
				self._remove_path(path)  # retry removing path

			else:
				# user didn't want to retry, remove path from list
				self._file_list.pop(self._file_list.index(path))

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		# get selected items
		with gtk.gdk.lock:
			self._file_list = self._source.get_selection(relative=True)

			# clear selection on source directory
			parent = self._source.get_parent()
			if self._source_path == parent.path:
				parent.unselect_all()

		# remove them
		for index, item in enumerate(self._file_list, 1):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()  # pause lock

			gobject.idle_add(self._dialog.set_current_file, item)
			self._remove_path(item)

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


class RenameOperation(Operation):
	"""Thread used for rename of large number of files"""

	def __init__(self, application, provider, path, file_list):
		Operation.__init__(self, application, provider)

		self._source_path = path
		self._file_list = file_list
		
	def _create_dialog(self):
		"""Create operation dialog"""
		self._dialog = RenameDialog(self._application, self)

	def _rename_path(self, old_name, new_name, index):
		"""Rename specified path"""
		try:
			# try renaming specified path
			self._source.rename_path(old_name, new_name, relative_to=self._source_path)

		except StandardError as error:
			# problem renaming path, ask user what to do
			response = self._get_rename_error_input(error)

			# handle user response
			if response == gtk.RESPONSE_YES:
				self._remove_path(old_name, new_name, index)  # retry renaming path

			else:
				# user didn't want to retry, remove path from list
				self._file_list.pop(index)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		# remove them
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
