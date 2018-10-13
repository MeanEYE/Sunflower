import os

from gi.repository import Gio, GLib
from urllib.parse import unquote
from .gio_wrapper import File
from .local_monitor import MonitorError, LocalMonitor
from sunflower.plugin_base.provider import Provider, FileType, FileInfo, FileInfoExtended, SystemSize
from sunflower.plugin_base.provider import Support


class GioProvider(Provider):
	"""Generic provider for file systems supported by GIO"""
	is_local = False
	protocol = ''

	def is_file(self, path, relative_to=None):
		"""Test if given path is file"""
		result = False
		real_path = self.real_path(path, relative_to)

		try:
			info = Gio.File.new_for_commandline_arg(real_path).query_info('standard::type', Gio.FileQueryInfoFlags.NONE, None)
			result = info.get_file_type() == Gio.FileType.REGULAR
		except GLib.GError as error:
			pass

		return result

	def is_dir(self, path, relative_to=None):
		"""Test if given path is directory"""
		result = False
		real_path = self.real_path(path, relative_to)

		try:
			info = Gio.File.new_for_commandline_arg(real_path).query_info('standard::type', Gio.FileQueryInfoFlags.NONE, None)
			result = info.get_file_type() == Gio.FileType.DIRECTORY
		except GLib.GError as error:
			pass

		return result

	def is_link(self, path, relative_to=None):
		"""Test if given path is a link"""
		real_path = self.real_path(path, relative_to)
		info = Gio.File.new_for_commandline_arg(real_path).query_info('standard::type', Gio.FileQueryInfoFlags.NONE, None)

		return info.get_file_type() == Gio.FileType.SYMBOLIC_LINK

	def exists(self, path, relative_to=None):
		"""Test if given path exists"""
		real_path = self.real_path(path, relative_to)
		return Gio.File.new_for_commandline_arg(real_path).query_exists()

	def unlink(self, path, relative_to=None):
		"""Unlink given path"""
		pass

	def remove_directory(self, path, relative_to=None):
		"""Remove directory and optionally its contents"""
		real_path = self.real_path(path, relative_to)
		file_list = []
		to_scan = []

		# add current path to the list
		file_list.append(real_path)
		to_scan.append(real_path)

		# traverse through directories
		# TODO: Check if this is really necessary. Recursive removal seems to be automatic.
		while len(to_scan) > 0:
			current_path = to_scan.pop(0)
			info_list = Gio.File.new_for_commandline_arg(current_path).enumerate_children('standard::name,standard::type', Gio.FileQueryInfoFlags.NONE, None)

			for info in info_list:
				name = info.get_name()
				item_path = os.path.join(current_path, name)

				# add item to the removal list
				file_list.append(item_path)

				# if item is directory, we need to scan it
				if info.get_file_type() == Gio.FileType.DIRECTORY:
					to_scan.append(item_path)

			info_list.close()

		# remove all items in reverse order
		file_list.reverse()
		for path in file_list:
			Gio.File.new_for_commandline_arg(path).delete()

	def remove_file(self, path, relative_to=None):
		"""Remove file"""
		real_path = self.real_path(path, relative_to)
		Gio.File.new_for_commandline_arg(real_path).delete()

	def create_file(self, path, mode=None, relative_to=None):
		"""Create empty file with specified mode set"""
		real_path = self.real_path(path, relative_to)
		Gio.File.new_for_commandline_arg(real_path).create()

		if Support.SET_ACCESS in self.get_support():
			self.set_mode(real_path, mode)

	def create_directory(self, path, mode=None, relative_to=None):
		"""Create directory with specified mode set"""
		real_path = self.real_path(path, relative_to)
		Gio.File.new_for_commandline_arg(real_path).make_directory_with_parents()

		if Support.SET_ACCESS in self.get_support():
			self.set_mode(real_path, mode)

	def get_file_handle(self, path, mode, relative_to=None):
		"""Open path in specified mode and return its handle"""
		real_path = self.real_path(path, relative_to)
		return File(real_path, mode)

	def get_stat(self, path, relative_to=None, extended=False, follow=False):
		"""Return file statistics"""
		real_path = self.real_path(path, relative_to)

		try:
			# try getting file stats
			flags = (
					Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
					Gio.FileQueryInfoFlags.NONE
				)[follow]

			file_stat = Gio.File.new_for_commandline_arg(real_path).query_info(
											'standard::size,unix::mode,unix::uid,unix::gid'
											'time::access,time::modified,time::changed,'
											'standard::type,unix:device,unix::inode',
											flags, None
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

		if file_type == Gio.FileType.SYMBOLIC_LINK:
			item_type = FileType.LINK

		elif file_type == Gio.FileType.DIRECTORY:
			item_type = FileType.DIRECTORY

		elif file_type == Gio.FileType.SPECIAL:
			item_type = FileType.DEVICE_BLOCK

		else:
			item_type = FileType.REGULAR

		if not extended:
			# create normal file information
			result = FileInfo(
						size = file_stat.get_size(),
						mode = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_MODE),
						user_id = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_UID),
						group_id = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_GID),
						time_modify = file_stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED),
						type = item_type,
					)
		else:
			# create extended file information
			result = FileInfoExtended(
						size = file_stat.get_size(),
						mode = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_MODE),
						i_mode = 0,
						user_id = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_UID),
						group_id = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_GID),
						time_access = file_stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_ACCESS),
						time_modify = file_stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED),
						time_change = file_stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_CHANGED),
						type = item_type,
						device = file_stat.get_attribute_uint32(Gio.FILE_ATTRIBUTE_UNIX_DEVICE),
						inode = file_stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_UNIX_INODE)
					)

		return result

	def set_mode(self, path, mode, relative_to=None):
		"""Set access mode to specified path"""
		real_path = self.real_path(path, relative_to)
		Gio.File.new_for_commandline_arg(real_path).set_attribute(
					Gio.FILE_ATTRIBUTE_UNIX_MODE,
					Gio.FILE_ATTRIBUTE_TYPE_UINT32,
					mode
				)

	def set_owner(self, path, owner=-1, group=-1, relative_to=None):
		"""Set owner and/or group for specified path"""
		real_path = self.real_path(path, relative_to)
		temp = Gio.File.new_for_commandline_arg(real_path)
		temp.set_attribute(
					Gio.FILE_ATTRIBUTE_UNIX_UID,
					Gio.FILE_ATTRIBUTE_TYPE_UINT32,
					owner
				)
		temp.set_attribute(
					Gio.FILE_ATTRIBUTE_UNIX_GID,
					Gio.FILE_ATTRIBUTE_TYPE_UINT32,
					group
				)

	def set_timestamp(self, path, access=None, modify=None, change=None, relative_to=None):
		"""Set timestamp for specified path"""
		real_path = self.real_path(path, relative_to)
		temp = Gio.File.new_for_commandline_arg(real_path)

		if access is not None:
			temp.set_attribute(
					Gio.FILE_ATTRIBUTE_TIME_ACCESS,
					Gio.FILE_ATTRIBUTE_TYPE_UINT64,
					long(access)
				)

		if modify is not None:
			temp.set_attribute(
					Gio.FILE_ATTRIBUTE_TIME_MODIFIED,
					Gio.FILE_ATTRIBUTE_TYPE_UINT64,
					long(modify)
				)

		if change is not None:
			temp.set_attribute(
					Gio.FILE_ATTRIBUTE_TIME_CHANGED,
					Gio.FILE_ATTRIBUTE_TYPE_UINT64,
					long(change)
				)

	def move_path(self, source, destination, relative_to=None):
		"""Move path on same file system to a different parent node """
		real_source = self.real_path(source, relative_to)
		Gio.File.new_for_commandline_arg(real_source).move(Gio.File.new_for_commandline_arg(destination))

	def rename_path(self, source, destination, relative_to=None):
		"""Rename file/directory within parents path"""
		real_source = self.real_path(source, relative_to)
		Gio.File.new_for_commandline_arg(real_source).set_display_name(destination)

	def list_dir(self, path, relative_to=None):
		"""Get directory list"""
		real_path = self.real_path(path, relative_to)
		directory = Gio.File.new_for_commandline_arg(real_path)
		result = []

		try:
			information = directory.enumerate_children('standard::name', Gio.FileQueryInfoFlags.NONE, None)
			for file_information in information:
				result.append(file_information.get_name())

			information.close()

		except GLib.GError as error:
			raise OSError(str(error))

		return result

	def get_root_path(self, path):
		"""Get root for specified path"""
		result = None

		# try to get mount
		mount = Gio.File.new_for_commandline_arg(path).find_enclosing_mount()

		# get root directory from mount
		if mount is not None:
			result = mount.get_root().get_uri()

		# remove trailing slash
		if result[-1] == os.path.sep:
			result = result[:-1]

		return unquote(result)

	def get_parent_path(self, path):
		"""Get parent path for specified"""
		return unquote(Gio.File.new_for_commandline_arg(path).get_parent().get_uri())

	def get_system_size(self, path):
		"""Return system size information"""
		try:
			stat = Gio.File.new_for_commandline_arg(path).query_filesystem_info('filesystem::size,filesystem::free')

			space_free = stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE)
			space_total = stat.get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_SIZE)

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
		try:
			result = LocalMonitor(self, path)

		except MonitorError as error:
			result = Provider.get_monitor(self, path)

		return result

	def get_support(self):
		"""Return supported options by provider"""
		return (
			Support.MONITOR,
			Support.SET_TIMESTAMP,
			Support.SET_ACCESS,
			Support.SET_OWNER,
			Support.SYSTEM_SIZE
		)


