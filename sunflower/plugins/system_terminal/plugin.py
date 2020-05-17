from __future__ import absolute_import

import os

import shlex
import subprocess

from gi.repository import GLib, Vte

from sunflower.parameters import Parameters
from sunflower.plugin_base.terminal import Terminal, TerminalType


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_class('system_terminal', _('System terminal'), SystemTerminal)


class SystemTerminal(Terminal):
	"""System terminal plugin"""

	def __init__(self, parent, notebook, options):
		Terminal.__init__(self, parent, notebook, options)

		# variable to store process id
		self._pid = None

		# make sure we open in a good path
		self.path = self._options.get('path', os.path.expanduser('~'))
		self._close_on_child_exit = self._options.get('close_with_child', True)
		self._terminal_type = self._parent.options.section('terminal').get('type')

		if self._terminal_type == TerminalType.VTE:
			# we need TERM environment variable set
			if not 'TERM' in os.environ:
				os.environ['TERM'] = 'xterm-color'
				os.environ['COLORTERM'] = 'gnome-terminal'

			# fork default shell
			self._terminal.connect('child-exited', self.__child_exited)
			self._terminal.connect('realize', self.__terminal_realized)

		elif self._terminal_type == TerminalType.EXTERNAL:
			# connect signals
			self._terminal.connect('realize', self.__socket_realized)
			self._terminal.connect('plug-removed', self.__child_exited)

			# disable controls
			self._menu_button.set_sensitive(False)

		shell_command = self._options.get('shell_command', os.environ['SHELL'])

		# change titles
		self._change_tab_text(_('Terminal'))
		self._title_bar.set_title(_('Terminal'))
		self._title_bar.set_subtitle(shell_command)

		self.show_all()

	def __socket_realized(self, widget, data=None):
		"""Connect process when socket is realized"""
		socket_id = self._terminal.get_id()
		shell_command = self._options.get('shell_command', None)
		command_version = 'command' if shell_command is None else 'command2'
		arguments = self._options.get('arguments', [])

		# append additional parameter if we need to wait for command to finish
		if not self._options.get('close_with_child'):
			arguments.extend(('&&', 'read'))

		arguments_string = ' '.join(arguments)

		# parse command
		terminal_command = self._parent.options.section('terminal').get(command_version)
		terminal_command = shlex.split(terminal_command.format(socket_id, arguments_string))

		# execute process
		process = subprocess.Popen(terminal_command, cwd=self.path)
		self._pid = process.pid

	def __terminal_realized(self, widget, data=None):
		"""Event called once terminal emulator is realized"""
		shell_command = self._options.get('shell_command', os.environ['SHELL'])

		command = {
				'pty_flags': Vte.PtyFlags.DEFAULT,
				'working_directory': self.path,
				'argv': self._options.get('arguments', [shell_command]),
				'envv': [],
				'spawn_flags': GLib.SpawnFlags.DO_NOT_REAP_CHILD,
				'child_setup': None,
				'child_setup_data': None
			}

		# since VTE 0.38 fork_command_full has been renamed spawn_sync
		if hasattr(self._terminal, 'fork_command_full'):
			(result, self._pid) = self._terminal.fork_command_full(**command)
		else:
			(result, self._pid) = self._terminal.spawn_sync(**command)

	def __child_exited(self, widget, data=None):
		"""Handle child process termination"""
		already_closing = self._notebook.page_num(self) == -1

		if not already_closing and self._close_on_child_exit or self._terminal_type == TerminalType.EXTERNAL:
			self._close_tab()

		return True

	def __update_path_from_pid(self):
		"""Update terminal path from child process"""
		try:
			if self._pid is not None and os.path.isdir('/proc/{0}'.format(self._pid)):
				self.path = os.readlink('/proc/{0}/cwd'.format(self._pid))
				self._options.set('path', self.path)
		except:
			pass

	def _close_tab(self, widget=None, data=None):
		"""Provide additional functionality"""
		if self._notebook.get_n_pages() == 1:
			DefaultList = self._parent.plugin_classes['file_list']
			options = Parameters()
			options.set('path', self.path)

			self._parent.create_tab(self._notebook, DefaultList, options)

		return Terminal._close_tab(self, widget, data)

	def _handle_tab_close(self):
		"""Clean up before closing tab"""
		Terminal._handle_tab_close(self)
		self.__update_path_from_pid()

	def _create_file_list(self, widget=None, data=None):
		"""Create file list in parent notebook"""
		self.__update_path_from_pid()
		DefaultList = self._parent.plugin_classes['file_list']
		options = Parameters()
		options.set('path', self.path)
		self._parent.create_tab(self._notebook, DefaultList, options)
		return True
