import gtk


class Separator(gtk.SeparatorToolItem):
	"""Toolbar separator widget"""

	def __init__(self, application, name, config):
		gtk.SeparatorToolItem.__init__(self)
