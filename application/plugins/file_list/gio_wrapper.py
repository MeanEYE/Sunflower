import gio


class File:
	"""This is a wrapper class that provides file-like object but
	uses gio.File for actual operations."""

	def __init__(self):
		pass

	def close(self):
		"""Close file"""
		pass

	def flush(self):
		"""Flush internal buffer"""
		pass

	def read(self, size):
		"""Read at most _size_ bytes from the file"""
		pass

	def seek(offset, whence=None):
		"""Set the file's current position"""
		pass

	def tell(self):
		"""Return file's current position"""
		pass

	def truncate(self, size=None):
		"""Truncate the file's size"""
		pass

	def write(self, buff):
		"""Write string to the file"""
		pass
