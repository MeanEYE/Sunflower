from gi.repository import Gtk, GObject


# GTK 4 removed tool items, a plain separator is used instead
if Gtk.get_major_version() == 3:
	SeparatorBase = Gtk.SeparatorToolItem

else:
	SeparatorBase = Gtk.Separator


class Separator(SeparatorBase):
	"""Toolbar separator widget"""

	def __init__(self, application, name, config):
		GObject.GObject.__init__(self)
