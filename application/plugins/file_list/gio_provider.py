import os
import gio

from plugin_base.provider import Provider, FileType, FileInfo, FileInfoExtended, SystemSize


class GioProvider(Provider):
	"""Generic provider for file systems supported by GIO"""
	is_local = False
	protocol = ''

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		info = gio.File(real_path).query_info('standard::type')

		return info.get_file_type() == gio.FILE_TYPE_REGULAR

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		info = gio.File(real_path).query_info('standard::type')

		return info.get_file_type() == gio.FILE_TYPE_DIRECTORY

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		info = gio.File(real_path).query_info('standard::type')

		return info.get_file_type() == gio.FILE_TYPE_SYMBOLIC_LINK

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		return gio.File(real_path).query_exists()

	def unlink(self, path, relative_to=None):
		"""Unlink given path"""
		# TODO: Implement
		pass

	def remove_directory(self, path, recursive, relative_to=None):
		"""Remove directory and optionally its contents"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		if recursive:
			# TODO: Implement
			pass
		else:
			gio.File(real_path).delete()

	def remove_file(self, path, relative_to=None):
		"""Remove file"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		gio.File(real_path).delete()

	def get_stat(self, path, relative_to=None, extended=False):
		"""Return file statistics"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)

		try:
			# try getting file stats
			file_stat = gio.File(real_path).query_info(
											'standard::size,unix::mode,unix::uid,unix::gid'
											'time::access,time::modified,time::changed,'
											'standard::type,unix:device,unix::inode'
										)

		except:
			# handle invalid files/links
			if not extended: 
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
		file_type = file_stat.get_file_type()
		item_type = FileType.REGULAR

		if file_type == gio.FILE_TYPE_DIRECTORY:
			item_type = FileType.DIRECTORY

		elif file_type == gio.FILE_TYPE_SYMBOLIC_LINK:
			item_type = FileType.LINK

		elif file_type == gio.FILE_TYPE_SPECIAL:
			item_type = FileType.DEVICE_BLOCK

		if not extended:
			# create normal file information
			result = FileInfo(
						size = file_stat.get_size(),
						mode = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_MODE),
						user_id = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_UID),
						group_id = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_GID),
						time_modify = file_stat.get_attribute_uint64(gio.FILE_ATTRIBUTE_TIME_MODIFIED),
						type = item_type,
					)
		else:
			# create extended file information
			result = FileInfoExtended(
						size = file_stat.get_size(),
						mode = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_MODE),
						i_mode = 0,
						user_id = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_UID),
						group_id = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_GID),
						time_access = file_stat.get_attribute_uint64(gio.FILE_ATTRIBUTE_TIME_ACCESS),
						time_modify = file_stat.get_attribute_uint64(gio.FILE_ATTRIBUTE_TIME_MODIFIED),
						time_change = file_stat.get_attribute_uint64(gio.FILE_ATTRIBUTE_TIME_CHANGED),
						type = item_type,
						device = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_DEVICE),
						inode = file_stat.get_attribute_uint32(gio.FILE_ATTRIBUTE_UNIX_INODE)
					)

		return result

	def list_dir(self, path, relative_to=None):
		"""Get directory list"""
		real_path = path if relative_to is None else os.path.join(relative_to, path)
		directory = gio.File(real_path)
		result = []

		try:
			information = directory.enumerate_children('standard::name')
			for file_information in information:
				result.append(file_information.get_name())

		except gio.Error:
			pass

		return result

	def get_system_size(self, path):
		"""Return system size information"""
		try:
			stat = gio.File(path).query_filesystem_info('filesystem::size,filesystem::free')

			space_free = stat.get_attribute_uint64(gio.FILE_ATTRIBUTE_FILESYSTEM_FREE)
			space_total = stat.get_attribute_uint64(gio.FILE_ATTRIBUTE_FILESYSTEM_SIZE)

			result = SystemSize(
						block_size = 0,
						block_total = 0,
						block_available = 0,
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
		return None


class SmbProvider(GioProvider):
	is_local = False
	protocol = 'smb'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'samba'


class FtpProvider(GioProvider):
	is_local = False
	protocol = 'ftp'


class NetworkProvider(GioProvider):
	is_local = False
	protocol = 'network'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'network-workgroup'

