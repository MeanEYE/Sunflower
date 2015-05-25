import os

from collections import namedtuple
from monitor import Monitor


FileInfo = namedtuple(
				'FileInfo',
				[
					'size',  # file size
					'mode',  # file access mode
					'user_id',  # user id
					'group_id',  # group id
					'time_modify',  # time of last modification
					'type',  # file type, constant from FileType class
				])


FileInfoExtended = namedtuple(
				'FileInfo',
				[
					'size',  # file size
					'mode',  # file access mode
					'i_mode',  # inode protection mode
					'user_id',  # user id
					'group_id',  # group id
					'time_access',  # time of last access
					'time_modify',  # time of last modification
					'time_change',  # time of file creation / on win create time
					'type',  # file type, constant from FileType class
					'device',  # device inode resides on
					'inode'  # inode number
				])


SystemSize = namedtuple(
				'SystemSize',
				[
					'block_size',  # block size in bytes
					'block_total',  # total block on specified system
					'block_available',  # available blocks
					'size_total',  # total system size in bytes
					'size_available'  # available size in bytes
				])


class FileType:
	INVALID = -1
	REGULAR = 0
	DIRECTORY = 1
	LINK = 2
	SOCKET = 3
	DEVICE_CHARACTER = 4
	DEVICE_BLOCK = 5


class Support:
	MONITOR = 0
	TRASH = 1
	SYMBOLIC_LINK = 2
	HARD_LINK = 3
	RESERVE_SIZE = 4
	SET_OWNER = 5
	SET_ACCESS = 6
	SET_TIMESTAMP = 7
	SYSTEM_SIZE = 8


class Mode:
	READ = 0
	WRITE = 1
	APPEND = 2
	READ_APPEND = 3


class TrashError(Exception): pass


class Provider:
	"""Abstract provider class used to manipulate items"""

	is_local = True  # if provider handles local files
	protocol = None # name of supported protocol
	archives = ()  # list of supported archive types

	def __init__(self, parent, path=None, selection=None):
		self._parent = parent

		self._path = path  # only used for archives and operations
		self._selection = selection
		self._handle = None

		# we need only existing items in selection list
		if selection is not None:
			self._selection = [item for item in selection if self.exists(item, path)]

	def _real_path(self, path, relative_to=None):
		"""Commonly used function to get real path"""
		return path if relative_to is None else os.path.join(relative_to, path)

	def set_archive_handle(self, handle):
		"""Set archive file handle."""
		self._handle = handle

	def release_archive_handle(self):
		"""Release archive handle when it's no longer needed."""
		if self._handle is not None:
			self._handle.close()

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		pass

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		pass

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		pass

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		pass

	def link(self, existing_path, destination_path, relative_to=None, symbolic=True):
		"""Create hard or symbolic link from existing path.

		Please note that relative_to parameter only applies to destination_path. It
		should not be applied to existing_path parameter.

		"""
		pass

	def unlink(self, path, relative_to=None):
		"""Unlink given path"""
		pass

	def remove_directory(self, path, recursive, relative_to=None):
		"""Remove directory and optionally its content"""
		pass

	def remove_file(self, path, relative_to=None):
		"""Remove file"""
		pass

	def create_file(self, path, mode=None, relative_to=None):
		"""Create empty file with specified mode set"""
		pass

	def create_directory(self, path, mode=None, relative_to=None):
		"""Create directory with specified mode set"""
		pass

	def get_file_handle(self, path, mode, relative_to=None):
		"""Open path in specified mode and return its handle"""
		pass

	def get_stat(self, path, relative_to=None, extended=False, follow=False):
		"""Return file statistics.

		This method returns FileInfo or FileInfoExtended objects for specified
		path. Unless otherwise specified by `follow` parameter this method is not
		suppose to follow symlinks.

		"""
		pass

	def get_directory_size(self, path, relative_to=None):
		"""Return directory size"""
		pass

	def get_selection(self, relative=False):
		"""Get list of selected items"""
		if self._selection is None:
			# get selection from parent
			result = self._parent._get_selection_list(relative=relative)

		else:
			# return predefined selection
			result = self._selection

		return result

	def get_path(self):
		"""Return parents path"""
		if self._path is None:
			# return parent path
			result = self._parent.path

		else:
			# return predefined path
			result = self._path

		return result

	def set_mode(self, path, mode, relative_to=None):
		"""Set access mode to specified path"""
		pass

	def set_owner(self, path, owner=-1, group=-1, relative_to=None):
		"""Set owner and/or group for specified path"""
		pass

	def set_timestamp(self, path, access=None, modify=None, change=None, relative_to=None):
		"""Set timestamp for specified path"""
		pass

	def remove_path(self, path, relative_to=None):
		"""Remove path"""
		if self.is_link(path, relative_to):  # handle links
			self.unlink(path, relative_to)

		elif self.is_dir(path, relative_to):  # handle directories
			self.remove_directory(path, relative_to)

		else:  # handle files
			self.remove_file(path, relative_to)

	def trash_path(self, path, relative_to=None):
		"""Instead of deleting, move path to the trash"""
		pass

	def move_path(self, source, destination, relative_to=None):
		"""Move path on same file system to a different parent node """
		pass

	def rename_path(self, source, destination, relative_to=None):
		"""Rename file/directory within parents path"""
		pass

	def list_dir(self, path, relative_to=None):
		"""Get directory list"""
		pass

	def get_parent(self):
		"""Return parent list"""
		return self._parent

	def get_root_path(self, path):
		"""Get root for specified path"""
		pass

	def get_parent_path(self, path):
		"""Get parent path for specified"""
		pass

	def get_system_size(self, path):
		"""Return system size information"""
		pass

	def get_monitor(self, path):
		"""Return monitor object to be used with specified list"""
		return Monitor(self, path)

	def get_support(self):
		"""Return supported options by provider"""
		return ()

	def get_protocol(self):
		"""Return true if scheme is supported by the provider"""
		return self.protocol

	def get_protocol_icon(self):
		"""Returns protocol icon name used in tab title bar"""
		return 'folder'
