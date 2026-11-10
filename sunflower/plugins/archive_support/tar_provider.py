from __future__ import absolute_import

import os
import time
import tarfile
import tempfile

from threading import RLock

from sunflower.plugin_base.provider import Provider, SystemSize, Mode
from sunflower.plugin_base.provider import FileInfo, FileInfoExtended, FileType


class TarWriter:
	"""File-like object used for adding new file to the archive.

	Every file in the archive is preceded by a header containing its size,
	which is not known until all the data is written. Data is collected in
	temporary storage and added to the archive when file is closed.

	"""

	MEMORY_LIMIT = 16 * 1024 * 1024

	def __init__(self, provider, name):
		self._provider = provider
		self._name = name
		self._data = tempfile.SpooledTemporaryFile(max_size=self.MEMORY_LIMIT)
		self._closed = False

	def write(self, data):
		"""Write data to the file"""
		self._data.write(data)

	def tell(self):
		"""Return number of bytes written so far"""
		return self._data.tell()

	def seek(self, offset, whence=0):
		"""Position can't be changed for files being added to archive"""
		return self._data.tell()

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
		"""Add collected data to the archive"""
		if not self._closed:
			self._closed = True

			try:
				self._provider._add_member(self._name, tarfile.REGTYPE, None, self._data)

			finally:
				self._data.close()


