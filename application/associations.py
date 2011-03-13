import os

from urllib import quote
from ConfigParser import ConfigParser

class AssociationManager:
	"""Class that provides 'Open With' menu"""

	def __init__(self):

		# application config section
		self._config_section = 'Desktop Entry'

		# user defined list
		self._user_section = 'Added Associations'
		self._user_path = os.path.expanduser('~/.local/share/applications')
		self._user_file = 'mimeapps.list'

		#system defined list
		self._default_section = 'Default Applications'
		self._default_path = '/usr/share/applications'
		self._default_file = 'mimeinfo.cache'

		self._config = ConfigParser()
		self._config.read([
						os.path.join(self._default_path, self._default_file),
						os.path.join(self._user_path, self._user_file)
					])

	def get_user_list(self, mime_type):
		"""Returns user defined file association"""
		result = None

		# if section is loaded and mime type is defined get application list
		if self._config.has_section(self._user_section) \
		and self._config.has_option(self._user_section, mime_type):
			result = self._config.get(
									self._user_section,
									mime_type
								).split(';')

		return result

	def get_default_list(self, mime_type):
		"""Returns system default file associtation"""
		result = None

		if self._config.has_section(self._default_section) \
		and self._config.has_option(self._default_section, mime_type):
			result = self._config.get(
									self._default_section,
									mime_type
								).split(';')

		return result

	def get_association_config(self, file_name):
		"""Return dictionary containing all the options"""
		result = None
		config = ConfigParser()

		if os.path.exists(os.path.join(self._user_path, file_name)):
			config.read(os.path.join(self._user_path, file_name))

		elif os.path.exists(os.path.join(self._default_path, file_name)):
			config.read(os.path.join(self._default_path, file_name))

		if config.has_section(self._config_section):
			result = dict(config.items(self._config_section))

		return result

	def open_file_with_config(self, callback, config_file):
		"""Open filename using config data"""
		config = self.get_association_config(config_file)
		get_file_list = callback

		if config is None: return

		exec_string = config['exec']

		file_list = get_file_list()

		if file_list is not None:
			exec_string = exec_string.replace('%f', "'{0}'".format(file_list[0]))
			exec_string = exec_string.replace('%F', " ".join("'{0}'".format(file) for file in file_list))
			exec_string = exec_string.replace('%u', 'file://{0}'.format(quote(file_list[0])))
			exec_string = exec_string.replace('%U', " ".join('file://{0}'.format(quote(file)) for file in file_list))
			exec_string = exec_string.replace('%d', "'{0}'".format(os.path.dirname(file_list[0])))
			exec_string = exec_string.replace('%D', " ".join("'{0}'".format(os.path.dirname(file) for file in file_list)))
			exec_string = exec_string.replace('%n', "'{0}'".format(os.path.basename(file_list[0])))
			exec_string = exec_string.replace('%N', " ".join("'{0}'".format(os.path.basename(file) for file in file_list)))

			os.system('{0} &'.format(exec_string))
