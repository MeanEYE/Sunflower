import gtk


class Button(gtk.ToolButton):
	"""Toolbar control used to popup bookmarks menu"""

	def __init__(self, application, name, config):
		gtk.ToolButton.__init__(self)

		# store parameters locally
		self._name = name
		self._config = config
		self._application = application

		# configure
		self.set_label(_('Bookmarks'))
		self.set_tooltip_text(_('Bookmarks'))
		self.set_icon_name('go-jump')
		self.set_is_important(True)

		# connect events
		self.connect('clicked', self._clicked)

	def _clicked(self, widget, data=None):
		"""Handle click"""
		self._application.show_bookmarks_menu(widget=self)
