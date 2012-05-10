import gtk


class SambaCreate:

	def __init__(self, parent):
		self._dialog = gtk.Dialog(parent=parent)

		# configure dialog
		self.set_title(_('Create Samba mount'))
		self._dialog.set_default_size(340, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(gtk.RESPONSE_OK)

		# create user interface
		self._container = gtk.VBox(False, 5)
		self._container.set_border_width(5)

		hbox_icon = gtk.HBox(False, 0)
		vbox_icon = gtk.VBox(False, 0)
		icon = gtk.Image()
		icon.set_from_icon_name('samba', gtk.ICON_SIZE_DIALOG)

		vbox_name = gtk.VBox(False, 0)

		label_name = gtk.Label(_('Name:'))
		label_name.set_alignment(0, 0.5)
		self._entry_name = gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = gtk.HSeparator()

		vbox_server = gtk.VBox(False, 0)
		vbox_port = gtk.VBox(False, 0)
		hbox_server = gtk.HBox(False, 5)

		label_server = gtk.Label(_('Server:'))
		label_server.set_alignment(0, 0.5)
		label_port = gtk.Label(_('Port:'))
		label_port.set_alignment(0, 0.5)

		self._entry_server = gtk.Entry()
		self._entry_port = gtk.SpinButton()
		self._entry_port.set_size_request(70, -1)

		label_server = gtk.Label(_('Server:'))
		label_server.set_alignment(0, 0.5)
		self._entry_server = gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_share = gtk.VBox(False, 0)
		vbox_directory = gtk.VBox(False, 0)

		label_share = gtk.Label(_('Share:'))
		label_share.set_alignment(0, 0.5)
		label_directory = gtk.Label(_('Directory:'))
		label_directory.set_alignment(0, 0.5)
		self._entry_share = gtk.Entry()
		self._entry_directory = gtk.Entry()

		# access information
		hseparator2 = gtk.HSeparator()

		vbox_domain = gtk.VBox(False, 0)
		vbox_username = gtk.VBox(False, 0)
		vbox_password = gtk.VBox(False, 0)
		
		label_domain = gtk.Label(_('Domain:'))
		label_username = gtk.Label(_('Username:'))
		label_password = gtk.Label(_('Password:'))

		label_domain.set_alignment(0, 0.5)
		label_username.set_alignment(0, 0.5)
		label_password.set_alignment(0, 0.5)

		self._entry_domain = gtk.Entry()
		self._entry_username = gtk.Entry()
		self._entry_password = gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		# create controls
		button_save = gtk.Button(stock=gtk.STOCK_SAVE)
		button_save.connect('clicked', self._confirm_entry)
		button_save.set_can_default(True)

		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

		# pack user interface
		vbox_domain.pack_start(label_domain, False, False, 0)
		vbox_domain.pack_start(self._entry_domain, False, False, 0)

		vbox_username.pack_start(label_username, False, False, 0)
		vbox_username.pack_start(self._entry_username, False, False, 0)

		vbox_password.pack_start(label_password, False, False, 0)
		vbox_password.pack_start(self._entry_password, False, False, 0)

		vbox_share.pack_start(label_share, False, False, 0)
		vbox_share.pack_start(self._entry_share, False, False, 0)

		vbox_directory.pack_start(label_directory, False, False, 0)
		vbox_directory.pack_start(self._entry_directory, False, False, 0)

		vbox_server.pack_start(label_server, False, False, 0)
		vbox_server.pack_start(self._entry_server, False, False, 0)

		vbox_port.pack_start(label_port, False, False, 0)
		vbox_port.pack_start(self._entry_port, False, False, 0)

		hbox_server.pack_start(vbox_server, True, True, 0)
		hbox_server.pack_start(vbox_port, False, False, 0)

		vbox_name.pack_start(label_name, False, False, 0)
		vbox_name.pack_start(self._entry_name, False, False, 0)

		self._container.pack_start(vbox_name, False, False, 0)
		self._container.pack_start(hseparator, False, False, 2)
		self._container.pack_start(hbox_server, False, False, 0)
		self._container.pack_start(vbox_share, False, False, 0)
		self._container.pack_start(vbox_directory, False, False, 0)
		self._container.pack_start(hseparator2, False, False, 2)
		self._container.pack_start(vbox_domain, False, False, 0)
		self._container.pack_start(vbox_username, False, False, 0)
		self._container.pack_start(vbox_password, False, False, 0)

		self._dialog.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)
		self._dialog.action_area.pack_end(button_save, False, False, 0)

		vbox_icon.pack_start(icon, False, False, 0)
		hbox_icon.pack_start(vbox_icon, True, True, 0)
		hbox_icon.pack_start(self._container, True, True, 0)

		self._dialog.vbox.pack_start(hbox_icon, True, True, 0)
		self._dialog.show_all()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		self._dialog.response(gtk.RESPONSE_OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = self._dialog.run()
		result = None

		self._dialog.destroy()

		return (code, result)
