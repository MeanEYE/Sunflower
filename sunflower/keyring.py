from __future__ import absolute_import


try:
	import gi
	gi.require_version('Secret', '1')
	from gi.repository import Secret
	from gi.repository import GLib
except:
	Secret = None
else:
	from gi.repository import Gtk, GObject
	from sunflower.gui.input_dialog import InputDialog


class EntryType:
	GENERIC = 0
	NETWORK = 1
	NOTE = 2


class KeyringCreateError(Exception): pass
class PasswordStoreError(Exception): pass
class InvalidKeyringError(Exception): pass
class InvalidEntryError(Exception): pass


class KeyringManager:
	"""Keyring manager is used to securely store passwords. It also
	manages keyring availability and provides automatic locking.

	"""

	KEYRING_NAME = 'sunflower'
	TIMEOUT = 1

	if Secret is not None:
		KEYRING_SCHEMA = {
			EntryType.GENERIC: None,
			EntryType.NETWORK: Secret.SchemaType.COMPAT_NETWORK,
			EntryType.NOTE: Secret.SchemaType.NOTE
		}

	def __init__(self, application):
		# initialize keyring
		if not self.is_available():
			return

		self._application = application
		self._timeout = None

		# create status icon
		self._status_icon = Gtk.Image()
		self._status_icon.show()

		self.__initialize_keyring()

	def __update_icon(self):
		"""Update icon based on keyring status"""
		is_locked = self.is_locked()
		icon_name = ('changes-allow-symbolic', 'changes-prevent-symbolic')[is_locked]
		icon_tooltip = (
					_('Keyring is unlocked'),
					_('Keyring is locked')
				)[is_locked]

		self._status_icon.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
		self._status_icon.set_tooltip_text(icon_tooltip)

	def __initialize_keyring(self, collection=None):
		"""Initialize keyring"""
		if not self.keyring_exists():
			return

		if collection is None:
			try:
				collection = Secret.Collection.for_alias_sync(self.secret_service, self.KEYRING_NAME, Secret.CollectionFlags.NONE)

				if collection is not None:
					# update icon when locked status changes
					collection.connect('notify::locked', self.__update_icon)

					self.collection = collection
			except GLib.Error as error:
				print(error)
				return

	def __reset_timeout(self):
		"""Reset autolock timeout"""
		if self._timeout is not None:
			GObject.source_remove(self._timeout)
			self._timeout = None

		timeout = int(self.TIMEOUT * 60 * 1000)
		self._timeout = GObject.timeout_add(timeout, self.__lock_keyring)

	def __lock_keyring(self):
		"""Method called after specified amount of time has passed"""
		if self._timeout is not None:
			GObject.source_remove(self._timeout)
			self._timeout = None

		# lock keyring
		try:
			self.secret_service.lock_sync([self.collection])
		except GLib.Error as error:
			print(error)
			raise

	def __unlock_keyring(self):
		"""Unlock keyring and schedule automatic lock"""
		result = False

		# try to unlock keyring
		try:
			self.secret_service.unlock_sync([self.collection])

			if not self.is_locked():
				# set timeout for automatic locking
				self.__reset_timeout()
				result = True
		except GLib.Error as error:
			print(error)

		return result

	def __get_entry(self, entry):
		"""Get item object for given entry"""
		result = None

		for item in self.collection.get_items():
			if item.get_label() == entry:
				result = item
				break

		return result

	def lock_keyring(self):
		"""Lock keyring"""
		if self.keyring_exists():
			self.__lock_keyring()

	def keyring_exists(self):
		"""Check if keyring exists"""

		return self.collection is not None

	def is_available(self):
		"""Return true if we are able to use Gnome keyring"""
		if Secret is None:
			return False

		if self.secret_service is None:
			try:
				self.secret_service = Secret.Service.get_sync(Secret.ServiceFlags.LOAD_COLLECTIONS)
			except GLib.Error as error:
				print(error)
				return False

		return True

	def is_locked(self):
		"""Return true if current keyring is locked"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		return self.collection.get_locked()

	def rename_entry(self, entry, new_name):
		"""Rename entry"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = False

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# get entry information
		item = self.__get_entry(entry)

		if item is not None:
			try:
				item.set_label_sync(new_name)
			except GLib.Error as error:
				print(error)
				raise
			result = True

		return result

	def change_secret(self, entry_id, secret):
		"""Change secret for selected entry"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = False

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# get entry information
		item = self.__get_entry(entry)

		if item is not None:
			try:
				item.set_secret_sync(secret)
			except GLib.Error as error:
				print(error)
				raise
			result = True

		return result

	def remove_entry(self, entry):
		"""Remove entry from keyring"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = False

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# get entry id
		item = self.__get_entry(entry)

		if item is not None:
			try:
				item.delete_sync()
				result = True
			except GLib.Error as error:
				print(error)

		return result

	def get_entries(self):
		"""Return list of tuples containing entry names and description"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = []

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# populate result list
		for item in self.collection.get_items():
			result.append((item.get_object_path() item.get_label(), item.get_modified()))

		return result

	def get_password(self, entry):
		"""Return password for specified entry"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = None

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# get password
		item = self.__get_entry(entry)

		if item_info is not None:
			if item.get_secret() is None:
				try:
					item.load_secret_sync()
					result = item.get_secret()
				except GLib.Error as error:
					print(error)
					raise

		# reset autolock timeout
		self.__reset_timeout()

		return result

	def get_attributes(self, entry):
		"""Get attributes associated with specified entry"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = None

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# get password
		item = self.__get_entry(entry)

		if item not None:
			result = item.get_attributes()

		# reset autolock timeout
		self.__reset_timeout()

	def store_password(self, entry, password, attributes, entry_type=EntryType.GENERIC):
		"""Create new entry in keyring with specified data"""
		assert self.is_available()

		# create a new keyring if it doesn't exist
		if self.collection is None:
			try:
				# create new keyring
				collection = Secret.Collection.create_sync(self.secret_service, _('Sunflower file manager'), self.KEYRING_NAME, Secret.CollectionCreateFlags.NONE)
				self.__initialize_keyring(collection)
			except GLib.Error as error:
				print(error)
				raise KeyringCreateError(_('Error creating keyring.'))

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return False

		schema = self.KEYRING_SCHEMA[entry_type],

		try:
			# store password to existing keyring
			Secret.Item.create_sync(
				self.collection,
				schema,
				attributes,
				entry,
				password,
				Secret.ItemCreateFlags.REPLACE  # update if exists
			)

			return True
		except GLib.Error as error:
			print(error)
			return False
