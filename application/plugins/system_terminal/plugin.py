import os
import user

from plugin_base.terminal import Terminal


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_class('system_terminal', _('System terminal'), SystemTerminal)


class SystemTerminal(Terminal):
	"""System terminal plugin"""

	def __init__(self, parent, notebook, path=None):
		Terminal.__init__(self, parent, notebook, path)

		# variable to store process id
		self._pid = None

		# make sure we open in a good path
		if self.path is None:
			self.path = user.home

		self._close_on_child_exit = True
		shell_command = os.environ['SHELL']

		# we need TERM environment variable set
		if not os.environ.has_key('TERM'):
			os.environ['TERM'] = 'xterm'
			os.environ['COLORTERM'] = 'gnome-terminal'

		# force shell to update terminal title
		if not os.environ.has_key('PROMPT_COMMAND'):
			os.environ['PROMPT_COMMAND'] = 'echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD}\007"'

		if self._vte_present:
			# fork default shell
			self._terminal.connect('child-exited', self.__child_exited)
			self._terminal.connect('status-line-changed', self._update_terminal_status)
			self._pid = self._terminal.fork_command(
									command=shell_command,
									directory=self.path
								)

			self._title_bar.set_title(_('Terminal'))
			self._title_bar.set_subtitle(shell_command)

		# change tab label text
		self._change_tab_text(_('Terminal'))

		self.show_all()

	def __child_exited(self, widget, data=None):
		"""Handle child process termination"""
		if self._close_on_child_exit:
			self._close_tab()

	def __update_path_from_pid(self):
		"""Update terminal path from child process"""
		if self._pid is not None and os.path.isdir('/proc/{0}'.format(self._pid)):
			self.path = os.readlink('/proc/{0}/cwd'.format(self._pid))

	def _recycle_terminal(self, widget, data=None):
		"""Recycle terminal"""
		if not self._vte_present: return

		# enable close on exit
		self._close_on_child_exit = True

		shell_command = os.environ['SHELL']
		self._terminal.reset(True, True)
		self._terminal.fork_command(
								command=shell_command,
								directory=self.path
							)

	def _close_tab(self, widget=None, data=None):
		"""Provide additional functionality"""
		if self._notebook.get_n_pages() == 1:
			DefaultList = self._parent.plugin_classes['file_list']
			self._parent.create_tab(self._notebook, DefaultList, self.path)

		Terminal._close_tab(self, widget, data)

	def _handle_tab_close(self):
		"""Clean up before closing tab"""
		Terminal._handle_tab_close(self)
		self.__update_path_from_pid()
