import os
import gnomevfs

from urllib import quote
from ConfigParser import ConfigParser


class AssociationManager:
	"""Class that provides 'Open With' menu"""

	executable_types = (
					'application/x-executable',
					'application/x-shellscript',
				)

	def __init__(self):
		self._config_section = 'Desktop Entry'
		self._application_config_path = '/usr/share/applications'
		self._user_path = os.path.expanduser('~/.local/share/applications')
		
	def get_mime_type(self, path):
		"""Get mime type for specified path"""
		return gnomevfs.get_mime_type(path)
	
	def get_mime_description(self, mime_type):
		"""Get description from mime type"""
		return gnomevfs.mime_get_description(mime_type)

	def get_all_configs(self):
		"""Return list of all applications"""
		system_list = os.listdir(self._application_config_path)
		system_list = map(lambda item: os.path.join(self._application_config_path, item), system_list)
		
		user_list = os.listdir(self._user_path)
		user_list = map(lambda item: os.path.join(self._user_path, item), user_list)
		
		result = []
		result.extend(system_list)
		result.extend(user_list)
		
		result = filter(lambda item: os.path.splitext(item)[1] == '.desktop', result)
		
		return result

	def get_application_list_for_type(self, mime_type):
		"""Get list of associated programs for specified type"""
		return gnomevfs.mime_get_all_applications(mime_type)

	def get_default_application_for_type(self, mime_type):
		"""Get default application for specified type"""
		return gnomevfs.mime_get_default_application(mime_type)

	def get_association_config(self, file_name):
		"""Return dictionary containing all the options"""
		result = None
		config = ConfigParser()

		if os.path.exists(os.path.join(self._user_path, file_name)):
			config.read(os.path.join(self._user_path, file_name))

		elif os.path.exists(os.path.join(self._application_config_path, file_name)):
			config.read(os.path.join(self._application_config_path, file_name))

		if config.has_section(self._config_section):
			result = dict(config.items(self._config_section))

		return result

	def open_file(self, selection, config_file=None, exec_command=None):
		"""Open filename using config file or specified execute command"""
		if config_file is not None:
			# get command from config file
			config = self.get_association_config(config_file)
			
			if config is None \
			and not config.has_option(self._config_section, 'exec'): 
				return
	
			command = config['exec']
			
		elif exec_command is not None:
			# use specified command
			command = exec_command
		
		else:
			# raise exception, we need at least one argument
			raise AttributeError('We need either config_file or command to be specified!')
		
		# we modify exec_string and use 
		# command for testing to avoid problem
		# with Unicode characters in URI
		exec_string = command

		if selection is not None:
			# prepare lists
			normal_list = ["'{0}'".format(item) for item in selection]
			uri_list = ['file://{0}'.format(quote(item.encode('utf-8'))) for item in selection]
			dir_list = ["'{0}'".format(os.path.dirname(item) for item in selection)]
			names_list = ["'{0}'".format(os.path.basename(item) for item in selection)]

			# prepare single item selection
			if '%f' in command:
				exec_string = exec_string.replace('%f', "'{0}'".format(selection[0]))

			if '%u' in command:
				exec_string = exec_string.replace('%u', 'file://{0}'.format(quote(selection[0].encode('utf-8'))))

			if '%d' in command:
				exec_string = exec_string.replace('%d', "'{0}'".format(os.path.dirname(selection[0])))

			if '%n' in command:
				exec_string = exec_string.replace('%n', "'{0}'".format(os.path.basename(selection[0])))

			# prepare multiple selection
			if '%F' in command:
				exec_string = exec_string.replace('%F', ' '.join(normal_list))

			if '%U' in command:
				exec_string = exec_string.replace('%U', ' '.join(uri_list))

			if '%D' in command:
				exec_string = exec_string.replace('%D', ' '.join(dir_list))

			if '%N' in command:
				exec_string = exec_string.replace('%N', ' '.join(names_list))

			# open selected file(s)
			os.system('{0} &'.format(exec_string))

	def execute_file(self, path):
		"""Execute specified item"""
		mime_type = self.get_mime_type(path)
		is_executable = gnomevfs.is_executable_command_string(path)

		if mime_type in self.executable_types and is_executable:
			# file is executable type and has executable bit set
			os.system('{0} &'.format(path))

		else:
			# file does not have executable bit set, open with default application
			default_program = self.get_default_application_for_type(mime_type)
			config_file = default_program[0]

			self.open_file((path,), config_file)
