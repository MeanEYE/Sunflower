from gi.repository import Gtk


class SambaResult:
	NAME = 0
	SERVER = 1
	SHARE = 2
	DIRECTORY = 3
	DOMAIN = 4
	USERNAME = 5
	PASSWORD = 6


class FtpResult:
	NAME = 0
	SERVER = 1
	DIRECTORY = 2
	USERNAME = 3
	PASSWORD = 4


class DavResult:
	NAME = 0
	SERVER = 1
	SERVER_TYPE = 2
	DIRECTORY = 3
	USERNAME = 4
	PASSWORD = 5


class SambaInputDialog:
	"""Dialog used for editing and creating Samba connections"""

	def __init__(self, parent):
		self._dialog = Gtk.Dialog(parent=parent)

		# configure dialog
		self.set_title(_('Create Samba mount'))
		self._dialog.set_default_size(340, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# create user interface
		self._container = Gtk.VBox(False, 5)
		self._container.set_border_width(5)

		hbox_icon = Gtk.HBox(False, 0)
		vbox_icon = Gtk.VBox(False, 0)
		icon = Gtk.Image()
		icon.set_from_icon_name('samba', Gtk.IconSize.DIALOG)

		vbox_name = Gtk.VBox(False, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_alignment(0, 0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = Gtk.HSeparator()

		vbox_server = Gtk.VBox(False, 0)

		label_server = Gtk.Label(label=_('Server:'))
		label_server.set_alignment(0, 0.5)
		self._entry_server = Gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_share = Gtk.VBox(False, 0)
		vbox_directory = Gtk.VBox(False, 0)

		label_share = Gtk.Label(label=_('Share:'))
		label_share.set_alignment(0, 0.5)
		label_directory = Gtk.Label(label=_('Directory:'))
		label_directory.set_alignment(0, 0.5)
		self._entry_share = Gtk.Entry()
		self._entry_directory = Gtk.Entry()

		self._entry_share.connect('activate', self._confirm_entry)
		self._entry_directory.connect('activate', self._confirm_entry)

		# access information
		hseparator2 = Gtk.HSeparator()

		vbox_domain = Gtk.VBox(False, 0)
		vbox_username = Gtk.VBox(False, 0)
		vbox_password = Gtk.VBox(False, 0)
		
		label_domain = Gtk.Label(label=_('Domain:'))
		label_username = Gtk.Label(label=_('Username:'))
		label_password = Gtk.Label(label=_('Password:'))

		label_domain.set_alignment(0, 0.5)
		label_username.set_alignment(0, 0.5)
		label_password.set_alignment(0, 0.5)

		self._entry_domain = Gtk.Entry()
		self._entry_username = Gtk.Entry()
		self._entry_password = Gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		self._entry_domain.connect('activate', self._confirm_entry)
		self._entry_username.connect('activate', self._confirm_entry)
		self._entry_password.connect('activate', self._confirm_entry)

		# create controls
		button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)
		button_save.connect('clicked', self._confirm_entry)
		button_save.set_can_default(True)

		button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

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

		vbox_name.pack_start(label_name, False, False, 0)
		vbox_name.pack_start(self._entry_name, False, False, 0)

		self._container.pack_start(vbox_name, False, False, 0)
		self._container.pack_start(hseparator, False, False, 2)
		self._container.pack_start(vbox_server, False, False, 0)
		self._container.pack_start(vbox_share, False, False, 0)
		self._container.pack_start(vbox_directory, False, False, 0)
		self._container.pack_start(hseparator2, False, False, 2)
		self._container.pack_start(vbox_domain, False, False, 0)
		self._container.pack_start(vbox_username, False, False, 0)
		self._container.pack_start(vbox_password, False, False, 0)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.action_area.pack_end(button_save, False, False, 0)

		vbox_icon.pack_start(icon, False, False, 0)
		hbox_icon.pack_start(vbox_icon, True, True, 0)
		hbox_icon.pack_start(self._container, True, True, 0)

		self._dialog.vbox.pack_start(hbox_icon, True, True, 0)
		self._dialog.show_all()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() == '' \
		or self._entry_server.get_text() == '':
			# missing required fields
			dialog = Gtk.MessageDialog(
									self._dialog,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.INFO,
									Gtk.ButtonsType.OK,
									_(
										'One or more required fields are empty. '
										'Please make sure you have entered name, '
										'server and share.'
									)
								)
			dialog.run()
			dialog.destroy()

		else:
			# return response
			self._dialog.response(Gtk.ResponseType.OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def set_keyring_available(self, available):
		"""Change sensitivity of some fields based on our ability
		to store passwords safely.

		"""
		self._entry_password.set_sensitive(available)

	def set_name(self, name):
		"""Set username for editing"""
		self._entry_name.set_text(name)

	def set_server(self, uri):
		"""Set server URI for editing"""
		self._entry_server.set_text(uri)

	def set_share(self, share):
		"""Set name of share for editing"""
		self._entry_share.set_text(share)

	def set_directory(self, directory):
		"""Set name of directory for editing"""
		self._entry_directory.set_text(directory)

	def set_domain(self, domain):
		"""Set name of domain for editing"""
		self._entry_domain.set_text(domain)

	def set_username(self, username):
		"""Set username for editing"""
		self._entry_username.set_text(username)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = self._dialog.run()

		result = (
				self._entry_name.get_text(),
				self._entry_server.get_text(),
				self._entry_share.get_text(),
				self._entry_directory.get_text(),
				self._entry_domain.get_text(),
				self._entry_username.get_text(),
				self._entry_password.get_text()
			)

		self._dialog.destroy()

		return code, result


class FtpInputDialog:
	"""Dialog used for editing and creating FTP connections"""

	def __init__(self, parent):
		self._dialog = Gtk.Dialog(parent=parent)

		# configure dialog
		self.set_title(_('Create FTP mount'))
		self._dialog.set_default_size(340, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# create user interface
		self._container = Gtk.VBox(False, 5)
		self._container.set_border_width(5)

		hbox_icon = Gtk.HBox(False, 0)
		vbox_icon = Gtk.VBox(False, 0)
		icon = Gtk.Image()
		icon.set_from_icon_name('folder-remote-ftp', Gtk.IconSize.DIALOG)

		vbox_name = Gtk.VBox(False, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_alignment(0, 0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = Gtk.HSeparator()

		vbox_server = Gtk.VBox(False, 0)

		label_server = Gtk.Label(label=_('Server:'))
		label_server.set_alignment(0, 0.5)
		self._entry_server = Gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_directory = Gtk.VBox(False, 0)

		label_directory = Gtk.Label(label=_('Directory:'))
		label_directory.set_alignment(0, 0.5)
		self._entry_share = Gtk.Entry()
		self._entry_directory = Gtk.Entry()

		self._entry_share.connect('activate', self._confirm_entry)
		self._entry_directory.connect('activate', self._confirm_entry)

		# access information
		hseparator2 = Gtk.HSeparator()

		vbox_username = Gtk.VBox(False, 0)
		vbox_password = Gtk.VBox(False, 0)
		
		label_username = Gtk.Label(label=_('Username:'))
		label_password = Gtk.Label(label=_('Password:'))

		label_username.set_alignment(0, 0.5)
		label_password.set_alignment(0, 0.5)

		self._entry_username = Gtk.Entry()
		self._entry_password = Gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		self._entry_username.connect('activate', self._confirm_entry)
		self._entry_password.connect('activate', self._confirm_entry)

		# create controls
		button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)
		button_save.connect('clicked', self._confirm_entry)
		button_save.set_can_default(True)

		button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		# pack user interface
		vbox_username.pack_start(label_username, False, False, 0)
		vbox_username.pack_start(self._entry_username, False, False, 0)

		vbox_password.pack_start(label_password, False, False, 0)
		vbox_password.pack_start(self._entry_password, False, False, 0)

		vbox_directory.pack_start(label_directory, False, False, 0)
		vbox_directory.pack_start(self._entry_directory, False, False, 0)

		vbox_server.pack_start(label_server, False, False, 0)
		vbox_server.pack_start(self._entry_server, False, False, 0)

		vbox_name.pack_start(label_name, False, False, 0)
		vbox_name.pack_start(self._entry_name, False, False, 0)

		self._container.pack_start(vbox_name, False, False, 0)
		self._container.pack_start(hseparator, False, False, 2)
		self._container.pack_start(vbox_server, False, False, 0)
		self._container.pack_start(vbox_directory, False, False, 0)
		self._container.pack_start(hseparator2, False, False, 2)
		self._container.pack_start(vbox_username, False, False, 0)
		self._container.pack_start(vbox_password, False, False, 0)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.action_area.pack_end(button_save, False, False, 0)

		vbox_icon.pack_start(icon, False, False, 0)
		hbox_icon.pack_start(vbox_icon, True, True, 0)
		hbox_icon.pack_start(self._container, True, True, 0)

		self._dialog.vbox.pack_start(hbox_icon, True, True, 0)
		self._dialog.show_all()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() == '' \
		or self._entry_server.get_text() == '':
			# missing required fields
			dialog = Gtk.MessageDialog(
									self._dialog,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.INFO,
									Gtk.ButtonsType.OK,
									_(
										'One or more required fields is empty. '
										'Please make sure you have entered name and server.'
									)
								)
			dialog.run()
			dialog.destroy()

		else:
			# return response
			self._dialog.response(Gtk.ResponseType.OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def set_keyring_available(self, available):
		"""Change sensitivity of some fields based on our ability
		to store passwords safely.

		"""
		self._entry_password.set_sensitive(available)

	def set_name(self, name):
		"""Set username for editing"""
		self._entry_name.set_text(name)

	def set_server(self, uri):
		"""Set server URI for editing"""
		self._entry_server.set_text(uri)

	def set_directory(self, directory):
		"""Set name of directory for editing"""
		self._entry_directory.set_text(directory)

	def set_username(self, username):
		"""Set username for editing"""
		self._entry_username.set_text(username)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = self._dialog.run()

		result = (
				self._entry_name.get_text(),
				self._entry_server.get_text(),
				self._entry_directory.get_text(),
				self._entry_username.get_text(),
				self._entry_password.get_text()
			)

		self._dialog.destroy()

		return code, result


class SftpInputDialog(FtpInputDialog):
	"""Dialog used for editing and creating SFTP connections"""

	def __init__(self, parent):
		FtpInputDialog.__init__(self, parent)
		self.set_title(_('Create SFTP mount'))


class DavInputDialog:
	"""Dialog used for editing and creating FTP connections"""

	def __init__(self, parent):
		self._dialog = Gtk.Dialog(parent=parent)

		# configure dialog
		self.set_title(_('Create WebDav mount'))
		self._dialog.set_default_size(340, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# create user interface
		self._container = Gtk.VBox(False, 5)
		self._container.set_border_width(5)

		hbox_icon = Gtk.HBox(False, 0)
		vbox_icon = Gtk.VBox(False, 0)
		icon = Gtk.Image()
		icon.set_from_icon_name('folder-remote-ftp', Gtk.IconSize.DIALOG)

		vbox_name = Gtk.VBox(False, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_alignment(0, 0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = Gtk.HSeparator()

		vbox_server = Gtk.VBox(False, 0)

		label_server = Gtk.Label(label=_('Server:'))
		label_server.set_alignment(0, 0.5)
		self._entry_server = Gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_server_type = Gtk.VBox(False, 0)

		label_server_type = Gtk.Label(label=_('Server type:'))
		label_server_type.set_alignment(0, 0.5)
		self._entry_server_type = Gtk.ComboBoxText()
		self._entry_server_type.append_text('http')
		self._entry_server_type.append_text('https')
		self._entry_server_type.set_active(0)

		vbox_directory = Gtk.VBox(False, 0)

		label_directory = Gtk.Label(label=_('Directory:'))
		label_directory.set_alignment(0, 0.5)
		self._entry_share = Gtk.Entry()
		self._entry_directory = Gtk.Entry()

		self._entry_share.connect('activate', self._confirm_entry)
		self._entry_directory.connect('activate', self._confirm_entry)

		# access information
		hseparator2 = Gtk.HSeparator()

		vbox_username = Gtk.VBox(False, 0)
		vbox_password = Gtk.VBox(False, 0)

		label_username = Gtk.Label(label=_('Username:'))
		label_password = Gtk.Label(label=_('Password:'))

		label_username.set_alignment(0, 0.5)
		label_password.set_alignment(0, 0.5)

		self._entry_username = Gtk.Entry()
		self._entry_password = Gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		self._entry_username.connect('activate', self._confirm_entry)
		self._entry_password.connect('activate', self._confirm_entry)

		# create controls
		button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)
		button_save.connect('clicked', self._confirm_entry)
		button_save.set_can_default(True)

		button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		# pack user interface
		vbox_username.pack_start(label_username, False, False, 0)
		vbox_username.pack_start(self._entry_username, False, False, 0)

		vbox_password.pack_start(label_password, False, False, 0)
		vbox_password.pack_start(self._entry_password, False, False, 0)

		vbox_directory.pack_start(label_directory, False, False, 0)
		vbox_directory.pack_start(self._entry_directory, False, False, 0)

		vbox_server_type.pack_start(label_server_type, False, False, 0)
		vbox_server_type.pack_start(self._entry_server_type, False, False, 0)

		vbox_server.pack_start(label_server, False, False, 0)
		vbox_server.pack_start(self._entry_server, False, False, 0)

		vbox_name.pack_start(label_name, False, False, 0)
		vbox_name.pack_start(self._entry_name, False, False, 0)

		self._container.pack_start(vbox_name, False, False, 0)
		self._container.pack_start(hseparator, False, False, 2)
		self._container.pack_start(vbox_server, False, False, 0)
		self._container.pack_start(vbox_server_type, False, False, 0)
		self._container.pack_start(vbox_directory, False, False, 0)
		self._container.pack_start(hseparator2, False, False, 2)
		self._container.pack_start(vbox_username, False, False, 0)
		self._container.pack_start(vbox_password, False, False, 0)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.action_area.pack_end(button_save, False, False, 0)

		vbox_icon.pack_start(icon, False, False, 0)
		hbox_icon.pack_start(vbox_icon, True, True, 0)
		hbox_icon.pack_start(self._container, True, True, 0)

		self._dialog.vbox.pack_start(hbox_icon, True, True, 0)
		self._dialog.show_all()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() == ''\
		or self._entry_server.get_text() == '':
			# missing required fields
			dialog = Gtk.MessageDialog(
				self._dialog,
				Gtk.DialogFlags.DESTROY_WITH_PARENT,
				Gtk.MessageType.INFO,
				Gtk.ButtonsType.OK,
				_(
					'One or more required fields is empty. '
					'Please make sure you have entered name and server.'
				)
			)
			dialog.run()
			dialog.destroy()

		else:
			# return response
			self._dialog.response(Gtk.ResponseType.OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def set_keyring_available(self, available):
		"""Change sensitivity of some fields based on our ability
		to store passwords safely.

		"""
		self._entry_password.set_sensitive(available)

	def set_name(self, name):
		"""Set username for editing"""
		self._entry_name.set_text(name)

	def set_server(self, uri):
		"""Set server URI for editing"""
		self._entry_server.set_text(uri)

	def set_server_type(self, type):
		"""Set server URI for editing"""
		self._entry_server_type.set_active(type)

	def set_directory(self, directory):
		"""Set name of directory for editing"""
		self._entry_directory.set_text(directory)

	def set_username(self, username):
		"""Set username for editing"""
		self._entry_username.set_text(username)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = self._dialog.run()

		result = (
			self._entry_name.get_text(),
			self._entry_server.get_text(),
			self._entry_server_type.get_active(),
			self._entry_directory.get_text(),
			self._entry_username.get_text(),
			self._entry_password.get_text()
		)

		self._dialog.destroy()

		return code, result
