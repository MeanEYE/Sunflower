class ViewerExtension:
	"""Base class used for extending viewer tool"""

	def __init__(self, parent):
		self._parent = parent

	def get_title(self):
		"""Return page title"""
		pass

	def get_container(self):
		"""Return container widget to be embeded to notebook"""
		pass

	def focus_object(self):
		"""Focus main object in extension"""
		pass
