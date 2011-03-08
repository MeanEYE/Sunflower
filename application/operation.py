#!/usr/bin/env python

import os
import gtk
import stat
import gobject
import fnmatch

from threading import Thread, Event
from gui.input_dialog import OverwriteFileDialog, OverwriteDirectoryDialog
from gui.operation_dialog import CopyDialog, MoveDialog, DeleteDialog

# import constants
from gui.input_dialog import OPTION_APPLY_TO_ALL, OPTION_RENAME, OPTION_NEW_NAME

# constants
OPTION_FILE_TYPE   = 0
OPTION_DESTINATION = 1
OPTION_SET_OWNER   = 2
OPTION_SET_MODE    = 3

COPY_BUFFER = 100 * 1024


class Operation(Thread):
	"""Parent class for all operation threads"""

	def __init__(self, application, source, destination=None):
		Thread.__init__(self, target=self)

		self._can_continue = Event()
		self._abort = Event()
		self._application = application
		self._source = source
		self._destination = destination
		self._dialog = None

		# store initial paths
		self._source_path = self._source.get_path()
		if self._destination is not None:
			self._destination_path = self._destination.get_path()

		self._can_continue.set()

	def _destroy_ui(self):
		"""Destroy user interface"""
		if self._dialog is not None:
			self._dialog.destroy()

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

		self._create_dialog()
		self._options = options

		self._merge_all = None
		self._overwrite_all = None

		self._reserve_size = self._application.options.getboolean('main', 'reserve_size')

	def _create_dialog(self):
		"""Create progress dialog"""
		self._dialog = CopyDialog(self._application, self)

	def _update_status(self, status):
		"""Set status and reset progress bars"""
		self._dialog.set_status(status)
		self._dialog.set_current_file("")
		self._dialog.set_current_file_fraction(0)

	def _get_merge_input(self, path):
		"""Get merge confirmation"""
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

		gtk.gdk.threads_enter()  # prevent deadlocks
		result = dialog.get_response()
		gtk.gdk.threads_leave()

		merge = result[0] == gtk.RESPONSE_YES

		if result[1][OPTION_APPLY_TO_ALL]:
			self._merge_all = merge

		# in case user canceled operation
		if result[0] == gtk.RESPONSE_CANCEL:
			self.cancel()

		return merge  # return only response for current directory

	def _get_overwrite_input(self, path):
		"""Get overwrite confirmation"""
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

		gtk.gdk.threads_enter()  # prevent deadlocks
		result = dialog.get_response()
		gtk.gdk.threads_leave()

		overwrite = result[0] == gtk.RESPONSE_YES

		if result[1][OPTION_APPLY_TO_ALL]:
			self._overwrite_all = overwrite

		# in case user canceled operation
		if result[0] == gtk.RESPONSE_CANCEL:
			self.cancel()

		return overwrite, result[1]

	def _get_lists(self, dir_list, file_list):
		"""Find all files for copying"""
		gobject.idle_add(self._update_status, _('Searching for files...'))

		for item in self._source.get_selection(relative=True):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, item)
			gobject.idle_add(self._dialog.pulse)

			if self._source.is_dir(item, relative_to=self._source_path):
				can_procede = True
				can_create = True

				if self._destination.exists(item, relative_to=self._destination_path):
					can_create = False

					if self._merge_all is not None:
						can_procede = self._merge_all
					else:
						can_procede = self._get_merge_input(item)

				if can_procede:
					if can_create: dir_list.append(item)
					self._scan_directory(dir_list, file_list, item)

			elif fnmatch.fnmatch(item, self._options[OPTION_FILE_TYPE]):
				stat = self._source.get_stat(item, relative_to=self._source_path)
				gobject.idle_add(self._dialog.increment_total_size, stat.st_size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				file_list.append(item)

	def _scan_directory(self, dir_list, file_list, directory):
		"""Recursively scan directory and populate list"""
		for item in self._source.list_dir(directory, relative_to=self._source_path):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, item)
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
					if can_create: dir_list.append(full_name)
					self._scan_directory(dir_list, file_list, full_name)

			elif fnmatch.fnmatch(item, self._options[OPTION_FILE_TYPE]):
				stat = self._source.get_stat(full_name, relative_to=self._source_path)
				gobject.idle_add(self._dialog.increment_total_size, stat.st_size)
				gobject.idle_add(self._dialog.increment_total_count, 1)
				file_list.append(full_name)

	def _copy_file(self, file_):
		"""Copy file content"""
		can_procede = True
		dest_file = file_

		# check if destination file exists
		if self._destination.exists(file_, relative_to=self._destination_path):
			if self._overwrite_all is not None:
				can_procede = self._overwrite_all
			else:
				can_procede, options = self._get_overwrite_input(file_)

				# get new name if user specified
				if options[OPTION_RENAME]:
					dest_file = options[OPTION_NEW_NAME]

		# if user skipped this file return
		if not can_procede: return

		# TODO: Handle errors!
		sh = self._source.get_file_handle(file_, 'rb', relative_to=self._source_path)
		dh = self._destination.get_file_handle(dest_file, 'wb', relative_to=self._destination_path)

		destination_size = 0L
		file_stat = self._source.get_stat(file_, relative_to=self._source_path)

		# reserve file size
		try:
			if self._reserve_size:
				# reserve file size in advance, can be slow on memory cards and network
				dh.truncate(file_stat.st_size)

			else:
				# just truncate file to 0 size in case source file is smaller
				dh.truncate()
		except:
			# not all file systems support this option,
			# just ignore exception
			pass

		dh.seek(0)

		while True:
			if self._abort.is_set(): break
			self._can_continue.wait()

			buffer_ = sh.read(COPY_BUFFER)

			if (buffer_):
				dh.write(buffer_)

				destination_size += len(buffer_)
				gobject.idle_add(self._dialog.increment_current_size, len(buffer_))
				if file_stat.st_size > 0:  # ensure we don't end up with error on 0 size files
					gobject.idle_add(
									self._dialog.set_current_file_fraction,
									destination_size / float(file_stat.st_size)
									)
				else:
					gobject.idle_add(self._dialog.set_current_file_fraction, 1)

			else:
				sh.close()
				dh.close()

				# set mode if required
				if self._options[OPTION_SET_MODE]:
					self._destination.set_mode(
											dest_file,
											stat.S_IMODE(file_stat.st_mode),
											relative_to=self._destination_path
										)

				# set owner if required
				if self._options[OPTION_SET_OWNER]:
					self._destination.set_owner(
											dest_file,
											file_stat.st_uid,
											file_stat.st_gid,
											relative_to=self._destination_path
										)
				break

	def _create_directories(self, list):
		"""Create all directories in list"""
		gobject.idle_add(self._update_status, _('Creating directories...'))
		for number, dir in enumerate(list, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, dir)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(number)/len(list))

			file_stat = self._source.get_stat(dir, relative_to=self._source_path)
			mode = stat.S_IMODE(file_stat.st_mode) if self._options[OPTION_SET_MODE] else 0755

			# TODO: Handle errors!
			self._destination.create_directory(dir, mode, relative_to=self._destination_path)

			# set owner if requested
			if self._options[OPTION_SET_OWNER]:
				self._destination.set_owner(
										dir,
										file_stat.st_uid,
										file_stat.st_gid,
										relative_to=self._destination_path
									)

	def _copy_file_list(self, list):
		"""Copy list of files to destination path"""
		gobject.idle_add(self._update_status, _('Copying files...'))
		for file in list:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, file)

			self._copy_file(file)
			gobject.idle_add(self._dialog.increment_current_count, 1)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		dir_list = []
		file_list = []

		# set dialog info
		self._dialog.set_source(self._source_path)
		self._dialog.set_destination(self._destination_path)

		self._get_lists(dir_list, file_list)

		self._create_directories(dir_list)
		self._copy_file_list(file_list)

		gobject.idle_add(self._destroy_ui)


