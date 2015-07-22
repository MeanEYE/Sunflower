import os
import io
import time
import zipfile
import datetime

from plugin_base.provider import Provider, Support, SystemSize, Mode
from plugin_base.provider import FileInfo, FileInfoExtended, FileType


class ZipProvider(Provider):
	"""Provider for handling of ZIP archives."""

	is_local = False
	protocol = None
	archives = (
			'application/zip',
			'application/jar',
			'application/war'
		)

	def __init__(self, parent, path, selection=None):
		Provider.__init__(self, parent, path, selection)

		self._cache = {}
		self._file_list = []
		self._zip_file = None

		# get icon name
		icon_manager = self._parent._parent.icon_manager
		self._protocol_icon = icon_manager.get_icon_for_file(path)

	def _real_path(self, path, relative_to=None):
		"""Commonly used function to get real path"""
		result = path if relative_to is None else os.path.join(relative_to, path)

		if result.startswith(self._path):
			result = result[len(self._path) + 1:]

		return result

	def _update_cache(self):
		"""Update archive cache."""
		self._cache[''] = []  # root directory

		for info in self._zip_file.infolist():
			# detect file type
			if info.filename[-1] == os.path.sep:
				raw_name = info.filename[:-1]
				key_name, file_name = os.path.split(raw_name)
				file_type = FileType.DIRECTORY

				# create storage list for directory
				if raw_name not in self._cache:
					self._cache[raw_name] = []

			else:
				key_name, file_name = os.path.split(info.filename)
				file_type = FileType.REGULAR

			# prepate file timestamp
			file_timestamp = time.mktime(datetime.datetime(*info.date_time).timetuple())

			# prepare file info
			file_info = FileInfo(
					size = info.file_size,
					mode = int(info.external_attr >> 16),
					user_id = 0,
					group_id = 0,
					time_modify = file_timestamp,
					type = file_type
				)

			if key_name not in self._cache:
				self._cache[key_name] = []

			self._cache[key_name].append((file_name, file_info))
			self._file_list.append(info.filename)

	def set_archive_handle(self, handle):
		"""Set archive file handle."""
		Provider.set_archive_handle(self, handle)
		self._zip_file = zipfile.ZipFile(self._handle, 'a')

	def release_archive_handle(self):
		"""Release archive handle when it's no longer needed."""
		self._zip_file.close()
		Provider.release_archive_handle(self)

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		real_path = self._real_path(path, relative_to)
		return real_path in self._file_list and real_path not in self._cache

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		real_path = self._real_path(path, relative_to)
		return real_path in self._cache

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		return False

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		real_path = self._real_path(path, relative_to)
		return real_path in self._cache or real_path == ''

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
		result = None
		real_path = self._real_path(path, relative_to)

		if mode is Mode.READ:
			result = self._zip_file.open(real_path, 'r')

		elif mode is Mode.WRITE:
			pass

		else:
			pass

		return result

	def get_stat(self, path, relative_to=None, extended=False, follow=False):
		"""Return file statistics.

		This method returns FileInfo or FileInfoExtended objects for specified
		path. Unless otherwise specified by `follow` parameter this method is not
		suppose to follow symlinks.

		"""
		result = None
		real_path = self._real_path(path, relative_to)
		key_name, file_name = os.path.split(real_path)

		if key_name in self._cache:
			# find file information
			for stored_file_name, file_info in self._cache[key_name]:
				if stored_file_name == file_name:
					result = file_info
					break

			if extended and result is not None:
				result = FileInfoExtended(
							size = result.size,
							mode = result.mode,
							i_mode = 0,
							user_id = result.user_id,
							group_id = result.group_id,
							time_access = 0,
							time_modify = result.time_modify,
							time_change = 0,
							type = result.type,
							device = 0,
							inode = 0
						)

		else:
			# handle invalid files/links
			if extended:
				result = FileInfo(
							size = 0,
							mode = 0,
							user_id = 0,
							group_id = 0,
							time_modify = 0,
							type = FileType.INVALID,
						)

			else:
				result = FileInfoExtended(
							size = 0,
							mode = 0,
							i_mode = 0,
							user_id = 0,
							group_id = 0,
							time_access = 0,
							time_modify = 0,
							time_change = 0,
							type = FileType.INVALID,
							device = 0,
							inode = 0
						)

		return result

	def get_directory_size(self, path, relative_to=None):
		"""Return directory size"""
		pass

	def set_timestamp(self, path, access=None, modify=None, change=None, relative_to=None):
		"""Set timestamp for specified path"""
		pass

	def move_path(self, source, destination, relative_to=None):
		"""Move path on same file system to a different parent node """
		pass

	def rename_path(self, source, destination, relative_to=None):
		"""Rename file/directory within parents path"""
		pass

	def list_dir(self, path, relative_to=None):
		"""Get directory list."""
		real_path = self._real_path(path, relative_to)

		# update file cache
		if len(self._cache) == 0:
			self._update_cache()

		# get file list
		result = []
		if real_path in self._cache:
			result = map(lambda info: info[0], self._cache[real_path])

		return result

	def get_parent(self):
		"""Return parent list"""
		return self._parent

	def get_root_path(self, path):
		"""Get root for specified path"""
		return os.path.dirname(self._path)

	def get_parent_path(self, path):
		"""Get parent path for specified"""
		pass

	def get_system_size(self, path):
		"""Return system size information."""
		return SystemSize(
				block_size = 0,
				block_total = 0,
				block_available = 0,
				size_total = 0,
				size_available = 0
			)

	def get_support(self):
		"""Return supported options by provider"""
		return (Support.SET_TIMESTAMP, Support.SET_ACCESS)

	def get_protocol_icon(self):
		"""Returns protocol icon name used in tab title bar"""
		return self._protocol_icon
