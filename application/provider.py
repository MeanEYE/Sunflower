#!/usr/bin/env python

class Provider:
	is_local = True  # if provider handles local files
	
	def __init__(self, parent):
		self._parent = parent

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
	
	def get_stat(self, path, relative_to=None):
		"""Return file statistics"""
		pass

	def get_selection(self, relative=False):
		"""Get list of selected items"""
		return self._parent._get_selection_list(relative=relative)
	
	def get_path(self):
		"""Return parents path"""
		return self._parent.path
	
	def set_mode(self, path, mode, relative_to=None):
		"""Set access mode to specified path"""
		pass
	
	def set_owner(self, path, owner=-1, group=-1, relative_to=None):
		"""Set owner and/or group for specified path"""
		pass
	
	def remove_path(self, path, recursive=True, relative_to=None):
		"""Remove path"""
		if self.is_link(path, relative_to):  # handle links
			self.unlink(path, relative_to)

		elif self.is_dir(path, relative_to):  # handle directories
			self.remove_directory(path, recursive, relative_to)

		else:  # handle files
			self.remove_file(path, relative_to)
			
	def rename_path(self, source, destination, relative_to=None):
		"""Rename file/directory within parents path"""
		pass
			
	def list_dir(self, path, relative_to=None):
		"""Get directory list"""
		pass
