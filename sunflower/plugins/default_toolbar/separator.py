from gi.repository import Gtk, GObject


from sunflower.plugins.default_toolbar import SeparatorBase


class Separator(SeparatorBase):
	"""Toolbar separator widget"""

	def __init__(self, application, name, config):
		GObject.GObject.__init__(self)
