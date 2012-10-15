import user

from bookmark_button import Button as BookmarkButton


class Button(BookmarkButton):
	"""Home directory toolbar button"""

	def __init__(self, application, name, config):
		BookmarkButton.__init__(self, application, name, config)

		self._path = user.home

	def _set_label(self):
		"""Set button label"""
		self.set_label(_('Home directory'))
		self.set_tooltip_text(_('Home directory'))

	def _set_icon(self):
		"""Set button icon"""
		self.set_icon_name('user-home')
