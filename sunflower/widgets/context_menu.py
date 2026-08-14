from gi.repository import Gtk


class ContextMenu:
	"""Interface which shows options and information related to current path."""

	def __init__(self, parent, relative_to):
		self._parent = parent

		# create popover interface
		self._popover = Gtk.Popover.new()
		if Gtk.get_major_version() == 3:
			self._popover.set_relative_to(relative_to)

		else:
			self._popover.set_parent(relative_to)
		self._popover.set_position(Gtk.PositionType.BOTTOM)

		# create widget container
		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
		set_border_width(self._container, 10)

		# show all widgets inside of container
		if Gtk.get_major_version() == 3:
			self._container.show_all()

		else:
			self._container.show()

		# pack interface
		if Gtk.get_major_version() == 3:
			self._popover.add(self._container)

		else:
			self._popover.set_child(self._container)

	def add_control(self, control, fill=False, spacing=0):
		"""Add specified control to the context menu."""
		if Gtk.get_major_version() == 3:
			control.show_all()

			self._container.pack_start(control, fill, False, spacing)

		else:
			control.show()

			set_border_width(control, spacing)
			self._container.append(control)

	def show(self):
		"""Show context menu for current directory."""
		self._popover.popup()
