import os

from gi.repository import Gtk, GObject


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

		if self._path is not None and self._path.startswith(path):
			# path is a subset, update highlight and exit
			for control in self.get_children():
				if control.path == path:
					control.set_active(True)
					break

		else:
			# prepare for parsing
			self._path = path
			self.foreach(self.remove)

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

				if control is not None:
					control = Gtk.RadioButton.new_from_widget(control)
				else:
					control = Gtk.RadioButton.new()

				control.set_focus_on_click(False)
				control.set_label(element)
				control.set_mode(False)
				control.connect('clicked', self.__fragment_click)
				control.path = current_path
				control.show()

				self.pack_start(control, False, False, 0)

			if control is not None:
				control.set_active(True)

		# prevent signal dead-loops
		self._updating = False

