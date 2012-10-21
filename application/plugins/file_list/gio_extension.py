import gtk
import gio

from dialogs import SambaCreate, SambaResult
from keyring import KeyringCreateError, EntryType
from plugin_base.mount_manager_extension import MountManagerExtension, ExtensionFeatures
from gui.input_dialog import InputDialog


class SambaColumn:
	NAME = 0
	SERVER = 1
	SHARE = 2
	DIRECTORY = 3
	DOMAIN = 4
	USERNAME = 5
	REQUIRES_LOGIN = 6
	URI = 7


class FTPColumn:
	NAME = 0
	SERVER = 1
	DIRECTORY = 2
	USERNAME = 3
	REQUIRES_LOGIN = 4
	URI = 7



class GioExtension(MountManagerExtension):
	"""Base class for all GIO based extensions"""
	features = set([ExtensionFeatures.SYSTEM_WIDE,])
	
	def __init__(self, parent, window):
		MountManagerExtension.__init__(self, parent, window)

	def __mount(self, uri, domain, username, password=None):
		"""Perform actual mounting operation with specified data"""
		self._show_spinner()

		def ask_password(operation, message, default_user, default_domain, flags): 
			# configure mount operationeration
			operation.set_domain(domain if domain != '' else default_domain)
			operation.set_username(username if username != '' else default_user)

			if password is not None:
				# set password to stored one
				operation.set_password(password)
				operation.reply(gio.MOUNT_OPERATION_HANDLED)

			else:
				# we don't have stored password, ask user to provide one
				with gtk.gdk.lock:
					dialog = InputDialog(self._application)
					dialog.set_title(_('Mount operation'))
					dialog.set_label(message)
					dialog.set_password()

					response = dialog.get_response()

					if response[0] == gtk.RESPONSE_OK:
						operation.set_password(response[1])
						operation.reply(gio.MOUNT_OPERATION_HANDLED)

		# create new mount operation object
		operation = gio.MountOperation()
		operation.connect('ask-password', ask_password)

		# perform mount
		path = gio.File(uri)
		path.mount_enclosing_volume(operation, self.__mount_callback)

	def __unmount(self, uri):
		"""Perform unmount on specified URI"""
		self._show_spinner()

		# get mount for specified URI
		try:
			mount = gio.File(uri).find_enclosing_mount()
			mount.unmount(self.__unmount_callback)

		except:
			pass

		finally:
			self._hide_spinner()

	def __mount_callback(self, path, result):
		"""Finish mounting"""
		try:
			path.mount_enclosing_volume_finish(result)

		except gio.Error as error:
			with gtk.gdk.lock:
				dialog = gtk.MessageDialog(
										self._parent.window,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										_(
											"Unable to mount:\n{0}\n\n{1}"
										).format(path.get_uri(), str(error))
									)
				dialog.run()
				dialog.destroy()

		finally:
			self._hide_spinner()

	def __unmount_callback(self, mount, result):
		"""Finish unmounting"""
		try:
			mount.unmount_finish(result)
		
		finally:
			self._hide_spinner()

	def _show_spinner(self):
		"""Show spinner"""
		if self._spinner is not None:
			self._spinner.show()
			self._spinner.start()

	def _hide_spinner(self):
		"""Hide spinner"""
		if self._spinner is not None:
			self._spinner.stop()
			self._spinner.hide()
	

