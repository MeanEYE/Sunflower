#!/usr/bin/env python

import os

from plugin_base.terminal import Terminal

class SystemTerminal(Terminal):
	"""System terminal plugin"""

	def __init__(self, parent, notebook, path=None):
		Terminal.__init__(self, parent, notebook)

		self.path = path
		shell_command = os.environ['SHELL']
		
		# we need TERM environment variable set
		if 'TERM' not in os.environ:
			os.environ['TERM'] = 'xterm'
			os.environ['COLORTERM'] = 'gnome-terminal'

		if self._vte_present:
			self._terminal.connect('child-exited', self._close_tab)
			self._terminal.connect('status-line-changed', self._update_terminal_status)
			self._terminal.fork_command(
									command=shell_command,
									directory=self.path
								)

		self._change_tab_text('Terminal')

		self.show_all()

	def _update_terminal_status(self, widget, data=None):
		"""Update status bar text with terminal data"""
		self.update_status(self._terminal.get_status_line())

	def _recycle_terminal(self, widget, data=None):
		"""Recycle terminal"""
		if not self._vte_present: return
		
		shell_command = os.environ['SHELL']
		self._terminal.reset(True, True)
		self._terminal.fork_command(
								command=shell_command,
								directory=self.path
							)

