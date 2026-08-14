from gi.repository import Gtk


class CommandRow(Gtk.ListBoxRow):
	"""List item which is used for displaying items in commands menu."""

	def __init__(self, name, command):
		Gtk.ListBoxRow.__init__(self)

		self._command = command

		self.set_selectable(True)
		self.set_activatable(True)
		self.set_focus_on_click(True)

		# create interface
		if Gtk.get_major_version() == 3:
			box = Gtk.EventBox.new()

		else:
			# GTK 4 removed event boxes, every widget receives events on its own
			box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

		set_border_width(box, 5)
		if Gtk.get_major_version() == 3:
			self.add(box)

		else:
			self.set_child(box)

		label = Gtk.Label.new(name)
		label.set_xalign(0)
		label.set_yalign(0.5)
		if Gtk.get_major_version() == 3:
			box.add(label)
			self.show_all()

		else:
			box.append(label)

	def _get_command(self):
		"""Return command for execution."""
		return self._command

	command = property(_get_command)
