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
		self._ubuntu_coloring = parent.options.getboolean('main', 'ubuntu_coloring')

		self._parent = parent  # parent is stored locally for later use
		self._notebook = notebook

		self.set_border_width(1)
		self.set_spacing(1)

		# create tab label
		self._tab_label = gtk.Label('')
		self._tab_label.set_max_width_chars(20)
		self._tab_label.set_ellipsize(pango.ELLIPSIZE_END)

		# create gui
		self._top_panel = gtk.EventBox()

		# top panel
		self._top_hbox = gtk.HBox(False, 1)
		self._top_hbox.set_border_width(3)
		self._top_panel.add(self._top_hbox)

		# top folder icon as default
		self._icon = gtk.Image()

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
		vbox = gtk.VBox(False, 1)

		self._title_label = gtk.Label()
		self._title_label.set_alignment(0, 0.5)
		self._title_label.set_use_markup(True)
		self._title_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)

		font = pango.FontDescription('8')
		self._subtitle_label = gtk.Label()
		self._subtitle_label.set_alignment(0, 0.5)
		self._subtitle_label.set_use_markup(False)
		self._subtitle_label.modify_font(font)

		# pack interface
		vbox.pack_start(self._title_label, True, True, 0)
		vbox.pack_start(self._subtitle_label, False, False, 0)

		self._top_hbox.pack_start(self._icon, False, False, 0)
		self._top_hbox.pack_start(vbox, True, True, 3)

		self.pack_start(self._top_panel, False, False, 0)
		self.pack_end(status_bar, False, False, 0)

	def _change_title_text(self, text):
		"""Change title label text"""
		self._title_label.set_text(text)

	def _change_tab_text(self, text):
		"""Change tab text"""
		self._tab_label.set_text(text)

	def _connect_main_object(self, object_):
		"""Create focus chain and connect basic events"""
		self._main_object = object_

		# connect events
		self._main_object.connect('focus-in-event', self._control_got_focus)
		self._main_object.connect('focus-out-event', self._control_lost_focus)
		self._main_object.connect('key-press-event', self._handle_key_press)

		# set focus chain only to main object
		self.set_focus_chain((self._main_object,))

		# configure drag and drop support
		types = self._get_supported_drag_types()
		actions = self._get_supported_drag_actions()

		if actions is not None:
			# configure drag and drop features
			self._main_object.drag_dest_set(
										gtk.DEST_DEFAULT_ALL,
										types,
										actions
									)

			self._main_object.drag_source_set(
										gtk.gdk.BUTTON1_MASK,
										types,
										actions
									)

			# connect drag and drop events
			self._main_object.connect('drag-begin', self._drag_begin)
			self._main_object.connect('drag-motion', self._drag_motion)
			self._main_object.connect('drag-drop', self._drag_drop)
			self._main_object.connect('drag-data-received', self._drag_data_received)
			self._main_object.connect('drag-data-get', self._drag_data_get)
			self._main_object.connect('drag-data-delete', self._drag_data_delete)
			self._main_object.connect('drag-end', self._drag_end)

	def _drag_begin(self, widget, drag_context):
		"""Handle start of drag and drop operation"""
		return True

	def _drag_motion(self, widget, drag_context, x, y, timestamp):
		"""Handle dragging data over widget"""
		return True

	def _drag_drop(self, widget, drag_context, x, y, timestamp):
		"""Handle dropping data over widget"""
		return True

	def _drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
		"""Handle drop of data"""
		return True

	def _drag_data_get(self, widget, drag_context, selection_data, info, time):
		"""Respond to get-data request from destination widget"""
		return True

	def _drag_data_delete(self, widget, drag_context):
		"""Handle delete data after move operation"""
		return True

	def _drag_end(self, widget, drag_context, data=None):
		"""Handle the end of drag and drop operation"""
		return True

	def _get_supported_drag_types(self):
		"""Return list of supported data for drag'n'drop events"""
		return []

	def _get_supported_drag_actions(self):
		"""Return integer representing supported drag'n'drop actions

		Returning None will disable drag and drop functionality for
		specified main object.

		"""
		return None

	def _control_got_focus(self, widget, data=None):
		"""List focus in event"""
		self._change_top_panel_color(gtk.STATE_SELECTED)
		self._parent._set_active_object(self)

	def _control_lost_focus(self, widget, data=None):
		"""List focus out event"""
		self._change_top_panel_color(gtk.STATE_NORMAL)

	def _enable_object_block(self, widget=None, data=None):
		"""Block main object signals"""
		self._main_object.handler_block_by_func(self._control_lost_focus)

	def _disable_object_block(self, widget=None, data=None):
		"""Block main object signals"""
		self._main_object.handler_unblock_by_func(self._control_lost_focus)

	def _change_top_panel_color(self, state):
		"""Modify coloring of top panel"""
		normal_style = self._notebook.get_style().copy()
		ubuntu_style = self._parent._menu_item_tools.get_style().copy()
		
		if self._ubuntu_coloring and state is gtk.STATE_SELECTED:
			# ubuntu coloring style
			background_color = ubuntu_style.bg[gtk.STATE_NORMAL]
			text_color = ubuntu_style.text[gtk.STATE_NORMAL]
			
		else:
			# normal coloring style
			background_color = normal_style.bg[state]
			text_color = normal_style.text[state]

		self._top_panel.modify_bg(gtk.STATE_NORMAL, background_color)
		self._title_label.modify_fg(gtk.STATE_NORMAL, text_color)
		self._subtitle_label.modify_fg(gtk.STATE_NORMAL, text_color)
		
		return background_color, text_color

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

		# make letters lower case for easier handling
		if len(key_name) == 1: key_name = key_name.lower()

		if self._key_handlers.has_key(key_name) and self._key_handlers[key_name].has_key(state):
			# call specific key handler and set result
			result = self._key_handlers[key_name][state](widget, event)

		return result

	def apply_settings(self):
		"""Method called after settings were changed"""
		self._ubuntu_coloring = self._parent.options.getboolean('main', 'ubuntu_coloring')
		
		if self._parent._get_active_object() is self:
			self._change_top_panel_color(gtk.STATE_SELECTED)
		
		else:
			self._change_top_panel_color(gtk.STATE_NORMAL)

	def update_status(self, status):
		"""Change status text"""
		self._status_bar.set_markup(status)

	def update_notebook(self, notebook=None):
		"""Update notebook and/or page number"""
		if notebook is not None:
			self._notebook = notebook

