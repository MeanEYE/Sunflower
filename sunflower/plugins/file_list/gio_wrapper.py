from gi.repository import Gio, GLib, GObject
from sunflower.common import escape_uri_path
from sunflower.plugin_base.provider import Mode

# GFile.read_bytes() has upper limit for size of
# G_MAXSSIZE (9223372036854775807) which is insensibly large
MAX_READ_FILE_SIZE = 4*1024*1024*1024


def get_file(path):
	"""Return GIO file object for path used within the program."""
	return Gio.File.new_for_commandline_arg(escape_uri_path(path))


class File:
	"""This is a wrapper class that provides file-like object but
	uses Gio.File for actual operations."""

	def __init__(self, path, mode):
		if mode == Mode.READ:
			self._resource = get_file(path).read()

		elif mode == Mode.WRITE:
			if get_file(path).query_exists():
				get_file(path).delete()  # have to manually remove since flag doesn't work

			self._resource = get_file(path).create(
					Gio.FileCreateFlags.REPLACE_DESTINATION  # doesn't seem to do anything
					)

		elif mode == Mode.APPEND:
			self._resource = get_file(path).append_to()

	def __enter__(self):
		"""Set opened file as runtime context"""
		return self._resource

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""Close file on exit from context"""
		self.close()

	def close(self):
		"""Close file"""
		self._resource.close()

	def closed(self):
		"""If file is closed"""
		self._resource.is_closed()

	def flush(self):
		"""Flush internal buffer"""
		if hasattr(self._resource, 'flush'):
			self._resource.flush()

	def read(self, size=MAX_READ_FILE_SIZE):
		"""Read at most _size_ bytes from the file"""
		result = self._resource.read_bytes(size)

		if result is True:
			result = ""

		return result.get_data()

	def seek(self, offset, whence=0):
		"""Set the file's current position"""
		relative = (1, 0, 2)[whence]

		if self._resource.can_seek():
			self._resource.seek(offset, relative)

	def tell(self):
		"""Return file's current position"""
		return self._resource.tell()

	def truncate(self, size=None):
		"""Truncate the file's size"""
		if size is None:
			size = self.tell()

		if self._resource.can_truncate():
			self._resource.truncate(size)

	def write(self, buff):
		"""Write string to the file"""
		self._resource.write(buff)