class SambaExtension(GioExtension):
	"""Mount manager extension that provides editing and mounting
	of Samba shares through GIO backend.

	"""

	def __init__(self, parent, window):
		GioExtension.__init__(self, parent, window)

		# create user interface
		list_container = gtk.ScrolledWindow()
		list_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		list_container.set_shadow_type(gtk.SHADOW_IN)

		self._store = gtk.ListStore(str, str, str, str, str, str, bool, str) 
		self._list = gtk.TreeView(model=self._store)

		cell_name = gtk.CellRendererText()
		cell_uri = gtk.CellRendererText()

		col_name = gtk.TreeViewColumn(_('Name'), cell_name, text=SambaColumn.NAME)
		col_uri = gtk.TreeViewColumn(_('URI'), cell_uri, text=SambaColumn.URI)

		col_name.set_expand(True)

		self._list.append_column(col_name)
		self._list.append_column(col_uri)

		# create controls
		image_add = gtk.Image()
		image_add.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)

		button_add = gtk.Button()
		button_add.set_image(image_add)
		button_add.connect('clicked', self._add_mount)

		image_edit = gtk.Image()
		image_edit.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)

		button_edit = gtk.Button()
		button_edit.set_image(image_edit)
		button_edit.connect('clicked', self._edit_mount)

		image_delete = gtk.Image()
		image_delete.set_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_BUTTON)

		button_delete = gtk.Button()
		button_delete.set_image(image_delete)
		button_delete.connect('clicked', self._delete_mount)

		button_mount = gtk.Button(_('Mount'))
		button_mount.connect('clicked', self._mount_selected)

		button_unmount = gtk.Button(_('Unmount'))
		button_unmount.connect('clicked', self._unmount_selected)

		# use spinner if possible to denote busy operation
		if hasattr(gtk, 'Spinner'):
			self._spinner = gtk.Spinner()
			self._spinner.set_size_request(20, 20)
			self._spinner.set_property('no-show-all', True)

		else:
			self._spinner = None

		# pack user interface
		list_container.add(self._list)
		
		self._container.pack_start(list_container, True, True, 0)

		self._controls.pack_start(button_add, False, False, 0)
		self._controls.pack_start(button_edit, False, False, 0)
		self._controls.pack_start(button_delete, False, False, 0)

		if self._spinner is not None:
			self._controls.pack_start(self._spinner, False, False, 0)
		self._controls.pack_end(button_unmount, False, False, 0)
		self._controls.pack_end(button_mount, False, False, 0)

		# load entries from config file
		self.__populate_list()

	def __form_uri(self, server, share, directory):
		"""Form URI based on result from SambaCreate dialog"""
		scheme = 'smb'
		path = share

		# include directory
		if directory is not None and directory != '':
			path = '{0}/{1}'.format(path, directory)

		return '{0}://{1}/{2}/'.format(scheme, server, path)

	def __store_mount(self, params, uri):
		"""Store mount entry to configuration file and list store"""
		store_params = (
				params[SambaResult.NAME],
				params[SambaResult.SERVER],
				params[SambaResult.SHARE],
				params[SambaResult.DIRECTORY],
				params[SambaResult.DOMAIN],
				params[SambaResult.USERNAME],
				params[SambaResult.PASSWORD] != '',
				uri
			)
		self._store.append(store_params)

	def __populate_list(self):
		"""Populate list with entries from config"""
		entries = self._application.mount_options.get('smb')

		# no entries found, nothing to do here
		if entries is None:
			return

		# clear store
		self._store.clear()

		# add entries to the list store
		for entry in entries:
			self._store.append((
					entry['name'],
					entry['server'],
					entry['share'],
					entry['directory'],
					entry['domain'],
					entry['username'],
					entry['requires_login'],
					self.__form_uri(entry['server'], entry['share'], entry['directory'])
				))

	def __save_list(self):
		"""Save mounts from store to config file"""
		mount_options = self._application.mount_options

		# store configuration to options file
		if mount_options.has('smb'):
			entries = mount_options.get('smb')
			del entries[:]

		else:
			entries = []
			mount_options.set('smb', entries)

		# add items from the store
		for row in self._store:
			entries.append({
					'name': row[SambaColumn.NAME],
					'server': row[SambaColumn.SERVER],
					'share': row[SambaColumn.SHARE],
					'directory': row[SambaColumn.DIRECTORY],
					'domain': row[SambaColumn.DOMAIN],
					'username': row[SambaColumn.USERNAME],
					'requires_login': row[SambaColumn.REQUIRES_LOGIN] 
				})

	def _add_mount(self, widget, data=None):
		"""Present dialog to user for creating a new mount"""
		keyring_manager = self._parent._application.keyring_manager

		# create dialog and get response from user
		dialog = SambaCreate(self._window)
		dialog.set_keyring_available(keyring_manager.is_available())
		response = dialog.get_response()

		if response[0] == gtk.RESPONSE_OK:
			name = response[1][SambaResult.NAME]
			uri = self.__form_uri(
						response[1][SambaResult.SERVER],
						response[1][SambaResult.SHARE],
						response[1][SambaResult.DIRECTORY]
					)
			requires_login = response[1][SambaResult.PASSWORD] != ''

			if requires_login:
				if keyring_manager.is_available():
					try:
						# prepare atributes
						attributes = {
								'server': uri,
								'user': response[1][SambaResult.USERNAME]
							}
						# first, try to store password with keyring
						keyring_manager.store_password(
									name, 
									response[1][SambaResult.PASSWORD],
									attributes,
									entry_type=EntryType.NETWORK
								)

					except KeyringCreateError:
						# show error message
						print "Keyring create error, we need it to store this option"

					else:
						# store entry
						self.__store_mount(response[1], uri)

				else:
					# show error message
					print "Keyring is not available but it's needed!"

			else:
				# no login required, just store
				self.__store_mount(response[1], uri)

			# save mounts to config file
			self.__save_list()

	def _edit_mount(self, widget, data=None):
		"""Present dialog to user for editing existing mount"""
		keyring_manager = self._parent._application.keyring_manager
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			dialog = SambaCreate(self._window)
			old_name = item_list.get_value(selected_iter, SambaColumn.NAME)

			# set dialog parameters
			dialog.set_keyring_available(keyring_manager.is_available())
			dialog.set_name(old_name)
			dialog.set_server(item_list.get_value(selected_iter, SambaColumn.SERVER))
			dialog.set_share(item_list.get_value(selected_iter, SambaColumn.SHARE))
			dialog.set_directory(item_list.get_value(selected_iter, SambaColumn.DIRECTORY))
			dialog.set_domain(item_list.get_value(selected_iter, SambaColumn.DOMAIN))
			dialog.set_username(item_list.get_value(selected_iter, SambaColumn.USERNAME))

			# show editing dialog
			response = dialog.get_response()

			if response[0] == gtk.RESPONSE_OK:
				new_name = response[1][SambaResult.NAME]

				# modify list store
				item_list.set_value(selected_iter, SambaColumn.NAME, new_name)
				item_list.set_value(selected_iter, SambaColumn.SERVER, response[1][SambaResult.SERVER])
				item_list.set_value(selected_iter, SambaColumn.SHARE, response[1][SambaResult.SHARE])
				item_list.set_value(selected_iter, SambaColumn.DIRECTORY, response[1][SambaResult.DIRECTORY])
				item_list.set_value(selected_iter, SambaColumn.DOMAIN, response[1][SambaResult.DOMAIN])
				item_list.set_value(selected_iter, SambaColumn.USERNAME, response[1][SambaResult.USERNAME])

				# rename entry if needed
				if new_name != old_name:
					keyring_manager.rename_entry(old_name, new_name)

				# form uri
				uri = self.__form_uri(
							response[1][SambaResult.SERVER],
							response[1][SambaResult.SHARE],
							response[1][SambaResult.DIRECTORY]
						)

				item_list.set_value(selected_iter, SambaColumn.URI, uri)

				# save changes
				self.__save_list()

	def _delete_mount(self, widget, data=None):
		"""Remove dialog if user confirms"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()
		keyring_manager = self._parent._application.keyring_manager

		if selected_iter is not None:
			entry_name = item_list.get_value(selected_iter, SambaColumn.NAME)
			requires_login = item_list.get_value(selected_iter, SambaColumn.REQUIRES_LOGIN)

			# ask user to confirm removal
			dialog = gtk.MessageDialog(
									self._parent.window,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_QUESTION,
									gtk.BUTTONS_YES_NO,
									_(
										"You are about to remove '{0}'.\n"
										"Are you sure about this?"
									).format(entry_name)
								)
			result = dialog.run()
			dialog.destroy()

			# remove selected mount
			if result == gtk.RESPONSE_YES:
				item_list.remove(selected_iter)
				
				# save changes
				self.__save_list()

				# remove password from keyring manager
				if requires_login:
					keyring_manager.remove_entry(entry_name)

	def _mount_selected(self, widget, data=None):
		"""Mount selected item"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()
		keyring_manager = self._parent._application.keyring_manager

		if selected_iter is not None:
			server = item_list.get_value(selected_iter, SambaColumn.SERVER)
			share = item_list.get_value(selected_iter, SambaColumn.SHARE)
			directory = item_list.get_value(selected_iter, SambaColumn.DIRECTORY)
			domain = item_list.get_value(selected_iter, SambaColumn.DOMAIN)
			username = item_list.get_value(selected_iter, SambaColumn.USERNAME)
			password = None

			# form URI for mounting
			uri = self.__form_uri(server, share, directory)

			# get password if domain requires login
			if item_list.get_value(selected_iter, SambaColumn.REQUIRES_LOGIN):
				entry_name = item_list.get_value(selected_iter, SambaColumn.NAME)
				password = keyring_manager.get_password(entry_name)

			# mount specified URI
			self.__mount(uri, domain, username, password)

	def _unmount_selected(self, widget, data=None):
		"""Unmount selected item"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			server = item_list.get_value(selected_iter, SambaColumn.SERVER)
			share = item_list.get_value(selected_iter, SambaColumn.SHARE)
			directory = item_list.get_value(selected_iter, SambaColumn.DIRECTORY)

			# form URI for mounting
			uri = self.__form_uri(server, share, directory)

			# mount specified URI
			self.__unmount(uri)

	def unmount(self, uri):
		"""Handle unmounting specified URI"""
		pass

	def can_handle(self, uri):
		"""Returns boolean denoting if specified URI can be handled by this extension"""
		protocol, path = uri.split('://', 1)
		return protocol == 'smb'

	def get_information(self):
		"""Get extension information"""
		return 'samba', 'Samba'


class FTPExtension(GioExtension):
	"""Mount manager extension that provides editing and mounting
	of FTP (and SFTP) shares through GIO backend.

	"""

	def __init__(self, parent, window):
		GioExtension.__init__(self, parent, window)

		# create user interface
		list_container = gtk.ScrolledWindow()
		list_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		list_container.set_shadow_type(gtk.SHADOW_IN)

		self._store = gtk.ListStore(str, str, str, str, bool, str) 
		self._list = gtk.TreeView(model=self._store)

		cell_name = gtk.CellRendererText()
		cell_uri = gtk.CellRendererText()

		col_name = gtk.TreeViewColumn(_('Name'), cell_name, text=SambaColumn.NAME)
		col_uri = gtk.TreeViewColumn(_('URI'), cell_uri, text=SambaColumn.URI)

		col_name.set_expand(True)

		self._list.append_column(col_name)
		self._list.append_column(col_uri)

		# create controls
		image_add = gtk.Image()
		image_add.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)

		button_add = gtk.Button()
		button_add.set_image(image_add)
		button_add.connect('clicked', self._add_mount)

		image_edit = gtk.Image()
		image_edit.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)

		button_edit = gtk.Button()
		button_edit.set_image(image_edit)
		button_edit.connect('clicked', self._edit_mount)

		image_delete = gtk.Image()
		image_delete.set_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_BUTTON)

		button_delete = gtk.Button()
		button_delete.set_image(image_delete)
		button_delete.connect('clicked', self._delete_mount)

		button_mount = gtk.Button(_('Mount'))
		button_mount.connect('clicked', self._mount_selected)

		button_unmount = gtk.Button(_('Unmount'))
		button_unmount.connect('clicked', self._unmount_selected)

		# use spinner if possible to denote busy operation
		if hasattr(gtk, 'Spinner'):
			self._spinner = gtk.Spinner()
			self._spinner.set_size_request(20, 20)
			self._spinner.set_property('no-show-all', True)

		else:
			self._spinner = None

		# pack user interface
		list_container.add(self._list)
		
		self._container.pack_start(list_container, True, True, 0)

		self._controls.pack_start(button_add, False, False, 0)
		self._controls.pack_start(button_edit, False, False, 0)
		self._controls.pack_start(button_delete, False, False, 0)

		if self._spinner is not None:
			self._controls.pack_start(self._spinner, False, False, 0)
		self._controls.pack_end(button_unmount, False, False, 0)
		self._controls.pack_end(button_mount, False, False, 0)

		# load entries from config file
		self.__populate_list()

	def __populate_list(self):
		"""Populate list with stored mounts"""
		pass

	def __form_uri(self, server, username, directory):
		"""Form URI string from specified parameters"""
		pass

	def __store_mount(self, params, uri):
		"""Store mount to the list"""
		pass

	def __save_list(self):
		"""Save list to config file"""
		pass

	def _add_mount(self, widget, data=None):
		"""Show dialog for adding new FTP mount"""
		pass

	def _delete_mount(self, widget, data=None):
		"""Remove selected mount"""
		pass

	def _edit_mount(self, widget, data=None):
		"""Edit selected mount"""
		pass

	def _mount_selected(self, widget, data=None):
		"""Mount selected"""
		pass

	def _unmount_selected(self, widget, data=None):
		"""Unmount selected"""
		pass

	def get_information(self):
		"""Get extension information"""
		return 'folder-remote-ftp', 'FTP'
