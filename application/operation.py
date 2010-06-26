#!/usr/bin/env python

import os
import stat
import gobject
import fnmatch

from threading import Thread
from gui.operation_dialog import CopyDialog, MoveDialog, DeleteDialog

OPTION_FILE_TYPE   = 0
OPTION_DESTINATION = 1
OPTION_SET_OWNER   = 2
OPTION_SET_MODE    = 3

COPY_BUFFER = 100 * 1024

class Operation(Thread):
	"""Parent class for all operation threads"""

	def __init__(self, application, source, destination):
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
			self._dialog.destroy()

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
		
	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = CopyDialog(self._application, self)

	def _update_status(self, status):
		"""Set status and reset progress bars"""
		self._dialog.set_status(status)
		self._dialog.set_current_file("")
		self._dialog.set_current_file_fraction(0)
		
	def _get_lists(self, dir_list, file_list):
		"""Find all files for copying"""
		gobject.idle_add(self._update_status, "Searching for files...")

		for item in self._source.get_selection():
			if self._source._is_dir(item):
				gobject.idle_add(self._dialog.set_current_file, os.path.basename(item))
				self._scan_directory(dir_list, file_list, item)
				
			elif fnmatch.fnmatch(os.path.basename(item), self._options[OPTION_FILE_TYPE]):
				stat = self._source.get_stat(item)
				gobject.idle_add(self._dialog.increment_total_size, stat.st_size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				file_list.append(item)
				
			if not self._can_continue: break  # abort operation if requested
	
	def _scan_directory(self, dir_list, file_list, dir):
		"""Recursively scan directory and populate list"""
		dir_list.append(dir)

		for item in self._source.list_dir(dir):
			full_name = os.path.join(dir, item)

			if self._source._is_dir(full_name):
				gobject.idle_add(self._dialog.set_current_file, item)
				self._scan_directory(dir_list, file_list, full_name)
				
			elif fnmatch.fnmatch(item, self._options[OPTION_FILE_TYPE]):
				stat = self._source.get_stat(full_name)
				gobject.idle_add(self._dialog.increment_total_size, stat.st_size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				file_list.append(full_name)
				
			if not self._can_continue: break  # abort operation if requested

	def _copy_file(self, source, destination):
		"""Copy file content"""
		# TODO: Handle errors!
		sh = self._source.get_file_handle(source, 'rb')
		dh = self._destination.get_file_handle(destination, "wb")
		
		destination_size = 0L
		file_stat = self._source.get_stat(source)
		
		while True:
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
			
			if not self._can_continue: break
		
	def _create_directories(self, source, destination, list):
		"""Create all directories in list"""
		gobject.idle_add(self._update_status, "Creating directories...")
		for number, dir in enumerate(list, 0):
			display_name = dir[len(source)+1:]
			gobject.idle_add(self._dialog.set_current_file, display_name)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(number)/len(list))

			file_stat = self._source.get_stat(dir)
			mode = stat.S_IMODE(file_stat.st_mode) if self._options[OPTION_SET_MODE] else 0755
			
			# TODO: Handle errors!
			self._destination.create_directory(os.path.join(destination, display_name), mode)
			
			# try to set owner
			if self._options[OPTION_SET_OWNER]:
				pass  # TODO: Implement set owner

			# if we are not allowed to continue, exit
			if not self._can_continue: break

	def _copy_file_list(self, source, destination, list):
		"""Copy list of files to destination path"""
		gobject.idle_add(self._update_status, "Copying files...")
		for file in list:
			display_name = file[len(source)+1:]  # just take the ending part of the path
			gobject.idle_add(self._dialog.set_current_file, os.path.basename(file))

			self._copy_file(file, os.path.join(destination, display_name))				
			gobject.idle_add(self._dialog.increment_current_count, 1)

			# if we are not allowed to continue, exit
			if not self._can_continue: break
		
	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		path_source = self._source.get_path()
		path_destination = self._options[OPTION_DESTINATION]
		dir_list = []
		file_list = []
		
		# set dialog info
		self._dialog.set_source(path_source)
		self._dialog.set_destination(path_destination)
		
		self._get_lists(dir_list, file_list)
		
		# create directories
		if self._can_continue:
			self._create_directories(path_source, path_destination, dir_list)
		
		# copy files
		if self._can_continue:
			self._copy_file_list(path_source, path_destination, file_list)

		gobject.idle_add(self._destroy_ui)


class MoveOperation(CopyOperation): 
	"""Operation thread used for moving files"""

	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = MoveDialog(self._application, self)
		
	def _copy_file_list(self, source, destination, list):
		"""Delete files after copying"""
		CopyOperation._copy_file_list(self, source, destination, list)
		
		if self._can_continue:
			self._delete_file_list()
		
	def _delete_file_list(self):
		"""Remove files from source list"""
		self._update_status("Deleting source files...")
		
		list = self._source.get_selection()
		for number, item in enumerate(list, 0):
			gobject.idle_add(self._dialog.set_current_file, os.path.basename(item))
			self._source.remove_path(item)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(number) / len(list))
			
			# if we are not allowed to continue, exit
			if not self._can_continue: break
			

class DeleteOperation(Operation):
	"""Operation thread used for deleting files"""

	def __init__(self, application, source, destination):
		Operation.__init__(self, application, source, destination)
		self._dialog = DeleteDialog(application, self)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		list = self._source.get_selection()

		for index, item in enumerate(list, 1):
			gobject.idle_add(self._dialog.set_current_file, os.path.basename(item))
			self._source.remove_path(item)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(index) / len(list))

			# if we are not allowed to continue, exit
			if not self._can_continue: break

		gobject.idle_add(self._destroy_ui)
