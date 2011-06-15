import gtk


class StatusBar(gtk.HBox):
	"""Plugin status bar"""

	def __init__(self):
		gtk.HBox.__init__(self, False, 3)

		# create default label
		self._label = gtk.Label()
		self._label.set_use_markup(True)
		self._label.set_alignment(0, 0.5)

		# pack interface
		self.pack_end(self._label, True, True, 0)

	def set_text(self, text):
		"""Set default label text"""
		self._label.set_markup(text)
