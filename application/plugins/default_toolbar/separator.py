from gi.repository import Gtk


class Separator(Gtk.SeparatorToolItem):
	"""Toolbar separator widget"""

	def __init__(self, application, name, config):
		GObject.GObject.__init__(self)
