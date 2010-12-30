#!/usr/bin/env python

import os
import gtk
import stat
import gobject
import fnmatch

from threading import Thread
from gui.input_dialog import OverwriteFileDialog, OverwriteDirectoryDialog, OPTION_APPLY_TO_ALL
from gui.operation_dialog import CopyDialog, MoveDialog, DeleteDialog

OPTION_FILE_TYPE   = 0
OPTION_DESTINATION = 1
OPTION_SET_OWNER   = 2
OPTION_SET_MODE    = 3

COPY_BUFFER = 100 * 1024

class Operation(Thread):
	"""Parent class for all operation threads"""

	def __init__(self, application, source, destination=None):
		Thread.__init__(self, target=self)

		self._paused = False
		self._can_continue = True
		self._application = application
		self._source = source
		self._destination = destination
		self._dialog = None

	def _destroy_ui(self):
		"""Destroy user interface"""
		if self._dialog is not None:
			self._dialog.hide()

	def pause(self, paused=True):
		"""Pause current operation"""
		self._paused = paused

	def cancel(self):
		"""Set an abort switch"""
		self._can_continue = False


class CopyOperation(Operation):
	"""Operation thread used for copying files"""

	def __init__(self, application, source, destination, options):
		Operation.__init__(self, application, source, destination)

		self._create_dialog()
		self._options = options
		
		self._merge_all = None
		self._overwrite_all = None
		
		self._merge_dialog = None
		self._overwrite_dialog = None
		
	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = CopyDialog(self._application, self)

	def _update_status(self, status):
		"""Set status and reset progress bars"""
		self._dialog.set_status(status)
		self._dialog.set_current_file("")
		self._dialog.set_current_file_fraction(0)
		
	def _get_merge_input(self, source_path, destination_path):
		"""Get merge confirmation
		
		Source path contains item in question while destination
		path contains parent directory.
		
		"""
		if self._merge_dialog is None:
			self._merge_dialog = OverwriteDirectoryDialog(self._application, self._dialog)
			
		title_element = os.path.basename(source_path)
		message_element = os.path.basename(destination_path) 
		
		self._merge_dialog.set_title_element(title_element)
		self._merge_dialog.set_message_element(message_element)
		self._merge_dialog.set_rename_value(title_element)
		self._merge_dialog.set_source(
									self._source, 
									source_path
								)
		self._merge_dialog.set_original(
									self._destination, 
									os.path.join(destination_path, title_element)
								)
		
		result = self._merge_dialog.get_response()
		
		merge = result[0] == gtk.RESPONSE_YES
		self._merge_all = merge and result[1][OPTION_APPLY_TO_ALL]
		
		# in case user canceled operation
		if result[0] == gtk.RESPONSE_CANCEL:
			self._can_continue = False
		
		return merge  # return only response for current directory
	
	def _get_overwrite_input(self, source_path, destination_path):
		"""Get overwrite confirmation
		
		Source path contains item in question while destination
		path contains parent directory.
		
		"""
		if self._overwrite_dialog is None:
			self._overwrite_dialog = OverwriteFileDialog(self._application, self._dialog)
			
		title_element = os.path.basename(source_path)
		message_element = os.path.basename(destination_path) 
		
		self._overwrite_dialog.set_title_element(title_element)
		self._overwrite_dialog.set_message_element(message_element)
		self._overwrite_dialog.set_rename_value(title_element)
		self._overwrite_dialog.set_source(
									self._source, 
									source_path
								)
		self._overwrite_dialog.set_original(
									self._destination, 
									os.path.join(destination_path, title_element)
								)
		
		result = self._overwrite_dialog.get_response()
		
		overwrite = result[0] == gtk.RESPONSE_YES
		self._overwrite_all = overwrite and result[1][OPTION_APPLY_TO_ALL]
		
		# in case user canceled operation
		if result[0] == gtk.RESPONSE_CANCEL:
			self._can_continue = False
		
		return overwrite  # return only response for current file
		
	def _get_lists(self, dir_list, file_list):
		"""Find all files for copying"""
		gobject.idle_add(self._update_status, "Searching for files...")

		for item in self._source.get_selection(relative=True):
			if not self._can_continue: break  # abort operation if requested

			if self._source.is_dir(item, relative=True):
				gobject.idle_add(self._dialog.set_current_file, os.path.basename(item))
				self._scan_directory(dir_list, file_list, item)
				
			elif fnmatch.fnmatch(item, self._options[OPTION_FILE_TYPE]):
				stat = self._source.get_stat(item, relative=True)
				gobject.idle_add(self._dialog.increment_total_size, stat.st_size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				file_list.append(item)
	
	def _scan_directory(self, dir_list, file_list, dir):
		"""Recursively scan directory and populate list"""
		dir_list.append(dir)

		for item in self._source.list_dir(dir, relative=True):
			if not self._can_continue: break  # abort operation if requested

			full_name = os.path.join(dir, item)
			
			if self._source.is_dir(full_name, relative=True):
				gobject.idle_add(self._dialog.set_current_file, item)
				self._scan_directory(dir_list, file_list, full_name)
				
			elif fnmatch.fnmatch(item, self._options[OPTION_FILE_TYPE]):
				stat = self._source.get_stat(full_name, relative=True)
				gobject.idle_add(self._dialog.increment_total_size, stat.st_size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				file_list.append(full_name)

	def _copy_file(self, file):
		"""Copy file content"""
		# TODO: Handle errors!
		sh = self._source.get_file_handle(file, 'rb', relative=True)
		dh = self._destination.get_file_handle(file, "wb", relative=True)
		
		destination_size = 0L
		file_stat = self._source.get_stat(file, relative=True)
		
		while True:
			if not self._can_continue: break

			buffer = sh.read(COPY_BUFFER)
			
			if (buffer):
				dh.write(buffer)
				
				destination_size += len(buffer)
				gobject.idle_add(self._dialog.increment_current_size, len(buffer))
				if file_stat.st_size > 0:  # ensure we don't end up with error on 0 size files
					gobject.idle_add(
									self._dialog.set_current_file_fraction, 
									destination_size / float(file_stat.st_size)
									)
			else:
				break;
		
	def _create_directories(self, list):
		"""Create all directories in list"""
		gobject.idle_add(self._update_status, "Creating directories...")
		for number, dir in enumerate(list, 0):
			# if we are not allowed to continue, exit
			if not self._can_continue: break

			gobject.idle_add(self._dialog.set_current_file, dir)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(number)/len(list))

			file_stat = self._source.get_stat(dir, relative=True)
			mode = stat.S_IMODE(file_stat.st_mode) if self._options[OPTION_SET_MODE] else 0755
			
			# TODO: Handle errors!
			self._destination.create_directory(dir, mode, relative=True)
			
			# try to set owner
			if self._options[OPTION_SET_OWNER]:
				pass  # TODO: Implement set owner

	def _copy_file_list(self, list):
		"""Copy list of files to destination path"""
		gobject.idle_add(self._update_status, "Copying files...")
		for file in list:
			# if we are not allowed to continue, exit
			if not self._can_continue: break

			gobject.idle_add(self._dialog.set_current_file, file)

			self._copy_file(file)				
			gobject.idle_add(self._dialog.increment_current_count, 1)
		
	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		path_source = self._source.get_path()
		path_destination = self._destination.get_path()
		dir_list = []
		file_list = []
		
		# set dialog info
		self._dialog.set_source(path_source)
		self._dialog.set_destination(path_destination)
		
		self._get_lists(dir_list, file_list)
		
		self._create_directories(dir_list)
		self._copy_file_list(file_list)

		gobject.idle_add(self._destroy_ui)


class MoveOperation(CopyOperation): 
	"""Operation thread used for moving files"""

	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = MoveDialog(self._application, self)
		
	def _move_file(self, source, destination):
		"""Move specified file using provider rename method"""
		self._source.rename_path(source, destination, relative=True)
	
	def _move_file_list(self, list):
		"""Move files from the list"""
		gobject.idle_add(self._update_status, "Moving files...")
		for file in list:
			# if we are not allowed to continue, exit
			if not self._can_continue: break

			gobject.idle_add(self._dialog.set_current_file, file)

			self._move_file(
						os.path.join(self._source.get_path(), file),
						os.path.join(self._destination.get_path(), file)
					)				
			gobject.idle_add(self._dialog.increment_current_count, 1)
		
	def _copy_file_list(self, list):
		"""Delete files after copying"""
		CopyOperation._copy_file_list(self, list)
		
		if self._can_continue:
			self._delete_file_list()
		
	def _delete_file_list(self):
		"""Remove files from source list"""
		self._update_status("Deleting source files...")
		
		list = self._source.get_selection(relative=True)
		for number, item in enumerate(list, 0):
			# if we are not allowed to continue, exit
			if not self._can_continue: break

			gobject.idle_add(self._dialog.set_current_file, item)
			self._source.remove_path(item, relative=True)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(number) / len(list))
	
	def _delete_directories(self):
		"""Remove empty directories after moving files"""
		list = self._source.get_selection(relative=True)
		
		for directory in list:
			if not self._can_continue: break
			if self._source.exists(directory, relative=True):
				self._source.remove_path(directory, relative=True)
			
	def _check_devices(self):
		"""Check if source and destination are on the same file system"""
		dev_source = self._source.get_stat(self._source.get_path()).st_dev
		dev_destination = self._destination.get_stat(self._destination.get_path()).st_dev
		
		return dev_source == dev_destination
			
	def run(self):
		"""Main thread method
		
		We override this method from CopyDialog in order to provide
		a bit smarter move operation.
		
		"""
		self._dialog.show_all()

		path_source = self._source.get_path()
		path_destination = self._destination.get_path()
		dir_list = []
		file_list = []
		
		# set dialog info
		self._dialog.set_source(path_source)
		self._dialog.set_destination(path_destination)
		
		self._get_lists(dir_list, file_list)
		
		# create directories
		self._create_directories(dir_list)
		
		# copy/move files
		if self._check_devices():
			# both paths are on the same file system, move instead of copy
			self._move_file_list(file_list)
			self._delete_directories()
			
		else:
			# paths are located on different file systems, copy and remove
			self._copy_file_list(file_list)
				
		gobject.idle_add(self._destroy_ui)			
		

class DeleteOperation(Operation):
	"""Operation thread used for deleting files"""

	def __init__(self, application, provider):
		Operation.__init__(self, application, provider)
		self._dialog = DeleteDialog(application, self)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		list = self._source.get_selection(relative=True)

		for index, item in enumerate(list, 1):
			gobject.idle_add(self._dialog.set_current_file, item)
			self._source.remove_path(item, relative=True)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(index) / len(list))

			# if we are not allowed to continue, exit
			if not self._can_continue: break

		gobject.idle_add(self._destroy_ui)
