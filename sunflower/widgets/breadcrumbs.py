from __future__ import absolute_import

import os

from gi.repository import Gtk, GObject
from sunflower.common import decode_file_name


class Breadcrumbs:
	"""Linked list of buttons navigating to different paths."""

	def __init__(self, parent):
		self.container = Gtk.ScrolledWindow.new()
		self.container.set_overlay_scrolling(True)
		self.container.set_placement(Gtk.CornerType.TOP_RIGHT)
		self.container.get_hscrollbar().hide()

		self.box = Gtk.HBox.new(False, 0)
		self.container.add_with_viewport(self.box)

		# change the look of container
		self.container.set_focus_on_click(False)
		self.container.get_style_context().add_class('sunflower-breadcrumbs')

		self._path = None
		self._parent = parent
		self._updating = False
		self._group = None

		self.container.show_all()

	def __fragment_click(self, widget, data=None):
		"""Handle clicking on path fragment."""
		if self._updating:
			return

		# ignore non active buttons
		if not widget.props.active:
			return

		# change path
		file_list = self._parent._parent
		if hasattr(file_list, 'change_path'):
			file_list.change_path(widget.path)

	def _focus_fragment(self, fragment, is_new=True):
		"""Set fragment as active and present it to user."""
		allocation = fragment.get_allocation()
		adjustment = self.container.get_hadjustment()
		container_size = self.container.get_allocation().width

		if is_new:
			position = adjustment.get_upper()
		elif allocation.x + allocation.width > container_size:
			position = allocation.x + allocation.width + 20
		else:
			position = 0

		adjustment.set_value(position)
		fragment.set_active(True)

	def set_state(self, state):
		"""Set widget state."""
		self._state = state

	def refresh(self, path):
		"""Update buttons on directory change."""
		provider = self._parent._parent.get_provider()

		# prevent signal dead-loops
		self._updating = True

		if self._path is not None and self._path.startswith(path):
			# path is a subset, update highlight and exit
			for control in self.box.get_children():
				if control.path == path:
					self._focus_fragment(control, is_new=False)
					break

		else:
			# prepare for parsing
			self._path = path
			self.box.foreach(self.box.remove)

			# split root element from others
			root_element = provider.get_root_path(path)
			other_elements = path[len(root_element):]

			# make sure our path doesn't begin with slash
			if other_elements.startswith(os.path.sep):
				other_elements = other_elements[1:]

			# split elements
			elements = other_elements.split(os.path.sep)
			elements.insert(0, root_element)

			# create controls
			control = None
			current_path = None
			for element in elements:
				current_path = os.path.join(current_path, element) if current_path is not None else element
				control = Fragment(decode_file_name(element), current_path, self.__fragment_click, control)
				self.box.pack_start(control, False, False, 0)

			if control is not None:
				GObject.idle_add(self._focus_fragment, control, is_new=True)

		# prevent signal dead-loops
		self._updating = False


class Fragment(Gtk.HBox):
	"""Simple path fragment containing necessary widgets."""

	def __init__(self, text, path, click_handler, previous):
		Gtk.HBox.__init__(self)

		self.path = path
		self.click_handler = click_handler

		# create separator label
		if previous is not None:
			label = Gtk.Label.new('/')
			self.pack_start(label, False, False, 0)

		# create button
		self._button = Gtk.RadioButton.new()
		self._button.set_focus_on_click(False)
		self._button.set_mode(False)
		self._button.connect('clicked', self.click_handler)
		self._button.path = path

		if previous is None:
			image = Gtk.Image.new_from_icon_name('drive-harddisk-symbolic', Gtk.IconSize.BUTTON)
			self._button.set_image(image)
		else:
			self._button.set_label(text)

		if previous is not None:
			self._button.join_group(previous._button)

		self.pack_start(self._button, False, False, 0)

		self.show_all()

	def set_active(self, active):
		"""Set button active state."""
		self._button.handler_block_by_func(self.click_handler)
		self._button.set_active(active)
		self._button.handler_unblock_by_func(self.click_handler)