class TarProvider(Provider):
	"""Provider for handling of TAR archives, plain and compressed.

	Archives can be browsed and files copied out of them. Files and
	directories can be added to archives which are not compressed, as
	new items are simply written at the end. Compressed archives would
	have to be compressed again as a whole, so they are not modified.
	Same goes for removing, since format has no list of files items
	could be taken out of.

	"""

	is_local = False
	protocol = None
	archives = (
			'application/x-tar',
			'application/x-compressed-tar',
			'application/x-bzip-compressed-tar',
			'application/x-bzip2-compressed-tar',
			'application/x-xz-compressed-tar',
			'application/x-lzma-compressed-tar',
			'application/x-zstd-compressed-tar'
		)

	def __init__(self, parent, path, selection=None):
		Provider.__init__(self, parent, path, selection)

		self._cache = {}
		self._members = {}
		self._end_offset = 0
		self._tar_file = None
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

	def _get_file_type(self, member):
		"""Return file type for archive member."""
		if member.isdir():
			result = FileType.DIRECTORY

		elif member.issym():
			result = FileType.LINK

		elif member.isblk():
			result = FileType.DEVICE_BLOCK

		elif member.ischr():
			result = FileType.DEVICE_CHARACTER

		else:
			# hard links are shown as files they are pointing to
			result = FileType.REGULAR

		return result

	def _add_directory(self, name):
		"""Make sure directory and all of its parents are in the cache.

		Archives don't necessarily contain entries for directories files
		are located in.

		"""
		while name != '' and name not in self._cache:
			self._cache[name] = []

			key_name, directory_name = os.path.split(name)
			file_info = FileInfo(
					size = 0,
					mode = 0o755,
					user_id = 0,
					group_id = 0,
					time_modify = 0,
					type = FileType.DIRECTORY
				)

			if key_name not in self._cache:
				self._add_directory(key_name)

			self._cache[key_name].append((directory_name, file_info))
			name = key_name

	def _update_cache(self):
		"""Update archive cache.

		Unlike other formats this one has no list of files. Whole archive
		needs to be read, and for compressed ones decompressed, in order
		to find what's in it. This is why cache is populated on first use,
		which is listing done by the thread loading the list.

		"""
		with self._lock:
			if len(self._cache) > 0:
				return

			cache = self._cache
			cache[''] = []  # root directory

			for member in self._tar_file.getmembers():
				# names are relative to the root of the archive
				name = os.path.normpath(member.name).lstrip(os.path.sep)

				if name in ('', os.path.curdir) or name.startswith(os.path.pardir):
					continue

				self._cache_member(name, member)

			# reading stops at the marker ending the archive, which is
			# where new items are added
			self._end_offset = self._tar_file.offset

	def _cache_member(self, name, member):
		"""Store information about archive member in the cache."""
		cache = self._cache
		key_name, file_name = os.path.split(name)
		file_type = self._get_file_type(member)
		file_info = FileInfo(
				size = member.size if file_type is FileType.REGULAR else 0,
				mode = member.mode,
				user_id = member.uid,
				group_id = member.gid,
				time_modify = int(member.mtime),
				type = file_type
			)

		self._add_directory(key_name)

		# later entries replace earlier ones with the same name, which
		# includes information assumed for directories without an entry
		if name in self._members or name in cache:
			cache[key_name] = [item for item in cache[key_name] if item[0] != file_name]

		if file_type is FileType.DIRECTORY and name not in cache:
			cache[name] = []

		cache[key_name].append((file_name, file_info))
		self._members[name] = member

	def _get_file_info(self, real_path):
		"""Return cached file information for path or None."""
		result = None
		key_name, file_name = os.path.split(real_path)

		self._update_cache()

		for stored_file_name, file_info in self._cache.get(key_name, ()):
			if stored_file_name == file_name:
				result = file_info
				break

		return result

	def _resolve_link(self, real_path):
		"""Return path inside of the archive link is pointing to."""
		result = real_path
		visited = set()

		while result in self._members and self._members[result].issym() and result not in visited:
			visited.add(result)
			target = self._members[result].linkname
			result = os.path.normpath(os.path.join(os.path.dirname(result), target))

		return result

	def set_archive_handle(self, handle):
		"""Set archive file handle."""
		Provider.set_archive_handle(self, handle)
		self._open_archive()

	def _open_archive(self):
		"""Open archive for reading, forgetting everything known about its content."""
		if self._tar_file is not None:
			self._tar_file.close()

		self._cache.clear()
		self._members.clear()

		# compression is detected automatically
		self._handle.seek(0)
		self._tar_file = tarfile.open(fileobj=self._handle, mode='r:*')

	def _check_writable(self):
		"""Make sure items can be added to the archive."""
		# archive is read directly from the file only when it's not compressed
		if self._tar_file.fileobj is not self._handle:
			raise IOError(_('Compressed TAR archives can not be modified.'))

		writable = getattr(self._handle, 'writable', None)
		if writable is not None and not writable():
			raise IOError(_('Archive can not be modified.'))

	def _add_member(self, real_path, member_type, mode, data=None):
		"""Add file or directory to the end of the archive.

		Archive can contain more than one item with the same name, in which
		case the last one is used. This is how existing files are replaced.

		New item is written over the marker ending the archive, followed by
		a new marker. Position of that marker is known from reading the list
		of items, and added item is recorded in the cache, so archive doesn't
		have to be read again. List showing the archive is updated through
		monitor events.

		"""
		real_path = real_path.rstrip(os.path.sep)
		is_directory = member_type == tarfile.DIRTYPE

		if real_path == '':
			raise IOError(_('Invalid name.'))

		with self._lock:
			self._check_writable()
			self._update_cache()

			if real_path in self._cache:
				raise IOError(_('Directory with the same name already exists.'))

			if is_directory and real_path in self._members:
				raise IOError(_('File with the same name already exists.'))

			member = tarfile.TarInfo(real_path)
			member.type = member_type
			member.mode = mode or (0o755 if is_directory else 0o644)
			member.mtime = int(time.time())
			member.uid = os.getuid()
			member.gid = os.getgid()

			if data is not None:
				member.size = data.tell()
				data.seek(0)

			archive = self._tar_file
			header = member.tobuf(archive.format, archive.encoding, archive.errors)

			# write header and data, which is padded to full block
			self._handle.seek(self._end_offset)
			self._handle.write(header)

			remaining = member.size
			while remaining > 0:
				block = data.read(min(remaining, 1024 * 1024))

				if not block:
					raise IOError(_('Unexpected end of data.'))

				self._handle.write(block)
				remaining -= len(block)

			padding = -member.size % tarfile.BLOCKSIZE
			self._handle.write(tarfile.NUL * padding)

			# location of data is needed for reading the file later
			member.offset = self._end_offset
			member.offset_data = self._end_offset + len(header)
			self._end_offset = member.offset_data + member.size + padding

			# write marker ending the archive, size of which is rounded to full record
			marker = tarfile.NUL * (tarfile.BLOCKSIZE * 2)
			marker += tarfile.NUL * (-(self._end_offset + len(marker)) % tarfile.RECORDSIZE)
			self._handle.write(marker)
			self._handle.flush()

			self._cache_member(real_path, member)

	def release_archive_handle(self):
		"""Release archive handle when it's no longer needed."""
		with self._lock:
			if self._tar_file is not None:
				self._tar_file.close()

		Provider.release_archive_handle(self)

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		file_info = self._get_file_info(self.real_path(path, relative_to))
		return file_info is not None and file_info.type is not FileType.DIRECTORY

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		real_path = self.real_path(path, relative_to)

		self._update_cache()

		return real_path in self._cache

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		file_info = self._get_file_info(self.real_path(path, relative_to))
		return file_info is not None and file_info.type is FileType.LINK

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		real_path = self.real_path(path, relative_to)

		# archive itself can be entered without reading through all of it
		if real_path == '':
			return True

		return self._get_file_info(real_path) is not None

	def readlink(self, path, relative_to=None):
		"""Return a string representing the path to which the symbolic link points."""
		real_path = self.real_path(path, relative_to)

		self._update_cache()

		if real_path not in self._members:
			raise IOError(_('No such file in archive.'))

		return self._members[real_path].linkname

	def _refuse_change(self, *args, **kwargs):
		"""Report that content of the archive can't be changed."""
		raise IOError(_('Items in TAR archives can not be removed, renamed or linked.'))

	remove_directory = _refuse_change
	remove_file = _refuse_change
	link = _refuse_change
	unlink = _refuse_change
	move_path = _refuse_change
	rename_path = _refuse_change

	def create_file(self, path, mode=None, relative_to=None):
		"""Create empty file with specified mode set"""
		self._add_member(self.real_path(path, relative_to), tarfile.REGTYPE, mode)

	def create_directory(self, path, mode=None, relative_to=None):
		"""Create directory with specified mode set"""
		self._add_member(self.real_path(path, relative_to), tarfile.DIRTYPE, mode)

	def get_file_handle(self, path, mode, relative_to=None):
		"""Open path in specified mode and return its handle"""
		real_path = self.real_path(path, relative_to)

		if mode is Mode.WRITE:
			# fail before any data is written instead of after all of it
			with self._lock:
				self._check_writable()

			return TarWriter(self, real_path)

		# handle used for opening archives located inside of this one
		# is requested for reading and writing, but will only allow reading
		if mode not in (Mode.READ, Mode.READ_APPEND):
			self._refuse_change()


		self._update_cache()

		# files are read through links pointing to them
		real_path = self._resolve_link(real_path)

		if real_path not in self._members:
			raise IOError(_('No such file in archive.'))

		with self._lock:
			result = self._tar_file.extractfile(self._members[real_path])

		if result is None:
			raise IOError(_('Item is not a file.'))

		return result

	def get_stat(self, path, relative_to=None, extended=False, follow=False):
		"""Return file statistics.

		This method returns FileInfo or FileInfoExtended objects for specified
		path. Unless otherwise specified by `follow` parameter this method is not
		suppose to follow symlinks.

		"""
		real_path = self.real_path(path, relative_to)

		self._update_cache()

		if follow:
			real_path = self._resolve_link(real_path)

		result = self._get_file_info(real_path)

		# links pointing outside of the archive, or to nothing, are invalid
		if result is None or (follow and result.type is FileType.LINK):
			result = FileInfo(
					size = 0,
					mode = 0,
					user_id = 0,
					group_id = 0,
					time_modify = 0,
					type = FileType.INVALID
				)

		if extended:
			result = FileInfoExtended(
						size = result.size,
						mode = result.mode,
						i_mode = 0,
						user_id = result.user_id,
						group_id = result.group_id,
						time_access = result.time_modify,  # archives don't store access time
						time_modify = result.time_modify,
						time_change = 0,
						time_access_ns = int(result.time_modify) * 10**9,
						time_modify_ns = int(result.time_modify) * 10**9,
						time_change_ns = 0,
						type = result.type,
						device = 0,
						inode = 0
					)

		return result

	def get_directory_size(self, path, relative_to=None):
		"""Return directory size"""
		pass

	def set_mode(self, path, mode, relative_to=None):
		"""Set access mode to specified path"""
		pass

	def set_owner(self, path, owner=-1, group=-1, relative_to=None):
		"""Set owner and/or group for specified path"""
		pass

	def set_timestamp(self, path, access=None, modify=None, change=None, relative_to=None):
		"""Set timestamp for specified path"""
		pass

	def list_dir(self, path, relative_to=None):
		"""Get directory list."""
		real_path = self.real_path(path, relative_to)

		self._update_cache()

		if real_path not in self._cache:
			raise IOError(_('No such directory in archive.'))

		return [info[0] for info in self._cache[real_path]]

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
		return ()

	def get_protocol_icon(self):
		"""Returns protocol icon name used in tab title bar"""
		return self._protocol_icon
