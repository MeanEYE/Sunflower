import gtk

from widgets.settings_page import SettingsPage


class TerminalOptions(SettingsPage):
	"""Terminal options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'terminal', _('Terminal'))

		# create interface
		self._checkbox_scrollbars_visible = gtk.CheckButton(_('Show scrollbars when needed'))
		self._checkbox_scrollbars_visible.connect('toggled', self._parent.enable_save)

		# pack interface
		self.pack_start(self._checkbox_scrollbars_visible, False, False, 0)

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options

		self._checkbox_scrollbars_visible.set_active(options.getboolean('main', 'terminal_scrollbars'))

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options
		_bool = ('False', 'True')

		options.set('main', 'terminal_scrollbars', _bool[self._checkbox_scrollbars_visible.get_active()])
