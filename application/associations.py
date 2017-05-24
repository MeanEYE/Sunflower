import os
import shlex
import urllib
import subprocess

from gi.repository import Gtk, Gio
from common import is_x_app
from collections import namedtuple
from parameters import Parameters
from plugin_base.provider import Mode
from plugin_base.terminal import TerminalType
from gui.input_dialog import ApplicationSelectDialog


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

	def __format_command_string(self, selection, command):
		"""Format command string"""
		# we modify exec_string and use
		# command for testing to avoid problem
		# with Unicode characters in URI
		exec_string = command

		if selection is not None:
			# prepare lists
			normal_list = ['"{0}"'.format(item.replace('"', '\\"')) for item in selection]
			uri_list = ['"{0}"'.format(item.replace('"', '\\"')) for item in selection]
			dir_list = ['"{0}"'.format(os.path.dirname(item).replace('"', '\\"') for item in selection)]
			names_list = ['"{0}"'.format(os.path.basename(item).replace('"', '\\"') for item in selection)]

			# prepare single item selection
			if '%f' in command:
				exec_string = exec_string.replace('%f', '"{0}"'.format(selection[0]))

			if '%u' in command:
				exec_string = exec_string.replace('%u', '"{0}"'.format(selection[0]))

			if '%d' in command:
				exec_string = exec_string.replace('%d', '"{0}"'.format(os.path.dirname(selection[0])))

			if '%n' in command:
				exec_string = exec_string.replace('%n', '"{0}"'.format(os.path.basename(selection[0])))

			# prepare multiple selection
			if '%F' in command:
				exec_string = exec_string.replace('%F', ' '.join(normal_list))

			if '%U' in command:
				exec_string = exec_string.replace('%U', ' '.join(uri_list))

			if '%D' in command:
				exec_string = exec_string.replace('%D', ' '.join(dir_list))

			if '%N' in command:
				exec_string = exec_string.replace('%N', ' '.join(names_list))

		return exec_string

	def is_mime_type_subset(self, mime_type, super_type):
		"""Check whether specified mime_type is a subset of super_type"""
		return Gio.content_type_is_a(mime_type, super_type)

	def is_mime_type_unknown(self, mime_type):
		"""Check if specified mime_type is unknown"""
		return Gio.content_type_is_unknown(mime_type)

	def get_sample_data(self, path, provider):
		"""Get sample data needed for content detection"""
		data = None
		file_handle = provider.get_file_handle(path, Mode.READ)

		if file_handle is not None:
			data = file_handle.read(128)
			file_handle.close()

		return data

	def get_mime_type(self, path=None, data=None):
		"""Get mime type for specified path"""
		result = None

		if path is not None:
			# detect content type based on file name
			result = Gio.content_type_guess(filename=path)[0]

		elif data is not None:
			# detect content type based on data
			result = Gio.content_type_guess(data=data)[0]

		return result

	def get_mime_description(self, mime_type):
		"""Get description from mime type"""
		return Gio.content_type_get_description(mime_type)

	def get_all(self):
		"""Return list of all applications"""
		result = []

		for app_info in Gio.app_info_get_all():
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

	def get_gio_application_by_id(self, id):
		"""Get GIO AppInfo object for specified Id"""
		result = None

		for app_info in Gio.app_info_get_all():
			if app_info.get_id() == id:
				result = app_info
				break

		return result

	def get_application_list_for_type(self, mime_type):
		"""Get list of associated programs for specified type"""
		result = []

		for app_info in Gio.app_info_get_all_for_type(mime_type):
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
		app_info = Gio.app_info_get_default_for_type(mime_type, must_support_uris=False)

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

	def set_default_application_for_type(self, mime_type, application_id):
		"""Set default application for specified type"""
		result = False

		for app_info in Gio.app_info_get_all():
			if application_id == app_info.get_id():
				app_info.set_as_default_for_type(mime_type)
				result = True
				break

		return result

	def open_file(self, selection, application_info=None, exec_command=None):
		"""Open filename using config file or specified execute command"""
		if application_info is not None:
			# launch application using GIO API
			application = self.get_gio_application_by_id(application_info.id)

			if application is not None:
				if application.supports_uris():
					selection = map(lambda path: 'file://{0}'.format(urllib.pathname2url(path)) if path.startswith('/') else path, selection)
					application.launch_uris(selection)
				else:
					application.launch([Gio.File.new_for_path(path) for path in selection])

		elif exec_command is not None:
			# use specified command
			command = exec_command

			selection = map(lambda item: item.replace('"', '\\"'), selection)
			exec_string = self.__format_command_string(selection, command)

			# open selected file(s)
			split_command = shlex.split(exec_string, posix=False)
			test_command = split_command[0] if len(split_command) > 1 else exec_string

			if is_x_app(test_command):
				subprocess.Popen(split_command, cwd=os.path.dirname(selection[0]))

			else:
				active_object = self._application.get_active_object()

				options = Parameters()
				options.set('close_with_child', True)
				options.set('shell_command', split_command[0])
				options.set('arguments', split_command)
				options.set('path', os.path.dirname(selection[0]))

				self._application.create_terminal_tab(active_object._notebook, options)

	def edit_file(self, selection):
		"""Edit selected filename"""
		section = self._application.options.section('editor')
		command = section.get('default_editor')

		exec_string = self.__format_command_string(selection, command)

		# open selected file(s)
		split_command = shlex.split(exec_string)
		test_command = split_command[0] if len(split_command) > 1 else exec_string

		if (section.get('terminal_command') and section.get('type') == 1) \
		or not is_x_app(test_command):
			active_object = self._application.get_active_object()

			options = Parameters()
			options.set('close_with_child', True)
			options.set('shell_command', split_command[0])
			options.set('arguments', split_command)
			options.set('path', os.path.dirname(selection[0]))

			self._application.create_terminal_tab(active_object._notebook, options)

		else:
			cwd = None
			if selection[0].startswith('/'):
				cwd = os.path.dirname(selection[0])
			subprocess.Popen(split_command, cwd=cwd)

	def execute_file(self, path, provider=None):
		"""Execute specified item properly."""
		mime_type = self.get_mime_type(path)
		terminal_type = self._application.options.section('terminal').get('type')
		should_execute = False

		if provider is not None and provider.is_local:
			# only allow local files which have execute
			# bit set to be executed locally
			should_execute = os.access(path, os.X_OK)

			# if we still don't know content type, try to guess
			if self.is_mime_type_unknown(mime_type):
				data = self.get_sample_data(path, provider)
				mime_type = self.get_mime_type(data=data)

		if Gio.content_type_can_be_executable(mime_type) and should_execute:
			# file type is executable
			if is_x_app(path):
				subprocess.Popen((path,), cwd=os.path.dirname(path))

			else:
				# command is console based, create terminal tab and fork it
				active_object = self._application.get_active_object()

				options = Parameters()
				options.set('close_with_child', False)
				options.set('shell_command', path)
				options.set('path', os.path.dirname(path))

				self._application.create_terminal_tab(active_object._notebook, options)

		else:
			# file type is not executable, try to open with default associated application
			default_application = self.get_default_application_for_type(mime_type)

			if default_application is not None:
				self.open_file((path,), default_application)

			else:
				# no default application selected, show application selection dialog
				dialog = ApplicationSelectDialog(self._application, path)
				result = dialog.get_response()

				if result[0] == Gtk.ResponseType.OK:
					self.open_file(selection=(path,), exec_command=result[2])

