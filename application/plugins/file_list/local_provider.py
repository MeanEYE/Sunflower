import os
import gio
import stat
import shutil

from local_monitor import LocalMonitor
from plugin_base.provider import Provider, FileType, FileInfo, FileInfoExtended, SystemSize
from plugin_base.provider import Support, TrashError


class LocalProvider(Provider):
	"""Content provider for local files"""
	is_local = True
	protocol = 'file'

	def _real_path(self, path, relative_to=None):
		"""Get real path based on specified parameters."""
		if path.startswith('file://'):
			path = path[7:]

		if relative_to is not None and relative_to.startswith('file://'):
			relative_to = relative_to[7:]

		return Provider._real_path(self, path, relative_to)

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		real_path = self._real_path(path, relative_to)
		return os.path.isfile(real_path)

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		real_path = self._real_path(path, relative_to)
		return os.path.isdir(real_path)

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		real_path = self._real_path(path, relative_to)
		return os.path.islink(real_path)

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		real_path = self._real_path(path, relative_to)
		return os.path.exists(real_path)

	def link(self, existing_path, destination_path, relative_to=None, symbolic=True):
		"""Create hard or symbolic link from existing path"""
		real_path = self._real_path(destination_path, relative_to)

		if symbolic:
			# create a symbolic link on destination path from existing path
			os.symlink(existing_path, real_path)

		else:
			# create a hard link on destination path from existing path
			os.link(existing_path, real_path)

	def unlink(self, path, relative_to=None):
		"""Unlink given path"""
		real_path = self._real_path(path, relative_to)
		os.remove(real_path)

	def remove_directory(self, path, relative_to=None):
		"""Remove directory and optionally its contents"""
		real_path = self._real_path(path, relative_to)
		shutil.rmtree(real_path)

	def remove_file(self, path, relative_to=None):
		"""Remove file"""
		real_path = self._real_path(path, relative_to)
		os.remove(real_path)

	def trash_path(self, path, relative_to=None):
		"""Move path to the trash"""
		real_path = self._real_path(path, relative_to)
		tmp = gio.File(real_path)

		try:
			tmp.trash()

		except Exception as error:
			raise TrashError(error)

	def create_file(self, path, mode=0644, relative_to=None):
		"""Create empty file with specified mode set"""
		real_path = self._real_path(path, relative_to)
		open(real_path, 'w').close()
		self.set_mode(real_path, mode)

	def create_directory(self, path, mode=0755, relative_to=None):
		"""Create directory with specified mode set"""
		real_path = self._real_path(path, relative_to)
		os.makedirs(real_path, mode)

	def get_file_handle(self, path, mode, relative_to=None):
		"""Open path in specified mode and return its handle"""
		real_path = self._real_path(path, relative_to)
		real_mode = ('rb', 'wb', 'ab', 'rab')[mode]
		return open(real_path, real_mode)

	def get_stat(self, path, relative_to=None, extended=False, follow=False):
		"""Return file statistics"""
		real_path = self._real_path(path, relative_to)

		try:
			# try getting file stats
			file_stat = os.lstat(real_path) if not follow else os.stat(real_path)

		except:
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

		# get file type
		if stat.S_ISLNK(file_stat.st_mode):
			item_type = FileType.LINK

		elif stat.S_ISDIR(file_stat.st_mode):
			item_type = FileType.DIRECTORY

		elif stat.S_ISBLK(file_stat.st_mode):
			item_type = FileType.DEVICE_BLOCK

		elif stat.S_ISCHR(file_stat.st_mode):
			item_type = FileType.DEVICE_CHARACTER

		elif stat.S_ISSOCK(file_stat.st_mode):
			item_type = FileType.SOCKET

		else:
			item_type = FileType.REGULAR

		if not extended:
			# create normal file information
			result = FileInfo(
						size = file_stat.st_size,
						mode = stat.S_IMODE(file_stat.st_mode),
						user_id = file_stat.st_uid,
						group_id = file_stat.st_gid,
						time_modify = file_stat.st_mtime,
						type = item_type,
					)
		else:
			# create extended file information
			result = FileInfoExtended(
						size = file_stat.st_size,
						mode = stat.S_IMODE(file_stat.st_mode),
						i_mode = file_stat.st_mode,
						user_id = file_stat.st_uid,
						group_id = file_stat.st_gid,
						time_access = file_stat.st_atime,
						time_modify = file_stat.st_mtime,
						time_change = file_stat.st_ctime,
						type = item_type,
						device = file_stat.st_dev,
						inode = file_stat.st_ino
					)

		return result

	def set_mode(self, path, mode, relative_to=None):
		"""Set access mode to specified path"""
		real_path = self._real_path(path, relative_to)
		os.chmod(real_path, mode)

	def set_owner(self, path, owner=-1, group=-1, relative_to=None):
		"""Set owner and/or group for specified path"""
		real_path = self._real_path(path, relative_to)
		os.chown(real_path, owner, group)

	def set_timestamp(self, path, access=None, modify=None, change=None, relative_to=None):
		"""Set timestamps for specified path

		On Linux/Unix operating system we can't set metadata change timestamp
		so we just ignore this part until other platforms are supported.

		"""
		real_path = self._real_path(path, relative_to)
		os.utime(real_path, (access, modify))

	def move_path(self, source, destination, relative_to=None):
		"""Move path on same file system to a different parent node """
		return self.rename_path(source,destination,relative_to)

	def rename_path(self, source, destination, relative_to=None):
		"""Rename file/directory within parents path"""
		if relative_to is None:
			real_source = source
			real_destination = destination
		else:
			real_source = os.path.join(relative_to, source)
			real_destination = os.path.join(relative_to, destination)

		os.rename(
				os.path.join(self._parent.path, real_source),
				os.path.join(self._parent.path, real_destination)
			)

	def list_dir(self, path, relative_to=None):
		"""Get directory list"""
		real_path = self._real_path(path, relative_to)
		return os.listdir(real_path)

	def get_root_path(self, path):
		"""Get root for specified path"""
		return 'file:///' if path.startswith('file://') else os.path.sep

	def get_parent_path(self, path):
		"""Get parent path for specified"""
		result = os.path.dirname(path)
		return result if result != path else None

	def get_system_size(self, path):
		"""Return system size information"""
		try:
			stat = os.statvfs(path)

			space_free = stat.f_bsize * stat.f_bavail
			space_total = stat.f_bsize * stat.f_blocks

			result = SystemSize(
						block_size = stat.f_bsize,
						block_total = stat.f_blocks,
						block_available = stat.f_bavail,
						size_total = space_total,
						size_available = space_free
					)

		except:
			result = SystemSize(
						block_size = 0,
						block_total = 0,
						block_available = 0,
						size_total = 0,
						size_available = 0
					)

		return result

	def get_monitor(self, path):
		"""Get file system monitor for specified path"""
		return LocalMonitor(self, path)

	def get_support(self):
		"""Return supported options by provider"""
		return (
			Support.MONITOR,
			Support.TRASH,
			Support.SYMBOLIC_LINK,
			Support.HARD_LINK,
			Support.RESERVE_SIZE,
			Support.SET_OWNER,
			Support.SET_ACCESS,
			Support.SET_TIMESTAMP,
			Support.SYSTEM_SIZE
		)
