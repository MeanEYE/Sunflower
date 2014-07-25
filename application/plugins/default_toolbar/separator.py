from gi.repository import Gtk


class Separator(Gtk.SeparatorToolItem):
	"""Toolbar separator widget"""

	def __init__(self, application, name, config):
		Gtk.SeparatorToolItem.__init__(self)