class SambaProvider(GioProvider):
	is_local = False
	protocol = 'smb'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'samba'

	def get_support(self):
		"""Return supported options by provider"""
		return (
			Support.SYSTEM_SIZE,
		)


class FtpProvider(GioProvider):
	is_local = False
	protocol = 'ftp'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'network'

	def get_support(self):
		"""Return supported options by provider"""
		return ()


class SftpProvider(GioProvider):
	is_local = False
	protocol = 'sftp'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'network'

	def get_support(self):
		"""Return supported options by provider"""
		return ()


class NetworkProvider(GioProvider):
	is_local = False
	protocol = 'network'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'network-workgroup'

	def get_support(self):
		"""Return supported options by provider"""
		return ()


class TrashProvider(GioProvider):
	is_local = True
	protocol = 'trash'

	def remove_directory(self, path, relative_to=None):
		"""Remove directory and optionally its contents"""
		real_path = self.real_path(path, relative_to)
		Gio.File.new_for_commandline_arg(real_path).delete()

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'user-trash'

	def get_support(self):
		"""Return supported options by provider"""
		return ()

	def get_root_path(self, path):
		"""Return root path."""
		return 'trash:///'


class DavProvider(GioProvider):
	is_local = False
	protocol = 'dav'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'network'

	def get_support(self):
		"""Return supported options by provider"""
		return (
			Support.SYSTEM_SIZE,
		)


class DavsProvider(GioProvider):
	is_local = False
	protocol = 'davs'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'network'

	def get_support(self):
		"""Return supported options by provider"""
		return (
			Support.SYSTEM_SIZE,
		)


class Gphoto2Provider(GioProvider):
	is_local = True
	protocol = 'gphoto2'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'camera-photo'

	def get_support(self):
		"""Return supported options by provider"""
		return ()


class MtpProvider(GioProvider):
	is_local = True
	protocol = 'mtp'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'multimedia-player'

	def get_support(self):
		"""Return supported options by provider"""
		return ()


class ArchiveProvider(GioProvider):
	is_local = True
	protocol = 'archive'

	def get_protocol_icon(self):
		"""Return protocol icon name"""
		return 'drive-removable-media'

	def get_support(self):
		"""Return supported options by provider"""
		return ()

	def get_root_path(self, path):
		"""Get root for specified path"""
		result = None

		# try to get mount
		mount = Gio.File.new_for_commandline_arg(path).find_enclosing_mount()

		# get root directory from mount
		if mount is not None:
			result = mount.get_root().get_uri()

		# remove trailing slash
		if result[-1] == os.path.sep:
			result = result[:-1]

		return result

