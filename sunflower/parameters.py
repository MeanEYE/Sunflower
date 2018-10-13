class Parameters:
	"""Simple class used as storage container for various parameters"""

	def __init__(self, params=None):
		self._parameters = {} if params is None else params.copy()

	def get(self, name, default=None):
		"""Get parameter"""
		return self._parameters[name] if name in self._parameters else default

	def set(self, name, value):
		"""Set parameter"""
		self._parameters[name] = value

	def get_params(self):
		"""Get copy of parameters"""
		return self._parameters.copy()

	def copy(self):
		"""Return copy of parameters"""
		return Parameters(self.get_params())
