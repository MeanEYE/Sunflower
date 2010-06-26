#!/usr/bin/env python

class Provider:
	is_local = True  # if provider handles local files
	
	def __init__(self, parent):
		self._parent = parent

	def _is_file(self, path):
		"""Test if given path is file"""
		pass

	def _is_dir(self, path):
		"""Test if given path is directory"""
		pass

	def _is_link(self, path):
		"""Test if given path is a ling"""
		pass

	def _unlink(self, path):
		"""Unlink given path"""
		pass

	def _remove_directory(self, path, recursive):
		"""Remove directory and optionally its contense"""
		pass

	def _remove_file(self, path):
		"""Remove file"""
		pass
	
	def create_file(self, path, mode=None):
		"""Create empty file with specified mode set"""
		pass
	
	def create_directory(self, path, mode=None):
		"""Create directory with specified mode set"""
		pass

	def get_file_handle(self, path, mode):
		"""Open path in specified mode and return its handle"""
		pass
	
	def get_stat(self, path):
		"""Return file statistics"""
		pass

	def get_selection(self):
		"""Get list of selected items"""
		return self._parent._get_selection_list()
	
	def get_path(self):
		"""Return parents path"""
		return self._parent.path
	
	def remove_path(self, path, recursive=True):
		"""Remove path"""
		if self._is_link(path):  # handle links
			self._unlink(path)

		elif self._is_dir(path):  # handle directories
			self._remove_directory(path, recursive)

		else:  # handle files
			self._remove_file(path)
			
	def rename_path(self, source, destination):
		"""Rename file/directory within parents path"""
		pass
			
	def list_dir(self, path):
		"""Get directory list"""
		pass
