from gi.repository import Gtk


class ContextMenu:
	"""Interface which shows options and information related to current path."""

	def __init__(self, parent, relative_to):
		self._parent = parent

		# popover interface
		self._popover = Gtk.Popover.new()
		self._popover.set_relative_to(relative_to)
		self._popover.set_modal(True)
		self._popover.set_position(Gtk.PositionType.BOTTOM)

		# widget container
		self._container = Gtk.VBox.new(False, 10)
		self._container.set_border_width(5)

		# show all widgets inside of container
		self._container.show_all()

		# pack interface
		self._popover.add(self._container)

	def _prepare(self):
		"""Prepare all the data before interface is displayed."""
		pass

	def add_control(self, control, fill=False):
		"""Add specified control to the context menu."""
		control.show_all()
		self._container.pack_start(control, fill, False, 0)

	def show(self):
		"""Show context menu for current directory."""
		self._prepare()
		self._popover.popup()
