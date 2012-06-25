import json


class Config:
	"""This class provides easy way to create and edit configuration files
	located in Sunflower's configuration directory. 
	
	It is recomended that this class is used for all purposes of storing 
	data used by program itself and	plugins!
	
	"""

	encoder_options = {
				'skipkeys': True,
				'check_circular': True,
				'sort_keys': True,
				'indent': 1
			}

	def __init__(self, name):
		self._name = name
		self._sections = {}

		self._encoder = json.JSONEncoder(*self.encoder_options)
		self._decoder = json.JSONDecoder()

	def save(self):
		"""Save options to configuration file"""
		pass

	def load(self):
		"""Load options from configuration file"""
		pass

	def add_section(self, name, section):
		"""Add new section to configutation"""
		self._values[name] = section

	def create_section(self, name):
		"""Create and return new section object"""
		section = Section()
		self._values[name] = section

		return section

	def get_sections(self):
		"""Get list of all sections available"""
		return self._sections.keys()

	def section(self, name):
		"""Retrieve specified section object"""
		assert name in self._sections
		return self._sections[name]

	def has_section(self, name):
		"""Check for existance of section"""
		return name in self._sections


class Container:
	"""Generic configuration container"""

	def __init__(self, data=None):
		self._values = {}

		if data is not None:
			self._values = data

	def _get_data(self):
		"""Get data for storage"""
		return self._values

	def set(self, name, value):
		"""Set configuration value"""
		self._values[name] = value

	def get(self, name):
		"""Get configuration value"""
		return self._values[name] if name in self._values else None
