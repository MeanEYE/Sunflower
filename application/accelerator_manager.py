

class AcceleratorManager:

	def __init__(self, application):
		self._application = application

		self._groups = []
		self._group_names = []

	def register_group(self, group):
		"""Register group with manager"""
		pass

	def get_groups(self):
		"""Get list of unique group names"""
		pass

	def get_methods(self, name):
		"""Get list of methods for a specific group"""
		pass

	def get_accelerator(self, group, name, primary=True):
		"""Get saved accelerator"""
		result = None

		return result

	def save_accelerators(self):
		"""Save accelerator map"""
		pass

	def load_accelerators(self):
		"""Load accelerator map"""
		pass
