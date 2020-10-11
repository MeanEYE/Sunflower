from __future__ import absolute_import

from gi.repository import Gtk, Gdk


class ErrorList:
	"""Operation error list.

	Error list is displayed only when errors occur during operation in
	silent mode.

	"""

	def __init__(self, parent):
		# create main window
		self._window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)

		# store parameters locally, we'll need them later
		self._parent = parent
		self._error_list = []

		# configure dialog
		self._window.set_title(_('Error list'))
		self._window.set_size_request(500, 400)
		self._window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self._window.set_resizable(True)
		self._window.set_skip_taskbar_hint(False)
		self._window.set_modal(False)
		self._window.set_transient_for(parent.get_window())
		self._window.set_border_width(7)

		self._window.connect('key-press-event', self._handle_key_press)

		# create user interface
		vbox = Gtk.VBox(False, 7)

		table = Gtk.Table(rows=4, columns=2, homogeneous=False)
		table.set_row_spacings(5)
		table.set_col_spacings(5)

		label_name = Gtk.Label(label=_('For:'))
		label_name.set_alignment(0, 0.5)

		self._entry_name = Gtk.Entry()
		self._entry_name.set_editable(False)

		label_source = Gtk.Label(label=_('Source:'))
		label_source.set_alignment(0, 0.5)

		self._entry_source = Gtk.Entry()
		self._entry_source.set_editable(False)

		label_destination = Gtk.Label(label=_('Destination:'))
		label_destination.set_alignment(0, 0.5)

		self._entry_destination = Gtk.Entry()
		self._entry_destination.set_editable(False)

		# create error list
		list_container = Gtk.ScrolledWindow()
		list_container.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		list_container.set_shadow_type(Gtk.ShadowType.IN)

		self._store = Gtk.ListStore(str)
		self._list = Gtk.TreeView(model=self._store)
		self._list.set_headers_visible(False)

		cell_error = Gtk.CellRendererText()
		col_error = Gtk.TreeViewColumn(None, cell_error, text=0)

		self._list.append_column(col_error)

		# create controls
		hbox = Gtk.HBox(False, 5)

		button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._close)

		# pack user interface
		list_container.add(self._list)

		table.attach(label_name, 0, 1, 0, 1, xoptions=Gtk.AttachOptions.SHRINK | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.SHRINK)
		table.attach(self._entry_name, 1, 2, 0, 1, yoptions=Gtk.AttachOptions.SHRINK)
		table.attach(label_source, 0, 1, 1, 2, xoptions=Gtk.AttachOptions.SHRINK | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.SHRINK)
		table.attach(self._entry_source, 1, 2, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)
		table.attach(label_destination, 0, 1, 2, 3, xoptions=Gtk.AttachOptions.SHRINK | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.SHRINK)
		table.attach(self._entry_destination, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.SHRINK)
		table.attach(list_container, 0, 2, 3, 4, xoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, yoptions=Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL)

		hbox.pack_end(button_close, False, False, 0)

		vbox.pack_start(table, True, True, 0)
		vbox.pack_start(hbox, False, False, 0)

		self._window.add(vbox)

		# show all items
		self._window.show_all()

	def _close(self, widget=None, data=None):
		"""Close error list window"""
		self._window.destroy()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys"""
		if event.keyval == Gdk.KEY_Escape:
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
