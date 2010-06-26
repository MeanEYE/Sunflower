#!/usr/bin/env python

import os

from plugin_base.terminal import Terminal

class SystemTerminal(Terminal):
	"""System terminal plugin"""

	def __init__(self, parent, notebook, path=None):
		Terminal.__init__(self, parent, notebook)

		self.path = path
		shell_command = os.environ['SHELL']

		if self._terminal is not None:
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
		if self._terminal is None: return
		
		shell_command = os.environ['SHELL']
		self._terminal.reset(True, True)
		self._terminal.fork_command(
								command=shell_command,
								directory=self.path
							)

