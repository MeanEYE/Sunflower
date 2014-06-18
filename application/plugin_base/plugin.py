# coding:utf-8 vi:noet:ts=4
import gtk
import getpass

from accelerator_group import AcceleratorGroup
from widgets.title_bar import TitleBar, Mode as TitleBarMode
from widgets.status_bar import StatusBar
from widgets.tab_label import TabLabel
from gui.preferences.display import StatusVisible


class PluginBase(gtk.VBox):
	"""Abstract plugin class

	This class provides basic and common GUI components for
	other plugins. Do NOT change this class!

	"""

	def __init__(self, parent, notebook, options):
		gtk.VBox.__init__(self, False, 3)

		self._parent = parent
		self._options = options
		self._notebook = notebook
		self._name = self.__class__.__name__

		# accelerator groups
		self._accelerator_groups = []
		self._configure_accelerators()

		# configure self
		self.set_border_width(2)

		# create tab label
		self._tab_label = TabLabel(self._parent, self)

		# title bar
		self._title_bar = TitleBar(self._parent, self)

		try:
			if getpass.getuser() == 'root':
				self._title_bar.set_mode(TitleBarMode.SUPER_USER)

		except:
			pass

		# status bar
		self._status_bar = StatusBar()

		# show status bar if needed
		if self._parent.options.get('show_status_bar') == StatusVisible.ALWAYS:
			self._status_bar.show()

		# lock options
		self._tab_lock = self._options.get('lock')

		if self.is_tab_locked():
			self.lock_tab()

		# pack interface
		self.pack_start(self._title_bar.get_container(), False, False, 0)
		self.pack_end(self._status_bar, False, False, 0)

	def _change_title_text(self, text):
		"""Change title label text"""
		self._title_bar.set_title(text)

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
										gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
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

	def _configure_accelerators(self):
		"""Configure accelerator group"""
		group = AcceleratorGroup(self._parent)
		keyval = gtk.gdk.keyval_from_name

		# configure accelerator group
		group.set_name('plugin_base')
		group.set_title(_('Plugin Base'))

		# add all methods to group
		group.add_method('focus_opposite_object', _('Focus opposite object'), self._parent.focus_opposite_object)
		group.add_method('next_tab', _('Next tab'), self._notebook_next_tab)
		group.add_method('previous_tab', _('Previous tab'), self._notebook_previous_tab)
		group.add_method('duplicate_tab', _('Duplicate tab'), self._duplicate_tab)
		group.add_method('close_tab', _('Close tab'), self._close_tab)
		group.add_method('focus_command_entry', _('Focus command entry'), self._focus_command_entry)
		group.add_method('focus_left_object', _('Focus left object'), self._focus_left_object)
		group.add_method('focus_right_object', _('Focus right object'), self._focus_right_object)

		# configure accelerators
		group.set_accelerator('focus_opposite_object', keyval('Tab'), 0)
		group.set_accelerator('next_tab', keyval('Tab'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('previous_tab', keyval('Tab'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
		group.set_accelerator('duplicate_tab', keyval('t'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('close_tab', keyval('w'), gtk.gdk.CONTROL_MASK)
		group.set_accelerator('focus_command_entry', keyval('Down'), gtk.gdk.MOD1_MASK)
		group.set_accelerator('focus_left_object', keyval('Left'), gtk.gdk.MOD1_MASK)
		group.set_accelerator('focus_right_object', keyval('Right'), gtk.gdk.MOD1_MASK)

		# add accelerator group to the list
		self._accelerator_groups.append(group)

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
		self._parent._set_active_object(self)

		# update states
		self.update_state(gtk.STATE_SELECTED)
		self._parent.get_opposite_object(self).update_state(gtk.STATE_NORMAL)

		# deactivate scheduled accelerators
		deactivated = self._parent.accelerator_manager.deactivate_scheduled_groups(self)

		# activate accelerators only if previous groups were deactivated
		if deactivated:
			for group in self._accelerator_groups:
				group.activate(self._parent)

	def _control_lost_focus(self, widget, data=None):
		"""List focus out event"""
		# schedule accelerator groups for deactivation
		self._parent.accelerator_manager.schedule_groups_for_deactivation(self._accelerator_groups, self)

	def _notebook_next_tab(self, widget, data=None):
		"""Go to next tab in parent Notebook"""
		self._parent.next_tab(self._notebook)
		return True

	def _notebook_previous_tab(self, widget, data=None):
		"""Go to previous tab in parent Notebook"""
		self._parent.previous_tab(self._notebook)
		return True

	def _focus_command_entry(self, widget=None, data=None):
		"""Focus command entry in main window"""
		self._parent.focus_command_entry()
		return True

	def _focus_left_object(self, widget=None, data=None):
		"""Focus left object"""
		self._parent.focus_left_object()
		return True

	def _focus_right_object(self, widget=None, data=None):
		"""Focus right object"""
		self._parent.focus_right_object()
		return True

	def _show_status_bar(self):
		"""Show status bar"""
		self._status_bar.show()

	def _hide_status_bar(self):
		"""Hide status bar"""
		self._status_bar.hide()

	def _duplicate_tab(self, widget, data=None):
		"""Creates new tab with same path"""
		self._parent.create_tab(self._notebook, self.__class__, self._options.copy())
		return True

	def _close_tab(self, widget=None, data=None):
		"""Ask parent to kill this tab"""
		self._parent.close_tab(self._notebook, self)
		return True

	def _move_tab(self, widget=None, data=None):
		"""Move tab to opposite panel"""
		notebook = self._parent.get_opposite_notebook(self._notebook)
		page_num = self._notebook.page_num(self)
		self._notebook.remove_page(page_num)
		notebook.append_page(self, self.get_tab_label())

	def _handle_key_press(self, widget, event):
		"""Handles key events in item list"""
		result = False

		special_keys = (
				gtk.keysyms.Tab,
				gtk.keysyms.Left,
				gtk.keysyms.Right,
				gtk.keysyms.Up,
				gtk.keysyms.Down
			)

		keyval = event.keyval
		state = event.state

		# pressing Shift + Tab gives ISO_Left_Tab
		# we need to override this behavior
		if keyval == gtk.keysyms.ISO_Left_Tab:
			keyval = gtk.keysyms.Tab

		if keyval in special_keys:
			for group in self._accelerator_groups:
				result = group.trigger_accelerator(keyval, state)

				if result:
					break

		return result

	def _handle_tab_close(self):
		"""Method called before tab is removed"""
		self._options.set('lock', self._tab_lock)
		for group in self._accelerator_groups:
			group.deactivate()

	def get_tab_label(self):
		"""Return tab label container"""
		return self._tab_label.get_container()

	def apply_settings(self):
		"""Method called after settings were changed"""
		self._title_bar.apply_settings()
		self._tab_label.apply_settings()

	def update_status(self, status):
		"""Change status text"""
		self._status_bar.set_text(status)

	def update_notebook(self, notebook=None):
		"""Update notebook and/or page number"""
		if notebook is not None:
			self._notebook = notebook

	def update_state(self, state):
		"""Update plugin state"""
		self._title_bar.set_state(state)

	def focus_main_object(self):
		"""Give focus to main object"""
		result = False

		if self._main_object is not None and hasattr(self._main_object, 'grab_focus'):
			self._main_object.grab_focus()
			result = True

		return result

	def lock_tab(self):
		"""Lock tab"""
		self._tab_lock = True
		self._tab_label.lock_tab()

	def unlock_tab(self):
		"""Unlock tab"""
		self._tab_lock = False
		self._tab_label.unlock_tab()

	def is_tab_locked(self):
		"""Return the status of lock"""
		return self._tab_lock
