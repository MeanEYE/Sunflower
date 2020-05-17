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
		box = Gtk.EventBox.new()
		box.set_border_width(5)
		self.add(box)

		label = Gtk.Label.new(name)
		label.set_alignment(0, 0.5)
		box.add(label)

		self.show_all()

	def _get_command(self):
		"""Return command for execution."""
		return self._command

	command = property(_get_command)
