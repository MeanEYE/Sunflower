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
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# create user interface
		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(self._container, 5)

		hbox_icon = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
		vbox_icon = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		icon = Gtk.Image()
		if Gtk.get_major_version() == 3:
			icon.set_from_icon_name('samba', Gtk.IconSize.DIALOG)

		else:
			icon.set_from_icon_name('samba')

		vbox_name = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_xalign(0)
		label_name.set_yalign(0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		vbox_server = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_server = Gtk.Label(label=_('Server:'))
		label_server.set_xalign(0)
		label_server.set_yalign(0.5)
		self._entry_server = Gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_share = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_directory = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_share = Gtk.Label(label=_('Share:'))
		label_share.set_xalign(0)
		label_share.set_yalign(0.5)
		label_directory = Gtk.Label(label=_('Directory:'))
		label_directory.set_xalign(0)
		label_directory.set_yalign(0.5)
		self._entry_share = Gtk.Entry()
		self._entry_directory = Gtk.Entry()

		self._entry_share.connect('activate', self._confirm_entry)
		self._entry_directory.connect('activate', self._confirm_entry)

		# access information
		hseparator2 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		vbox_domain = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_username = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_password = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_domain = Gtk.Label(label=_('Domain:'))
		label_username = Gtk.Label(label=_('Username:'))
		label_password = Gtk.Label(label=_('Password:'))

		label_domain.set_xalign(0)
		label_domain.set_yalign(0.5)
		label_username.set_xalign(0)
		label_username.set_yalign(0.5)
		label_password.set_xalign(0)
		label_password.set_yalign(0.5)

		self._entry_domain = Gtk.Entry()
		self._entry_username = Gtk.Entry()
		self._entry_password = Gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		self._entry_domain.connect('activate', self._confirm_entry)
		self._entry_username.connect('activate', self._confirm_entry)
		self._entry_password.connect('activate', self._confirm_entry)

		# create controls
		if Gtk.get_major_version() == 3:
			button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)

		else:
			button_save = Gtk.Button.new_with_label(_('Save'))
		button_save.connect('clicked', self._confirm_entry)
		if Gtk.get_major_version() == 3:
			button_save.set_can_default(True)

		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		# pack user interface
		if Gtk.get_major_version() == 3:
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

		else:
			vbox_domain.append(label_domain)
			vbox_domain.append(self._entry_domain)

			vbox_username.append(label_username)
			vbox_username.append(self._entry_username)

			vbox_password.append(label_password)
			vbox_password.append(self._entry_password)

			vbox_share.append(label_share)
			vbox_share.append(self._entry_share)

			vbox_directory.append(label_directory)
			vbox_directory.append(self._entry_directory)

			vbox_server.append(label_server)
			vbox_server.append(self._entry_server)

			vbox_name.append(label_name)
			vbox_name.append(self._entry_name)

			self._container.append(vbox_name)
			set_border_width(hseparator, 2)
			self._container.append(hseparator)
			self._container.append(vbox_server)
			self._container.append(vbox_share)
			self._container.append(vbox_directory)
			set_border_width(hseparator2, 2)
			self._container.append(hseparator2)
			self._container.append(vbox_domain)
			self._container.append(vbox_username)
			self._container.append(vbox_password)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		if Gtk.get_major_version() == 3:
			self._dialog.action_area.pack_end(button_save, False, False, 0)

			vbox_icon.pack_start(icon, False, False, 0)
			hbox_icon.pack_start(vbox_icon, True, True, 0)
			hbox_icon.pack_start(self._container, True, True, 0)

			self._dialog.vbox.pack_start(hbox_icon, True, True, 0)

		else:
			button_save.set_hexpand(True)
			button_save.set_halign(Gtk.Align.END)
			self._dialog.action_area.append(button_save)

			vbox_icon.append(icon)
			vbox_icon.set_hexpand(True)
			hbox_icon.append(vbox_icon)
			self._container.set_hexpand(True)
			hbox_icon.append(self._container)

			hbox_icon.set_vexpand(True)
			self._dialog.vbox.append(hbox_icon)
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() == '' \
		or self._entry_server.get_text() == '':
			# missing required fields
			dialog = Gtk.MessageDialog(
									transient_for=self._dialog,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.INFO,
									buttons=Gtk.ButtonsType.OK,
									text=_(
										'One or more required fields are empty. '
										'Please make sure you have entered name, '
										'server and share.'
									)
								)
			run_dialog(dialog)
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
		code = run_dialog(self._dialog)

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
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# create user interface
		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(self._container, 5)

		hbox_icon = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
		vbox_icon = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		icon = Gtk.Image()
		if Gtk.get_major_version() == 3:
			icon.set_from_icon_name('folder-remote-ftp', Gtk.IconSize.DIALOG)

		else:
			icon.set_from_icon_name('folder-remote-ftp')

		vbox_name = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_xalign(0)
		label_name.set_yalign(0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		vbox_server = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_server = Gtk.Label(label=_('Server:'))
		label_server.set_xalign(0)
		label_server.set_yalign(0.5)
		self._entry_server = Gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_directory = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_directory = Gtk.Label(label=_('Directory:'))
		label_directory.set_xalign(0)
		label_directory.set_yalign(0.5)
		self._entry_share = Gtk.Entry()
		self._entry_directory = Gtk.Entry()

		self._entry_share.connect('activate', self._confirm_entry)
		self._entry_directory.connect('activate', self._confirm_entry)

		# access information
		hseparator2 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		vbox_username = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_password = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_username = Gtk.Label(label=_('Username:'))
		label_password = Gtk.Label(label=_('Password:'))

		label_username.set_xalign(0)
		label_username.set_yalign(0.5)
		label_password.set_xalign(0)
		label_password.set_yalign(0.5)

		self._entry_username = Gtk.Entry()
		self._entry_password = Gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		self._entry_username.connect('activate', self._confirm_entry)
		self._entry_password.connect('activate', self._confirm_entry)

		# create controls
		if Gtk.get_major_version() == 3:
			button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)

		else:
			button_save = Gtk.Button.new_with_label(_('Save'))
		button_save.connect('clicked', self._confirm_entry)
		if Gtk.get_major_version() == 3:
			button_save.set_can_default(True)

		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		# pack user interface
		if Gtk.get_major_version() == 3:
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

		else:
			vbox_username.append(label_username)
			vbox_username.append(self._entry_username)

			vbox_password.append(label_password)
			vbox_password.append(self._entry_password)

			vbox_directory.append(label_directory)
			vbox_directory.append(self._entry_directory)

			vbox_server.append(label_server)
			vbox_server.append(self._entry_server)

			vbox_name.append(label_name)
			vbox_name.append(self._entry_name)

			self._container.append(vbox_name)
			set_border_width(hseparator, 2)
			self._container.append(hseparator)
			self._container.append(vbox_server)
			self._container.append(vbox_directory)
			set_border_width(hseparator2, 2)
			self._container.append(hseparator2)
			self._container.append(vbox_username)
			self._container.append(vbox_password)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		if Gtk.get_major_version() == 3:
			self._dialog.action_area.pack_end(button_save, False, False, 0)

			vbox_icon.pack_start(icon, False, False, 0)
			hbox_icon.pack_start(vbox_icon, True, True, 0)
			hbox_icon.pack_start(self._container, True, True, 0)

			self._dialog.vbox.pack_start(hbox_icon, True, True, 0)

		else:
			button_save.set_hexpand(True)
			button_save.set_halign(Gtk.Align.END)
			self._dialog.action_area.append(button_save)

			vbox_icon.append(icon)
			vbox_icon.set_hexpand(True)
			hbox_icon.append(vbox_icon)
			self._container.set_hexpand(True)
			hbox_icon.append(self._container)

			hbox_icon.set_vexpand(True)
			self._dialog.vbox.append(hbox_icon)
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() == '' \
		or self._entry_server.get_text() == '':
			# missing required fields
			dialog = Gtk.MessageDialog(
									transient_for=self._dialog,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.INFO,
									buttons=Gtk.ButtonsType.OK,
									text=_(
										'One or more required fields is empty. '
										'Please make sure you have entered name and server.'
									)
								)
			run_dialog(dialog)
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
		code = run_dialog(self._dialog)

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
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# create user interface
		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(self._container, 5)

		hbox_icon = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
		vbox_icon = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		icon = Gtk.Image()
		if Gtk.get_major_version() == 3:
			icon.set_from_icon_name('folder-remote-ftp', Gtk.IconSize.DIALOG)

		else:
			icon.set_from_icon_name('folder-remote-ftp')

		vbox_name = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_xalign(0)
		label_name.set_yalign(0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		vbox_server = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_server = Gtk.Label(label=_('Server:'))
		label_server.set_xalign(0)
		label_server.set_yalign(0.5)
		self._entry_server = Gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		vbox_server_type = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_server_type = Gtk.Label(label=_('Server type:'))
		label_server_type.set_xalign(0)
		label_server_type.set_yalign(0.5)
		self._entry_server_type = Gtk.ComboBoxText()
		self._entry_server_type.append_text('http')
		self._entry_server_type.append_text('https')
		self._entry_server_type.set_active(0)

		vbox_directory = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_directory = Gtk.Label(label=_('Directory:'))
		label_directory.set_xalign(0)
		label_directory.set_yalign(0.5)
		self._entry_share = Gtk.Entry()
		self._entry_directory = Gtk.Entry()

		self._entry_share.connect('activate', self._confirm_entry)
		self._entry_directory.connect('activate', self._confirm_entry)

		# access information
		hseparator2 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		vbox_username = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_password = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_username = Gtk.Label(label=_('Username:'))
		label_password = Gtk.Label(label=_('Password:'))

		label_username.set_xalign(0)
		label_username.set_yalign(0.5)
		label_password.set_xalign(0)
		label_password.set_yalign(0.5)

		self._entry_username = Gtk.Entry()
		self._entry_password = Gtk.Entry()

		self._entry_password.set_property('caps-lock-warning', True)
		self._entry_password.set_visibility(False)

		self._entry_username.connect('activate', self._confirm_entry)
		self._entry_password.connect('activate', self._confirm_entry)

		# create controls
		if Gtk.get_major_version() == 3:
			button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)

		else:
			button_save = Gtk.Button.new_with_label(_('Save'))
		button_save.connect('clicked', self._confirm_entry)
		if Gtk.get_major_version() == 3:
			button_save.set_can_default(True)

		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		# pack user interface
		if Gtk.get_major_version() == 3:
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

		else:
			vbox_username.append(label_username)
			vbox_username.append(self._entry_username)

			vbox_password.append(label_password)
			vbox_password.append(self._entry_password)

			vbox_directory.append(label_directory)
			vbox_directory.append(self._entry_directory)

			vbox_server_type.append(label_server_type)
			vbox_server_type.append(self._entry_server_type)

			vbox_server.append(label_server)
			vbox_server.append(self._entry_server)

			vbox_name.append(label_name)
			vbox_name.append(self._entry_name)

			self._container.append(vbox_name)
			set_border_width(hseparator, 2)
			self._container.append(hseparator)
			self._container.append(vbox_server)
			self._container.append(vbox_server_type)
			self._container.append(vbox_directory)
			set_border_width(hseparator2, 2)
			self._container.append(hseparator2)
			self._container.append(vbox_username)
			self._container.append(vbox_password)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		if Gtk.get_major_version() == 3:
			self._dialog.action_area.pack_end(button_save, False, False, 0)

			vbox_icon.pack_start(icon, False, False, 0)
			hbox_icon.pack_start(vbox_icon, True, True, 0)
			hbox_icon.pack_start(self._container, True, True, 0)

			self._dialog.vbox.pack_start(hbox_icon, True, True, 0)

		else:
			button_save.set_hexpand(True)
			button_save.set_halign(Gtk.Align.END)
			self._dialog.action_area.append(button_save)

			vbox_icon.append(icon)
			vbox_icon.set_hexpand(True)
			hbox_icon.append(vbox_icon)
			self._container.set_hexpand(True)
			hbox_icon.append(self._container)

			hbox_icon.set_vexpand(True)
			self._dialog.vbox.append(hbox_icon)
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() == ''\
		or self._entry_server.get_text() == '':
			# missing required fields
			dialog = Gtk.MessageDialog(
				transient_for=self._dialog,
				destroy_with_parent=True,
				message_type=Gtk.MessageType.INFO,
				buttons=Gtk.ButtonsType.OK,
				text=_(
					'One or more required fields is empty. '
					'Please make sure you have entered name and server.'
				)
			)
			run_dialog(dialog)
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
		code = run_dialog(self._dialog)

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
