class Parameters:
	"""Simple class used as storage container for various parameters"""

	def __init__(self):
		self._parameters = {}

	def get(self, name, default=None):
		"""Get parameter"""
		return self._parameters[name] if self._parameters.has_key(name) else default

	def set(self, name, value):
		"""Set parameter"""
		self._parameters[name] = value
