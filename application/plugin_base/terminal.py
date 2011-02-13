#!/usr/bin/env python

import gtk

try:
	import vte
except:
	vte = None

from plugin import PluginBase

class Terminal(PluginBase):
	"""Base class for terminal based plugins

	This class will provide basic VTE GTK+ component wrapped in VBox.

	You are strongly encouraged to use predefined methods rather than
	defining your own.

	"""

	_vte_present = False

	def __init__(self, parent, notebook, path=None):
		PluginBase.__init__(self, parent, notebook, path)

		# global key event handlers with modifier switches (control, alt, shift)
		self._key_handlers = {
			'Tab': {
					'001': self._parent.focus_oposite_list,
					'100': self._notebook_next_tab,
					'101': self._notebook_previous_tab,
				},
			'w': {
					'100': self._close_tab,
				},
			't': {
					'100': self._duplicate_tab,
				},
			'z': {
					'100': self._create_terminal,
				},
			'F11': {
					'000': self._parent.toggle_fullscreen
				},
		}

		# change list icon
		self._icon.set_from_icon_name('terminal', gtk.ICON_SIZE_LARGE_TOOLBAR)

		# recycle button
		self._recycle_button = gtk.Button(u'\u267B')
		self._recycle_button.set_focus_on_click(False)
		self._recycle_button.set_tooltip_text('Recycle terminal')
		self._recycle_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._recycle_button.connect('clicked', self._recycle_terminal)

		self._top_hbox.pack_end(self._recycle_button, False, False, 0)

		if vte is not None:
			self._vte_present = True
			self._terminal = vte.Terminal()
			self._terminal.connect('window-title-changed', self._update_title)
		else:
			self._terminal = gtk.Label('Python VTE module is not installed on this system!')

		self._container = gtk.ScrolledWindow()
		self._container.set_shadow_type(gtk.SHADOW_IN)

		policy = (
				gtk.POLICY_NEVER,
				gtk.POLICY_AUTOMATIC
			)[self._parent.options.getboolean('main', 'terminal_scrollbars')]
		self._container.set_policy(policy, policy)

		self._container.add(self._terminal)

		self.pack_start(self._container, True, True, 0)

		self._connect_main_object(self._terminal)

	def _change_top_panel_color(self, state):
		"""Modify coloring of top panel"""
		PluginBase._change_top_panel_color(self, state)

		style = self._parent.get_style().copy()
		background_color = style.bg[state]
		text_color = style.text[state]

		self._recycle_button.modify_bg(gtk.STATE_NORMAL, background_color)
		self._recycle_button.child.modify_fg(gtk.STATE_NORMAL, text_color)

	def _update_title(self, widget, data=None):
		"""Update title with terminal window text"""
		self._change_title_text(self._terminal.get_window_title())
		return True

	def _update_terminal_status(self, widget, data=None):
		"""Update status bar text with terminal data"""
		self.update_status(self._terminal.get_status_line())

	def _recycle_terminal(self, widget, data=None):
		"""Recycle terminal"""
		pass

	def _create_terminal(self, widget, data=None):
		"""Create terminal tab in parent notebook"""
		self._parent.create_terminal_tab(self._notebook, self.path)
		return True

	def _duplicate_tab(self, widget, data=None):
		"""Creates new tab with same path"""
		PluginBase._duplicate_tab(self, None, self.path)
		return True

	def feed_terminal(self, text):
		"""Feed terminal process with specified text"""
		self._terminal.feed_child(text)

	def apply_settings(self):
		"""Apply terminal settings"""
		# button relief
		self._recycle_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		# apply terminal scrollbar policy
		policy = (
				gtk.POLICY_NEVER,
				gtk.POLICY_AUTOMATIC
			)[self._parent.options.getboolean('main', 'terminal_scrollbars')]
		self._container.set_policy(policy, policy)
