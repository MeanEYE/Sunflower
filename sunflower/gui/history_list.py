from __future__ import absolute_import

import os

from gi.repository import Gtk, Gdk, GObject
from sunflower.parameters import Parameters


class Column:
	NAME = 0
	PATH = 1
	TIMESTAMP = 2


class HistoryList(Gtk.Window):
	"""History list is used to display complete browsing history."""

	def __init__(self, parent, application):
		# create main window
		GObject.GObject.__init__(self)

		# store parameters locally, we'll need them later
		self._parent = parent
		self._application = application

		# configure dialog
		self.set_title(_('History'))
		self.set_size_request(500, 300)
		self.set_resizable(True)
		self.set_modal(True)
		self.set_transient_for(application)
		set_border_width(self, 7)

		# create UI
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)

		list_container = Gtk.ScrolledWindow()
		list_container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		if Gtk.get_major_version() == 3:
			list_container.set_shadow_type(Gtk.ShadowType.IN)

		else:
			list_container.set_has_frame(True)

		self._history = Gtk.ListStore(str, str)

		cell_name = Gtk.CellRendererText()
		cell_path = Gtk.CellRendererText()

		col_name = Gtk.TreeViewColumn(_('Name'), cell_name, text=Column.NAME)
		col_path = Gtk.TreeViewColumn(_('Path'), cell_path, text=Column.PATH)

		self._history_list = Gtk.TreeView(self._history)
		if Gtk.get_major_version() == 3:
			self._history_list.connect('key-press-event', self._handle_key_press)

		else:
			key_controller = Gtk.EventControllerKey.new()
			key_controller.connect('key-pressed', self._handle_key_pressed)
			self._history_list.add_controller(key_controller)
		self._history_list.append_column(col_name)
		self._history_list.append_column(col_path)

		# create controls
		hbox_controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

		button_close = Gtk.Button.new_with_label(_('Close'))
		button_close.connect('clicked', self._close)

		image_jump = Gtk.Image()
		if Gtk.get_major_version() == 3:
			image_jump.set_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.BUTTON)

		else:
			image_jump.set_from_icon_name('document-open-symbolic')
		button_jump = Gtk.Button()
		if Gtk.get_major_version() == 3:
			button_jump.set_image(image_jump)

		else:
			button_content = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
			button_content.append(image_jump)
			button_content.append(Gtk.Label.new(button_jump.get_label()))
			button_jump.set_child(button_content)
		button_jump.set_label(_('Open'))
		if Gtk.get_major_version() == 3:
			button_jump.set_can_default(True)
		button_jump.connect('clicked', self._change_path, False)

		image_new_tab = Gtk.Image()
		if Gtk.get_major_version() == 3:
			image_new_tab.set_from_icon_name('tab-new', Gtk.IconSize.BUTTON)

		else:
			image_new_tab.set_from_icon_name('tab-new')

		button_new_tab = Gtk.Button()
		if Gtk.get_major_version() == 3:
			button_new_tab.set_image(image_new_tab)

		else:
			button_content = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
			button_content.append(image_new_tab)
			button_content.append(Gtk.Label.new(button_new_tab.get_label()))
			button_new_tab.set_child(button_content)
		button_new_tab.set_label(_('Open in tab'))
		button_new_tab.set_tooltip_text(_('Open selected path in new tab'))
		button_new_tab.connect('clicked', self._change_path, True)

		button_opposite = Gtk.Button(label=_('Open in opposite list'))
		button_opposite.set_tooltip_text(_('Open selected path in opposite list'))
		button_opposite.connect('clicked', self._open_in_opposite_list)

		# pack UI
		if Gtk.get_major_version() == 3:
			list_container.add(self._history_list)

			hbox_controls.pack_end(button_close, False, False, 0)
			hbox_controls.pack_end(button_jump, False, False, 0)
			hbox_controls.pack_end(button_new_tab, False, False, 0)
			hbox_controls.pack_end(button_opposite, False, False, 0)

			vbox.pack_start(list_container, True, True, 0)
			vbox.pack_start(hbox_controls, False, False, 0)

			self.add(vbox)

		else:
			list_container.set_child(self._history_list)

			# end packed children are shown in reverse order of addition
			button_opposite.set_hexpand(True)
			button_opposite.set_halign(Gtk.Align.END)
			hbox_controls.append(button_opposite)
			hbox_controls.append(button_new_tab)
			hbox_controls.append(button_jump)
			hbox_controls.append(button_close)

			list_container.set_vexpand(True)
			vbox.append(list_container)
			vbox.append(hbox_controls)

			self.set_child(vbox)

		# populate history list
		self._populate_list()

		# show all elements
		if Gtk.get_major_version() == 3:
			self.show_all()

		else:
			self.show()

	def _close(self, widget=None, data=None):
		"""Handle clicking on close button"""
		self.destroy()

	def _change_path(self, widget=None, new_tab=False):
		"""Change to selected path"""
		selection = self._history_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# if selection is valid, change to selected path
		if selected_iter is not None:
			path = item_list.get_value(selected_iter, Column.PATH)

			if not new_tab:
				# change path
				self._parent._handle_history_click(path=path)

			else:
				# create a new tab
				options = Parameters()
				options.set('path', path)

				self._application.create_tab(
								self._parent._notebook,
								self._parent.__class__,
								options
							)

			# close dialog
			self._close()

	def _open_in_opposite_list(self, widget=None, data=None):
		"""Open selected item in opposite list"""
		selection = self._history_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# if selection is valid, change to selected path
		if selected_iter is not None:
			path = item_list.get_value(selected_iter, Column.PATH)

			# open in opposite list
			opposite_object = self._application.get_opposite_object(self._application.get_active_object())
			if hasattr(opposite_object, 'change_path'):
				opposite_object.change_path(path)

			# close dialog
			self._close()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in history list (GTK 3)"""
		return self._handle_keyval(event.keyval, event.get_state())

	def _handle_key_pressed(self, controller, keyval, keycode, state):
		"""Handle pressing keys in history list (GTK 4)"""
		return self._handle_keyval(keyval, state)

	def _handle_keyval(self, keyval, state):
		"""Handle pressing keys in history list"""
		result = False

		if keyval == Gdk.KEY_Return:
			if state & Gdk.ModifierType.CONTROL_MASK:
				# open path in new tab
				self._change_path(new_tab=True)

			else:
				# open path in existing tab
				self._change_path(new_tab=False)

			result = True

		elif keyval == Gdk.KEY_Escape:
			# close window on escape
			self._close()
			result = True

		return result

	def _populate_list(self):
		"""Populate history list"""
		target_iter = None
		current_path = self._parent._options.get('path')

		# add all entries to the list
		for path in self._parent.history:
			name = os.path.basename(path)
			if name == '':
				name = path

			new_iter = self._history.append((name, path))

			# assign row to be selected
			if target_iter is None or path == current_path:
				target_iter = new_iter

		# select row
		path = self._history.get_path(target_iter)
		self._history_list.set_cursor(path)
