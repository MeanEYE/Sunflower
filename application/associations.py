import os
import gio
import gtk
import subprocess

from plugin_base.terminal import TerminalType
from gui.input_dialog import ApplicationSelectDialog
from collections import namedtuple
from common import is_x_app


ApplicationInfo = namedtuple(
				'ApplicationInfo',
				[
					'id',
					'name',
					'description',
					'executable',
					'command_line',
					'icon'
				])


class AssociationManager:
	"""Class that provides 'Open With' menu"""

	def __init__(self, application):
		self._application = application
	
	def __get_icon(self, icon_object):
		"""Get icon string from GIO icon object"""
		result = None
		
		if hasattr(icon_object, 'get_names'):
			result = icon_object.get_names()[0]
			
		elif hasattr(icon_object, 'get_file'):
			result = icon_object.get_file().get_path()
			
		return result

	def get_mime_type(self, path):
		"""Get mime type for specified path"""
		return gio.content_type_guess(path)
	
	def get_mime_description(self, mime_type):
		"""Get description from mime type"""
		return gio.content_type_get_description(mime_type)

	def get_all(self):
		"""Return list of all applications"""
		result = []
		
		for app_info in gio.app_info_get_all():
			application = ApplicationInfo(
									id = app_info.get_id(),
									name = app_info.get_name(),
									description = app_info.get_description(),
									executable = app_info.get_executable(),
									command_line = app_info.get_commandline(),
									icon = self.__get_icon(app_info.get_icon())
								)
			
			result.append(application)
			
		return result

	def get_application_list_for_type(self, mime_type):
		"""Get list of associated programs for specified type"""
		result = []
		
		for app_info in gio.app_info_get_all_for_type(mime_type):
			application = ApplicationInfo(
									id = app_info.get_id(),
									name = app_info.get_name(),
									description = app_info.get_description(),
									executable = app_info.get_executable(),
									command_line = app_info.get_commandline(),
									icon = self.__get_icon(app_info.get_icon())
								)
			
			result.append(application)
			
		return result

	def get_default_application_for_type(self, mime_type):
		"""Get default application for specified type"""
		app_info = gio.app_info_get_default_for_type(mime_type, must_support_uris=False)
		
		if app_info is not None:
			# create application container
			application = ApplicationInfo(
									id = app_info.get_id(),
									name = app_info.get_name(),
									description = app_info.get_description(),
									executable = app_info.get_executable(),
									command_line = app_info.get_commandline(),
									icon = self.__get_icon(app_info.get_icon())
								)
								
		else:
			# return None if there is no default application for this type
			application = None
					
		return application

	def open_file(self, selection, application_info=None, exec_command=None):
		"""Open filename using config file or specified execute command"""
		if application_info is not None:
			# get command from config file
			command = application_info.command_line
			
		elif exec_command is not None:
			# use specified command
			command = exec_command
		
		else:
			# raise exception, we need at least one argument
			raise AttributeError('Error opening file. We need command or application to be specified.')
		
		# we modify exec_string and use 
		# command for testing to avoid problem
		# with Unicode characters in URI
		exec_string = command

		if selection is not None:
			# prepare lists
			normal_list = ["'{0}'".format(item) for item in selection]
			uri_list = ["'{0}'".format(item) for item in selection]
			dir_list = ["'{0}'".format(os.path.dirname(item) for item in selection)]
			names_list = ["'{0}'".format(os.path.basename(item) for item in selection)]

			# prepare single item selection
			if '%f' in command:
				exec_string = exec_string.replace('%f', "'{0}'".format(selection[0]))

			if '%u' in command:
				exec_string = exec_string.replace('%u', "'{0}'".format(selection[0]))

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
		"""Execute specified item properly."""
		mime_type = self.get_mime_type(path)
		type_is_executable = gio.content_type_can_be_executable(mime_type)
		terminal_type = self._application.options.section('terminal').get('type')

		if type_is_executable:
			# file type is executable
			if is_x_app(path):
				subprocess.Popen(
							(path, '&'),
							cwd=os.path.dirname(path)
						)

			else:
				# command is console based, create terminal tab and fork it
				if terminal_type != TerminalType.EXTERNAL:
					active_object = self._application.get_active_object()
					tab = self._application.create_terminal_tab(active_object._notebook)

					tab._close_on_child_exit = True
					tab._terminal.fork_command(
									command=path,
									directory=os.path.dirname(path)
								)

		else:
			# file type is not executable, try to open with default associated application
			default_application = self.get_default_application_for_type(mime_type)

			if default_application is not None:
				self.open_file((path,), default_application)

			else:
				# no default application selected, show application selection dialog
				dialog = ApplicationSelectDialog(self._application, path)
				result = dialog.get_response()

				if result[0] == gtk.RESPONSE_OK:
					self.open_file(selection=(path,), exec_command=result[2])

