#!/usr/bin/env python

import gtk
import pango

class PluginBase(gtk.VBox):
	"""Abstract plugin class

	This class provides basic and common GUI components for
	other plugins. Do NOT change this class!

	"""

	def __init__(self, parent, notebook, path=None):
		gtk.VBox.__init__(self, False, 0)

		self.path = path

		self._parent = parent  # parent is stored locally for later use
		self._notebook = notebook

		self.set_spacing(1)

		# create tab label
		self._tab_label = gtk.Label('')

		# create gui
		self._top_panel = gtk.EventBox()

		# top panel
		self._top_hbox = gtk.HBox(False, 1)
		self._top_hbox.set_border_width(3)
		self._top_panel.add(self._top_hbox)

		# top folder icon as default
		self._icon = gtk.Image()
		self._top_hbox.pack_start(self._icon, False, False, 0)

		# status bar
		status_bar = gtk.Frame()
		status_bar.set_shadow_type(gtk.SHADOW_IN)

		self._status_bar = gtk.Label()
		self._status_bar.set_alignment(0, 0.5)
		self._status_bar.set_use_markup(True)
		self._status_bar.set_ellipsize(pango.ELLIPSIZE_END)

		status_bar.add(self._status_bar)
		status_bar.set_border_width(1)

		# create title bar
		self._title_label = gtk.Label()
		self._title_label.set_alignment(0, 0.5)
		self._title_label.set_use_markup(True)
		self._title_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
		self._top_hbox.pack_start(self._title_label, True, True, 3)

		# pack interface
		self.pack_start(self._top_panel, False, False, 0)
		self.pack_end(status_bar, False, False, 0)

	def _change_title_text(self, text):
		"""Change title label text"""
		self._title_label.set_text(text)

	def _change_tab_text(self, text):
		"""Change tab text"""
		self._tab_label.set_text(text)

	def _connect_main_object(self, object):
		"""Create focus chain and connect basic events"""
		object.connect('focus-in-event', self._control_got_focus)
		object.connect('focus-out-event', self._control_lost_focus)
		object.connect('key-press-event', self._handle_key_press)

		self.set_focus_chain((object,))
		self._main_object = object

	def _control_got_focus(self, widget, data=None):
		"""List focus in event"""
		self._change_top_panel_color(gtk.STATE_SELECTED)
		self._parent._set_active_object(self)

	def _control_lost_focus(self, widget, data=None):
		"""List focus out event"""
		self._change_top_panel_color(gtk.STATE_NORMAL)

	def _change_top_panel_color(self, state):
		"""Modify coloring of top panel"""
		style = self._notebook.get_style().copy()
		background_color = style.bg[state]
		text_color = style.text[state]

		self._top_panel.modify_bg(gtk.STATE_NORMAL, background_color)
		self._title_label.modify_fg(gtk.STATE_NORMAL, text_color)

	def _notebook_next_tab(self, widget, data=None):
		"""Go to next tab in parent Notebook"""

		self._parent.next_tab(self._notebook)
		return True

	def _notebook_previous_tab(self, widget, data=None):
		"""Go to previous tab in parent Notebook"""

		self._parent.previous_tab(self._notebook)
		return True

	def _duplicate_tab(self, widget, data=None):
		"""Creates new tab with same path"""
		self._parent.create_tab(self._notebook, self.__class__, data)
		return True

	def _close_tab(self, widget, data=None):
		"""Ask parent to kill this tab"""
		self._parent.close_tab(self._notebook, self)
		return True

	def _handle_key_press(self, widget, event):
		"""Handles key events in item list"""

		result = False

		# if plugin has no key handlers defined
		if self._key_handlers is None:
			return result

		# generate state sting based on modifier state (control, alt, shift)
		state = "%d%d%d" % (
					bool(event.state & gtk.gdk.CONTROL_MASK),
					bool(event.state & gtk.gdk.MOD1_MASK),
					bool(event.state & gtk.gdk.SHIFT_MASK)
				)

		# retrieve human readable key representation
		key_name = gtk.gdk.keyval_name(event.keyval)

		if self._key_handlers.has_key(key_name) and self._key_handlers[key_name].has_key(state):
			# call specific key handler and set result
			result = self._key_handlers[key_name][state](widget, event)

		return result

	def apply_settings(self):
		"""Method called after settings were changed"""
		pass

	def update_status(self, status):
		"""Change status text"""
		self._status_bar.set_markup(status)

	def update_notebook(self, notebook=None):
		"""Update notebook and/or page number"""
		if notebook is not None:
			self._notebook = notebook

