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
		self._resource = None
		self._input = None
		self._output = None

		if mode == Mode.READ:
			self._resource = get_file(path).read()
			self._input = self._resource

		elif mode == Mode.WRITE:
			if get_file(path).query_exists():
				get_file(path).delete()  # have to manually remove since flag doesn't work

			self._resource = get_file(path).create(
					Gio.FileCreateFlags.REPLACE_DESTINATION  # doesn't seem to do anything
					)
			self._output = self._resource

		elif mode == Mode.APPEND:
			self._resource = get_file(path).append_to()
			self._output = self._resource

		elif mode == Mode.READ_APPEND:
			try:
				# single stream is used for seeking with separate ones for data
				self._resource = get_file(path).open_readwrite()
				self._input = self._resource.get_input_stream()
				self._output = self._resource.get_output_stream()

			except GLib.Error:
				# not all file systems support writing, or allow it for this file
				self._resource = get_file(path).read()
				self._input = self._resource

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
		return self._resource.is_closed()

	def readable(self):
		"""If file can be read from"""
		return self._input is not None

	def writable(self):
		"""If file can be written to"""
		return self._output is not None

	def seekable(self):
		"""If position in the file can be changed"""
		return self._resource.can_seek()

	def flush(self):
		"""Flush internal buffer"""
		if self._output is not None:
			self._output.flush()

	def read(self, size=MAX_READ_FILE_SIZE):
		"""Read at most _size_ bytes from the file"""
		if size is None or size < 0:
			size = MAX_READ_FILE_SIZE

		result = b''

		# streams are allowed to return less data than requested,
		# which is something code reading files doesn't expect
		while len(result) < size:
			data = self._input.read_bytes(size - len(result)).get_data()

			if not data:
				break

			result += data

		return result

	def seek(self, offset, whence=0):
		"""Set the file's current position"""
		relative = (GLib.SeekType.SET, GLib.SeekType.CUR, GLib.SeekType.END)[whence]

		if self._resource.can_seek():
			try:
				self._resource.seek(offset, relative)

			except GLib.Error as error:
				# report the way file objects are expected to
				raise OSError(str(error))

		return self.tell()

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
		"""Write data to the file"""
		# plain write is allowed to store only part of the data
		self._output.write_all(buff, None)

		return len(buff)
