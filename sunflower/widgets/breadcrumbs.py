# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
if sys.version_info[0] == 2:
	def accumulate(iterable, func):
		def accumuloreductrix(so_far, and_beyond):
			return so_far + [func(so_far[-1], and_beyond)]
		it = iter(iterable)
		try:
			first = it.next()
		except StopIteration:
			return []
		return reduce(accumuloreductrix, it, [first])
else:
	from itertools import accumulate

import os

from gi.repository import Gtk, GObject, GLib, Gdk
from ..common import disp_fn

class Breadcrumbs(Gtk.HBox):
	"""Linked list of buttons navigating to different paths."""

	def __init__(self, parent):
		GObject.GObject.__init__(self)

		# change the look of container
		self.set_focus_on_click(False)
		self.get_style_context().add_class('linked')
		self.get_style_context().add_class('path-bar')

		self._path = None
		self._parent = parent
		self._updating = False
		self._truncated = False

	def __fragment_click(self, widget, data=None):
		"""Handle clicking on path fragment."""
		if self._updating:
			return

		# change path
		file_list = self._parent._parent
		if hasattr(file_list, 'change_path'):
			file_list.change_path(widget.path)

	def set_state(self, state):
		"""Set widget state."""
		self._state = state

	def refresh(self, path):
		"""Update buttons on directory change."""
		provider = self._parent._parent.get_provider()

		# prevent signal dead-loops
		self._updating = True

		if self._path is not None and self._path.startswith(path) and not self._truncated:
			# path is a subset, update highlight and exit
			for control in self.get_children():
				if control.path == path:
					control.set_active(True)
					break

		else:
			# prepare for parsing
			self._path = path
			self.foreach(self.remove)
			self._truncated = False

			# split root element from others
			root_element = provider.get_root_path(path)
			other_elements = path[len(root_element):]

			# make sure our path doesn't begin with slash
			if other_elements.startswith(os.path.sep):
				other_elements = other_elements[1:]

			# split elements
			elements = other_elements.split(os.path.sep)
			elements.insert(0, root_element)
			paths = list(accumulate(elements, os.path.join))

			# create controls
			control = None
			current_path = None

			my_width = self.get_allocated_width()
			# We need the width to properly draw the breadcrumbs. Wait until it's allocated.
			if my_width == 1:
				self._updating = False
				self._path = None
				Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE-10, self.refresh, path)
				return

			reversed_controls = []
			required_width = 0

			for current_path, element in zip(reversed(paths), reversed(elements)):
				if control is not None:
					control = Gtk.RadioButton.new_from_widget(control)
				else:
					control = Gtk.RadioButton.new()

				control.set_focus_on_click(False)
				control.set_label(disp_fn(element))
				control.set_mode(False)
				control.connect('clicked', self.__fragment_click)
				control.path = current_path
				control.show()

				min_w, natural_w = control.get_preferred_width()
				required_width += natural_w

				if required_width >= my_width:
					reversed_controls[-1].set_label('…')
					self._truncated = True
					break

				reversed_controls.append(control)

			for control in reversed(reversed_controls):
				self.pack_start(control, False, False, 0)

			if control is not None:
				control.set_active(True)

		# prevent signal dead-loops
		self._updating = False

