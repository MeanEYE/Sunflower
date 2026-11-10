from __future__ import absolute_import

import os
import io
import time
import zipfile
import datetime

from threading import RLock

from sunflower.plugin_base.provider import Provider, Support, SystemSize, Mode
from sunflower.plugin_base.provider import FileInfo, FileInfoExtended, FileType


class ZipWriter:
	"""File-like object used for adding new file to the archive.

	Data can only be written sequentially, which is all operations
	need. Archive is finalized once file is closed.

	"""

	def __init__(self, provider, stream):
		self._provider = provider
		self._stream = stream
		self._position = 0
		self._closed = False

	def write(self, data):
		"""Write data to the file"""
		self._stream.write(data)
		self._position += len(data)

	def tell(self):
		"""Return number of bytes written so far"""
		return self._position

	def seek(self, offset, whence=0):
		"""Position can't be changed for files being added to archive"""
		return self._position

	def truncate(self, size=None):
		"""File size is defined by the amount of data written"""
		pass

	def flush(self):
		"""Data is written to archive on close"""
		pass

	def closed(self):
		"""If file is closed"""
		return self._closed

	def close(self):
		"""Finish adding file to the archive"""
		if not self._closed:
			self._closed = True
			self._stream.close()
			self._provider._commit()


class ZipProvider(Provider):
	"""Provider for handling of ZIP archives."""

	is_local = False
	protocol = None
	# formats which are ZIP archives under different name, documents and
	# books are left out on purpose as those are expected to be opened
	archives = (
			'application/zip',
			'application/java-archive',
			'application/x-java-archive',
			'application/x-jar',
			'application/jar',
			'application/war',
			'application/vnd.android.package-archive',
			'application/x-xpinstall'
		)

	def __init__(self, parent, path, selection=None):
		Provider.__init__(self, parent, path, selection)

		self._cache = {}
		self._file_list = []
		self._zip_file = None
		self._writer = None
		self._lock = RLock()

		# get icon name
		icon_manager = self._parent._parent.icon_manager
		self._protocol_icon = icon_manager.get_icon_for_file(path)

	def real_path(self, path, relative_to=None):
		"""Commonly used function to get real path"""
		result = path if relative_to is None else os.path.join(relative_to, path)

		if result.startswith(self._path):
			result = result[len(self._path) + 1:]

		return result

	def _update_cache(self):
		"""Update archive cache."""
		self._cache.clear()
		del self._file_list[:]
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

			# prepare file timestamp
			try:
				file_timestamp = time.mktime(datetime.datetime(*info.date_time).timetuple())
			except ValueError:
				# set fallback timestamp for files with invalid date_time value
				file_timestamp = 0

			# get permissions mode
			mode = int(info.external_attr >> 16)
			# set default permissions if file had none
			if mode == 0:
				mode = 0o644 if file_type == FileType.REGULAR else 0o775

			# prepare file info
			file_info = FileInfo(
					size = info.file_size,
					mode = mode,
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
		with self._lock:
			# file left open by interrupted operation would leave archive unfinished
			if self._writer is not None:
				self._writer.close()

			self._zip_file.close()

		Provider.release_archive_handle(self)

	def _commit(self):
		"""Finalize changes made to the archive.

		List of files is located at the end of the archive, and is only
		written when archive gets closed. Until then data on disk is not
		a valid archive, so this is done after every change.

		"""
		with self._lock:
			self._writer = None
			self._zip_file.close()
			self._zip_file = zipfile.ZipFile(self._handle, 'a')
			self._update_cache()

	def _move_data(self, source, destination, size):
		"""Move block of data towards the beginning of the archive file."""
		moved = 0

		while moved < size:
			self._handle.seek(source + moved)
			data = self._handle.read(min(size - moved, 1024 * 1024))

			if not data:
				raise IOError(_('Unexpected end of archive.'))

			self._handle.seek(destination + moved)
			self._handle.write(data)
			moved += len(data)

	def _remove_entries(self, names):
		"""Remove entries with specified names from the archive.

		Archive format has no notion of removing files. Entries are taken out
		of the list of files stored at the end of the archive and data which
		follows them is moved over the space they used. Nothing is compressed
		again, but `zipfile` doesn't offer this so its entry list is modified
		directly.

		"""
		archive = self._zip_file
		entries = sorted(archive.filelist, key=lambda entry: entry.header_offset)
		removed_size = 0

		for index, entry in enumerate(entries):
			# data of each entry spans to the beginning of the next one
			if index + 1 < len(entries):
				entry_end = entries[index + 1].header_offset
			else:
				entry_end = archive.start_dir
			entry_size = entry_end - entry.header_offset

			if entry.filename in names:
				archive.filelist.remove(entry)
				if archive.NameToInfo.get(entry.filename) is entry:
					del archive.NameToInfo[entry.filename]
				removed_size += entry_size

			elif removed_size > 0:
				self._move_data(entry.header_offset, entry.header_offset - removed_size, entry_size)
				entry.header_offset -= removed_size

		# list of files is written from this position when archive is closed
		archive.start_dir -= removed_size
		archive._didModify = True

		self._commit()

	def _prepare_entry(self, real_path, mode, is_directory):
		"""Create archive entry for new file or directory."""
		self._check_writable()

		real_path = real_path.rstrip(os.path.sep)
		if real_path == '':
			raise IOError(_('Invalid name.'))

		# file added before the one being added now was never closed
		if self._writer is not None:
			self._writer.close()

		if len(self._cache) == 0:
			self._update_cache()

		if real_path in self._cache:
			raise IOError(_('Directory with the same name already exists.'))

		# archive format allows multiple entries with the same name
		# so existing file needs to be removed before adding new one
		if real_path in self._file_list:
			if is_directory:
				raise IOError(_('File with the same name already exists.'))

			self._remove_entries((real_path,))

		if is_directory:
			result = zipfile.ZipInfo(real_path + os.path.sep, time.localtime()[:6])
			result.external_attr = ((0o40000 | (mode or 0o755)) << 16) | 0x10  # directory flags

		else:
			result = zipfile.ZipInfo(real_path, time.localtime()[:6])
			result.external_attr = (0o100000 | (mode or 0o644)) << 16
			result.compress_type = zipfile.ZIP_DEFLATED

		return result

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		real_path = self.real_path(path, relative_to)
		return real_path in self._file_list and real_path not in self._cache

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		real_path = self.real_path(path, relative_to)
		return real_path in self._cache

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		return False

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		real_path = self.real_path(path, relative_to)
		return real_path in self._cache or real_path in self._file_list or real_path == ''

	def _check_writable(self):
		"""Make sure archive can be modified."""
		writable = getattr(self._handle, 'writable', None)
		if writable is not None and not writable():
			raise IOError(_('Archive can not be modified.'))

	def remove_directory(self, path, relative_to=None):
		"""Remove directory and its content"""
		real_path = self.real_path(path, relative_to).rstrip(os.path.sep)

		if real_path == '':
			raise IOError(_('Invalid name.'))

		with self._lock:
			self._check_writable()

			# directories don't necessarily have their own entry in the archive
			prefix = real_path + os.path.sep
			names = [name for name in self._zip_file.namelist() if name.startswith(prefix)]
			self._remove_entries(names)

	def remove_file(self, path, relative_to=None):
		"""Remove file"""
		real_path = self.real_path(path, relative_to)

		with self._lock:
			self._check_writable()

			if real_path not in self._zip_file.namelist():
				raise IOError(_('No such file in archive.'))

			self._remove_entries((real_path,))

	def create_file(self, path, mode=None, relative_to=None):
		"""Create empty file with specified mode set"""
		real_path = self.real_path(path, relative_to)

		with self._lock:
			self._zip_file.writestr(self._prepare_entry(real_path, mode, False), b'')
			self._commit()

	def create_directory(self, path, mode=None, relative_to=None):
		"""Create directory with specified mode set"""
		real_path = self.real_path(path, relative_to)

		with self._lock:
			self._zip_file.writestr(self._prepare_entry(real_path, mode, True), b'')
			self._commit()

	def get_file_handle(self, path, mode, relative_to=None):
		"""Open path in specified mode and return its handle"""
		result = None
		real_path = self.real_path(path, relative_to)

		if mode is Mode.READ:
			result = self._zip_file.open(real_path, 'r')

		elif mode is Mode.WRITE:
			with self._lock:
				entry = self._prepare_entry(real_path, None, False)
				self._writer = ZipWriter(self, self._zip_file.open(entry, 'w', force_zip64=True))
				result = self._writer

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
		real_path = self.real_path(path, relative_to)
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
							time_access_ns = 0,
							time_modify_ns = result.time_modify * 10**9,
							time_change_ns = 0,
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
							time_access_ns = 0,
							time_modify_ns = 0,
							time_change_ns = 0,
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
		real_path = self.real_path(path, relative_to)

		# update file cache
		if len(self._cache) == 0:
			self._update_cache()

		# get file list
		result = []
		if real_path in self._cache:
			result = [info[0] for info in self._cache[real_path]]

		return result

	def get_parent(self):
		"""Return parent list"""
		return self._parent

	def get_root_path(self, path):
		"""Get root for specified path"""
		return 'file:///' if path.startswith('file://') else os.path.sep

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

	def get_support(self, path=None):
		"""Return supported options by provider"""
		return (Support.SET_TIMESTAMP, Support.SET_ACCESS)

	def get_protocol_icon(self):
		"""Returns protocol icon name used in tab title bar"""
		return self._protocol_icon