class MoveOperation(CopyOperation):
	"""Operation thread used for moving files"""

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
				if options[OPTION_RENAME]:
					dest_file = options[OPTION_NEW_NAME]

		# if user skipped this file return
		if not can_procede: return

		# move file
		self._source.rename_path(
							file_,
							os.path.join(self._destination_path, dest_file),
							relative_to=self._source_path
						)

	def _move_file_list(self, list_):
		"""Move files from the list"""
		gobject.idle_add(self._update_status, _('Moving files...'))
		for file_ in list_:
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, file_)

			self._move_file(file_)
			gobject.idle_add(self._dialog.increment_current_count, 1)

	def _copy_file_list(self, list):
		"""Delete files after copying"""
		CopyOperation._copy_file_list(self, list)

	def _delete_file_list(self, file_list, dir_list):
		"""Remove files from source list"""
		gobject.idle_add(self._update_status, _('Deleting source files...'))

		for number, item in enumerate(file_list, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, item)
			self._source.remove_path(item, relative_to=self._source_path)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(number) / len(file_list))

		self._delete_directories(dir_list)

	def _delete_directories(self, dir_list):
		"""Remove empty directories after moving files"""
		gobject.idle_add(self._update_status, _('Deleting source directories...'))

		dir_list.reverse()

		for number, directory in enumerate(dir_list, 0):
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			if self._source.exists(directory, relative_to=self._source_path):
				gobject.idle_add(self._dialog.set_current_file, directory)
				self._source.remove_path(directory, relative_to=self._source_path)
				gobject.idle_add(
							self._dialog.set_current_file_fraction,
							float(number) / len(dir_list)
							)

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

		dir_list = []
		file_list = []

		# set dialog info
		self._dialog.set_source(self._source_path)
		self._dialog.set_destination(self._destination_path)

		self._get_lists(dir_list, file_list)

		# create directories
		self._create_directories(dir_list)

		# copy/move files
		if self._check_devices():
			# both paths are on the same file system, move instead of copy
			self._move_file_list(file_list)
			self._delete_directories(dir_list)

		else:
			# paths are located on different file systems, copy and remove
			self._copy_file_list(file_list)
			self._delete_file_list(file_list, dir_list)

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
			if self._abort.is_set(): break  # abort operation if requested
			self._can_continue.wait()

			gobject.idle_add(self._dialog.set_current_file, item)
			self._source.remove_path(item, relative_to=self._source_path)
			gobject.idle_add(self._dialog.set_current_file_fraction, float(index) / len(list))

		gobject.idle_add(self._destroy_ui)
