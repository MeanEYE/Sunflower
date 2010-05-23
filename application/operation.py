#!/usr/bin/env python

import time
import gobject

from threading import Thread
from gui.operation_dialog import CopyDialog, DeleteDialog


class Operation(Thread):
	"""Parent class for all operation threads"""

	def __init__(self, application, source, destination):
		Thread.__init__(self, target=self)

		self._paused = False
		self._can_continue = True
		self._application = application
		self._source = source
		self._destination = destination
		self._dialog = None

	def _destroy_ui(self):
		"""Destroy user interface"""
		if self._dialog is not None:
			self._dialog.destroy()

	def _update_ui(self):
		"""Abstract method used for interface updates"""
		pass

	def exit(self):
		"""Set an abort switch"""
		self._can_continue = False


class CopyOperation(Operation):
	"""Operation thread used for copying files"""

	def __init__(self, application, source, destination):
		Operation.__init__(self, application, source, destination)

		self._dialog = CopyDialog(application, self)

	def _update_ui(self, fraction):
		"""Update user interface"""
		self._dialog.set_current_file_fraction(fraction)
	
	def _copy_file(self, sh, dh):
		pass

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		for fraction in range(0, 60):
			print "current: {0}".format(fraction)
			time.sleep(0.2)
			gobject.idle_add(self._update_ui, float(fraction) / 60)

			# if we are not allowed to continue, exit
			if not self._can_continue: break

		gobject.idle_add(self._destroy_ui)


class MoveOperation(CopyOperation): pass


class DeleteOperation(Operation):
	"""Operation thread used for deleting files"""

	def __init__(self, application, source, destination):
		Operation.__init__(self, application, source, destination)
		self._dialog = DeleteDialog(application, self)

	def _update_ui(self, path, fraction):
		"""Update user interface"""
		self._dialog.set_current_file(path)
		self._dialog.set_current_file_fraction(fraction)

	def run(self):
		"""Main thread method, this is where all the stuff is happening"""
		self._dialog.show_all()

		list = self._source.get_selection()

		for index, item in enumerate(list, 1):
			gobject.idle_add(self._update_ui, item, float(index) / len(list))
			self._source.remove_path(item)

			# if we are not allowed to continue, exit
			if not self._can_continue: break

		gobject.idle_add(self._destroy_ui)
