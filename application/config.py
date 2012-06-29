import os
import json


class Container:
	"""Generic configuration container"""

	def __init__(self, data=None):
		self._values = {}

		if data is not None:
			self._values = data

	def _get_data(self):
		"""Get data for storage"""
		return self._values.copy()

	def set(self, name, value):
		"""Set configuration value"""
		self._values[name] = value

	def get(self, name):
		"""Get configuration value"""
		return self._values[name] if name in self._values else None

	def has(self, name):
		"""Check if options with specified name exists"""
		return name in self._values

	def remove(self, name):
		"""Remove option from container"""
		assert name in self._values
		del self._values[name]

	def update(self, options):
		"""Update missing options"""
		difference = dict(filter(lambda item: item[0] not in self._values, options.items()))
		self._values.update(difference)


class Config(Container):
	"""This class provides easy way to create and edit configuration files
	located in project's configuration directory. 
	
	It is recomended that this class is used for all purposes of storing 
	data used by program itself and	plugins!
	
	"""

	encoder_options = {
				'skipkeys': True,
				'check_circular': True,
				'sort_keys': True,
				'indent': 4
			}

	def __init__(self, name, application):
		Container.__init__(self)

		self._name = name
		self._sections = {}
		self._application = application

		self._encoder = json.JSONEncoder(**self.encoder_options)
		self._decoder = json.JSONDecoder()

		# try to load config file
		self.load()

	def save(self):
		"""Save options to configuration file"""
		data = self._get_data()
		file_name = os.path.join(
						self._application.config_path,
						'{0}.json'.format(self._name)
					)

		# merge sections with main values
		for name, section in self._sections.items():
			data[name] = section._get_data()

		# save output to file
		with open(file_name, 'w') as raw_file:
			raw_file.write(self._encoder.encode(data))

	def load(self):
		"""Load options from configuration file"""
		file_name = os.path.join(
						self._application.config_path,
						'{0}.json'.format(self._name)
					)

		if not os.path.exists(file_name):
			return

		try:
			# try loading config file
			data = self._decoder.decode(open(file_name).read())

		except ValueError:
			# if error occurs, we'll just ignore it
			# empty config is not that scary
			pass
	
		else:
			# finish the loading
			for name, values in data.items():
				if type(values) is dict:
					# section
					self._sections[name] = Container(values)

				else:
					# normal value
					self._values[name] = values

	def add_section(self, name, section):
		"""Add new section to configutation"""
		self._sections[name] = section

	def create_section(self, name):
		"""Create and return new section object"""
		if not name in self._sections:
			self._sections[name] = Container()

		return self._sections[name]

	def remove_section(self, name):
		"""Remove section from config"""
		assert name in self._sections
		del self._sections[name]

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
