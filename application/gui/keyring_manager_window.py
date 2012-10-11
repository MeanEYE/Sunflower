import gtk


class Column:
	NAME = 0
	DESCRIPTION = 1
	TYPE = 2


class KeyringManagerWindow:
	"""Keyring manager window is used to give user control over
	passwords stored in our own keyring.

	"""

	def __init__(self, application):
		self._application = application
		self._active_keyring = application.keyring_manager.KEYRING_NAME
		
		# create window
		self._window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		# configure window
		self._window.set_title(_('Keyring manager'))
		self._window.set_size_request(500, 300)
		self._window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self._window.set_skip_taskbar_hint(False)
		self._window.set_modal(False)
		self._window.set_wmclass('Sunflower', 'Sunflower')
		self._window.set_border_width(7)

		# create user interface
		vbox = gtk.VBox(homogeneous=False, spacing=5)
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._store = gtk.ListStore(str, str, int)
		self._list = gtk.TreeView(model=self._store)

		# create controls
		hbox = gtk.HBox(homogeneous=False, spacing=5)

		button_edit = gtk.Button(stock=gtk.STOCK_EDIT)
		button_edit.connect('clicked', self.__edit_selected)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self.__delete_selected)

		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)

		# pack components
		hbox.pack_start(button_edit, False, False, 0)
		hbox.pack_start(button_delete, False, False, 0)
		hbox.pack_end(button_close, False, False, 0)

		container.add(self._list)

		vbox.pack_start(container, True, True, 0)
		vbox.pack_start(hbox, False, False, 0)

		self._window.add(vbox)

		# populate list
		self.__populate_list()

		# show window
		self._window.show_all()

	def __populate_list(self, keyring_name=None):
		"""Populate list with items from specified keyring"""
		if keyring_name is not None:
			self._active_keyring = keyring_name

	def __delete_selected(self, widget, data=None):
		"""Delete selected entry in keyring"""
		pass

	def __edit_selected(self, widget, data=None):
		"""Edit selected entry in keyring"""
		pass
