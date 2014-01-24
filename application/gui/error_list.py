import gtk


class ErrorList:
	"""Operation error list.

	Error list is displayed only when errors occur during operation in
	silent mode.

	"""

	def __init__(self, parent):
		# create main window
		self._window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)

		# store parameters locally, we'll need them later
		self._parent = parent
		self._error_list = []

		# configure dialog
		self._window.set_title(_('Error list'))
		self._window.set_size_request(500, 400)
		self._window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self._window.set_resizable(True)
		self._window.set_skip_taskbar_hint(False)
		self._window.set_modal(False)
		self._window.set_transient_for(parent.get_window())
		self._window.set_wmclass('Sunflower', 'Sunflower')
		self._window.set_border_width(7)

		self._window.connect('key-press-event', self._handle_key_press)

		# create user interface
		vbox = gtk.VBox(False, 7)

		table = gtk.Table(rows=4, columns=2, homogeneous=False)
		table.set_row_spacings(5)
		table.set_col_spacings(5)

		label_name = gtk.Label(_('For:'))
		label_name.set_alignment(0, 0.5)

		self._entry_name = gtk.Entry()
		self._entry_name.set_editable(False)

		label_source = gtk.Label(_('Source:'))
		label_source.set_alignment(0, 0.5)

		self._entry_source = gtk.Entry()
		self._entry_source.set_editable(False)

		label_destination = gtk.Label(_('Destination:'))
		label_destination.set_alignment(0, 0.5)

		self._entry_destination = gtk.Entry()
		self._entry_destination.set_editable(False)

		# create error list
		list_container = gtk.ScrolledWindow()
		list_container.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		list_container.set_shadow_type(gtk.SHADOW_IN)

		self._store = gtk.ListStore(str)
		self._list = gtk.TreeView(model=self._store)
		self._list.set_headers_visible(False)

		cell_error = gtk.CellRendererText()
		col_error = gtk.TreeViewColumn(None, cell_error, text=0)

		self._list.append_column(col_error)

		# create controls
		hbox = gtk.HBox(False, 5)

		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._close)

		# pack user interface
		list_container.add(self._list)

		table.attach(label_name, 0, 1, 0, 1, xoptions=gtk.SHRINK | gtk.FILL, yoptions=gtk.SHRINK)
		table.attach(self._entry_name, 1, 2, 0, 1, yoptions=gtk.SHRINK)
		table.attach(label_source, 0, 1, 1, 2, xoptions=gtk.SHRINK | gtk.FILL, yoptions=gtk.SHRINK)
		table.attach(self._entry_source, 1, 2, 1, 2, yoptions=gtk.SHRINK)
		table.attach(label_destination, 0, 1, 2, 3, xoptions=gtk.SHRINK | gtk.FILL, yoptions=gtk.SHRINK)
		table.attach(self._entry_destination, 1, 2, 2, 3, yoptions=gtk.SHRINK)
		table.attach(list_container, 0, 2, 3, 4, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL)

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
		if event.keyval == gtk.keysyms.Escape:
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
