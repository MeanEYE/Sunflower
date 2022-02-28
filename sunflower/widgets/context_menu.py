from gi.repository import Gtk


class ContextMenu:
	"""Interface which shows options and information related to current path."""

	def __init__(self, parent, relative_to):
		self._parent = parent

		# create popover interface
		self._popover = Gtk.Popover.new()
		self._popover.set_relative_to(relative_to)
		self._popover.set_position(Gtk.PositionType.BOTTOM)

		# create widget container
		self._container = Gtk.VBox.new(False, 10)
		self._container.set_border_width(10)

		# show all widgets inside of container
		self._container.show_all()

		# pack interface
		self._popover.add(self._container)

	def add_control(self, control, fill=False, spacing=0):
		"""Add specified control to the context menu."""
		control.show_all()
		self._container.pack_start(control, fill, False, spacing)

	def show(self):
		"""Show context menu for current directory."""
		self._popover.popup()
