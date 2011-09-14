import gtk


class Button(gtk.ToolButton):
	"""Go to parent directory toolbar button"""

	def __init__(self, application, name, config):
		gtk.ToolButton.__init__(self)

		self._name = name
		self._config = config
		self._application = application

		self.set_label(_('Go to parent directory'))
		self.set_tooltip_text(_('Go to parent directory'))
		self.set_icon_name('go-up')

		self.connect('clicked', self._clicked)

	def _clicked(self, widget, data=None):
		"""Handle button click"""
		active_object = self._application.get_active_object()

		if hasattr(active_object, '_parent_directory'):
			active_object._parent_directory()
