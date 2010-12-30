#!/usr/bin/env python

class Provider:
	is_local = True  # if provider handles local files
	
	def __init__(self, parent):
		self._parent = parent

	def is_file(self, path, relative=False):
		"""Test if given path is file"""
		pass

	def is_dir(self, path, relative=False):
		"""Test if given path is directory"""
		pass

	def is_link(self, path, relative=False):
		"""Test if given path is a link"""
		pass
	
	def exists(self, path, relative=False):
		"""Test if given path exists"""
		pass

	def unlink(self, path, relative=False):
		"""Unlink given path"""
		pass

	def remove_directory(self, path, recursive, relative=False):
		"""Remove directory and optionally its content"""
		pass

	def remove_file(self, path, relative=False):
		"""Remove file"""
		pass
	
	def create_file(self, path, mode=None, relative=False):
		"""Create empty file with specified mode set"""
		pass
	
	def create_directory(self, path, mode=None, relative=False):
		"""Create directory with specified mode set"""
		pass

	def get_file_handle(self, path, mode, relative=False):
		"""Open path in specified mode and return its handle"""
		pass
	
	def get_stat(self, path, relative=False):
		"""Return file statistics"""
		pass

	def get_selection(self, relative=False):
		"""Get list of selected items"""
		return self._parent._get_selection_list()
	
	def get_path(self):
		"""Return parents path"""
		return self._parent.path
	
	def remove_path(self, path, recursive=True, relative=False):
		"""Remove path"""
		if self.is_link(path, relative):  # handle links
			self.unlink(path, relative)

		elif self.is_dir(path, relative):  # handle directories
			self.remove_directory(path, recursive, relative)

		else:  # handle files
			self.remove_file(path, relative)
			
	def rename_path(self, source, destination, relative=False):
		"""Rename file/directory within parents path"""
		pass
			
	def list_dir(self, path, relative=False):
		"""Get directory list"""
		pass
