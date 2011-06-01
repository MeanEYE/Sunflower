import gtk


class SettingsPage(gtk.VBox):
	"""Abstract class used to build pages in preferences window."""
	
	def __init__(self, parent, application, name, title):
		gtk.VBox.__init__(self, False, 0)

		self._parent = parent
		self._application = application
		self._page_name = name
		self._page_title = title

		# configure self
		self.set_spacing(5)
		self.set_border_width(0)
		
		# add page to preferences window
		self._parent.add_tab(self._page_name, self._page_title, self)
		
	def _load_options(self):
		"""Load options and update interface"""
		pass

	def _save_options(self):
		"""Method called when save button is clicked"""
		pass