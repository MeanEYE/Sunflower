from __future__ import absolute_import

from gi.repository import Gtk, Gdk


class ErrorList:
	"""Operation error list.

	Error list is displayed only when errors occur during operation in
	silent mode.

	"""

	def __init__(self, parent):
		# create main window
		if Gtk.get_major_version() == 3:
			self._window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)

		else:
			self._window = Gtk.Window.new()

		# store parameters locally, we'll need them later
		self._parent = parent
		self._error_list = []

		# configure dialog
		self._window.set_title(_('Error list'))
		self._window.set_size_request(500, 400)
		self._window.set_resizable(True)
		self._window.set_modal(False)
		self._window.set_transient_for(parent.get_window())

		if Gtk.get_major_version() == 3:
			self._window.connect('key-press-event', self._handle_key_press)

		else:
			key_controller = Gtk.EventControllerKey.new()
			key_controller.connect('key-pressed', self._handle_key_pressed)
			self._window.add_controller(key_controller)
		# create user interface
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
		set_border_width(vbox, 7)

		table = Gtk.Grid.new()
		table.set_row_spacing(5)
		table.set_column_spacing(5)

		label_name = Gtk.Label(label=_('For:'))
		label_name.set_xalign(0)
		label_name.set_yalign(0.5)

		self._entry_name = Gtk.Entry()
		self._entry_name.set_editable(False)

		label_source = Gtk.Label(label=_('Source:'))
		label_source.set_xalign(0)
		label_source.set_yalign(0.5)

		self._entry_source = Gtk.Entry()
		self._entry_source.set_editable(False)

		label_destination = Gtk.Label(label=_('Destination:'))
		label_destination.set_xalign(0)
		label_destination.set_yalign(0.5)

		self._entry_destination = Gtk.Entry()
		self._entry_destination.set_editable(False)

		# create error list
		list_container = Gtk.ScrolledWindow()
		list_container.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		if Gtk.get_major_version() == 3:
			list_container.set_shadow_type(Gtk.ShadowType.IN)

		else:
			list_container.set_has_frame(True)

		self._store = Gtk.ListStore(str)
		self._list = Gtk.TreeView(model=self._store)
		self._list.set_headers_visible(False)

		cell_error = Gtk.CellRendererText()
		col_error = Gtk.TreeViewColumn(None, cell_error, text=0)

		self._list.append_column(col_error)

		# create controls
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

		button_close = Gtk.Button.new_with_label(_('Close'))
		button_close.connect('clicked', self._close)

		# pack user interface
		if Gtk.get_major_version() == 3:
			list_container.add(self._list)

		else:
			list_container.set_child(self._list)

		table.attach(label_name, 0, 0, 1, 1)
		table.attach(self._entry_name, 1, 0, 1, 1)
		table.attach(label_source, 0, 1, 1, 1)
		table.attach(self._entry_source, 1, 1, 1, 1)
		table.attach(label_destination, 0, 2, 1, 1)
		table.attach(self._entry_destination, 1, 2, 1, 1)
		list_container.set_hexpand(True)
		list_container.set_vexpand(True)
		table.attach(list_container, 0, 3, 2, 1)

		if Gtk.get_major_version() == 3:
			hbox.pack_end(button_close, False, False, 0)

			vbox.pack_start(table, True, True, 0)
			vbox.pack_start(hbox, False, False, 0)

			self._window.add(vbox)

		else:
			button_close.set_hexpand(True)
			button_close.set_halign(Gtk.Align.END)
			hbox.append(button_close)

			table.set_vexpand(True)
			vbox.append(table)
			vbox.append(hbox)

			self._window.set_child(vbox)

		# show all items
		if Gtk.get_major_version() == 3:
			self._window.show_all()

		else:
			self._window.show()

	def _close(self, widget=None, data=None):
		"""Close error list window"""
		self._window.destroy()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys (GTK 3)"""
		return self._handle_keyval(event.keyval, event.get_state())

	def _handle_key_pressed(self, controller, keyval, keycode, state):
		"""Handle pressing keys (GTK 4)"""
		return self._handle_keyval(keyval, state)

	def _handle_keyval(self, keyval, state):
		"""Handle pressing keys"""
		if keyval == Gdk.KEY_Escape:
			self._close()

	def set_operation_name(self, operation_name):
		"""Set operation name"""
		self._entry_name.set_text(operation_name)

	def set_source(self, source_path):
		"""Set source path"""
		self._entry_source.set_text(source_path)

	def set_destination(self, destination_path):
		"""Set destination path"""
		self._entry_destination.set_text(destination_path)

	def set_errors(self, error_list):
		"""Populate error list"""
		for error in error_list:
			self._store.append((error,))

	def show(self):
		"""Show error list window"""
		self._window.show()
