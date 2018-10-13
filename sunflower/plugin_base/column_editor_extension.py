class ColumnEditorExtension:
	"""Class used for extending column editor in preferences window"""

	def __init__(self, parent, config):
		self._parent = parent
		self._parent_name = parent._name
		self._config = config

	def _save_settings(self):
		"""Save values to config"""
		pass

	def _load_settings(self):
		"""Load values from config"""
		pass

	def get_name(self):
		"""Get plugin's name"""
		pass

	def get_columns(self, only_visible=False):
		"""Get column names"""

	def get_size(self, column):
		"""Get column size"""
		pass

	def get_font_size(self, column):
		"""Get column font size"""
		pass

	def get_visible(self, column):
		"""Get column visibility"""
		pass

	def set_size(self, column, size):
		"""Set column size"""
		pass

	def set_visible(self, column, visible):
		"""Set column visibility"""
		pass
