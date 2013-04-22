import gtk
import gobject

from gui.input_dialog import InputDialog, PasswordDialog

try:
	import gnomekeyring as keyring

except:
	keyring = None


class EntryType:
	NO_TYPE = 0
	GENERIC = 1
	NETWORK = 2
	NOTE = 3


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

	if keyring is not None:
		KEYRING_TYPE = {
				EntryType.NO_TYPE: keyring.ITEM_NO_TYPE,
				EntryType.GENERIC: keyring.ITEM_GENERIC_SECRET,
				EntryType.NETWORK: keyring.ITEM_NETWORK_PASSWORD,
				EntryType.NOTE: keyring.ITEM_NOTE
			}

	def __init__(self, application):
		self._application = application
		self._info = None
		self._timeout = None

		# create status icon
		self._status_icon = gtk.Image()
		self._status_icon.show()

		# initialize keyring
		if self.is_available():
			self.__initialize_keyring()

	def __update_icon(self):
		"""Update icon based on keyring status"""
		is_locked = self.is_locked()
		icon_name = ('changes-allow-symbolic', 'changes-prevent-symbolic')[is_locked]
		icon_tooltip = (
					_('Keyring is unlocked'),
					_('Keyring is locked')
				)[is_locked]

		self._status_icon.set_from_icon_name(icon_name, gtk.ICON_SIZE_MENU)
		self._status_icon.set_tooltip_text(icon_tooltip)

	def __initialize_keyring(self):
		"""Initialize keyring"""
		if not self.keyring_exists():
			return

		# update keyring information
		self.__update_info()

	def __update_info(self):
		"""Update keyring status information"""
		self._info = keyring.get_info_sync(self.KEYRING_NAME)

		# update icon
		self.__update_icon()

	def __reset_timeout(self):
		"""Reset autolock timeout"""
		if self._timeout is not None:
			gobject.source_remove(self._timeout)
			self._timeout = None

		timeout = int(self.TIMEOUT * 60 * 1000)
		self._timeout = gobject.timeout_add(timeout, self.__lock_keyring)

	def __lock_keyring(self):
		"""Method called after specified amount of time has passed"""
		if self._timeout is not None:
			gobject.source_remove(self._timeout)
			self._timeout = None

		# lock keyring
		keyring.lock_sync(self.KEYRING_NAME)

		# update information about keyring
		self.__update_info()

	def __unlock_keyring(self):
		"""Unlock keyring and schedule automatic lock"""
		result = False

		dialog = InputDialog(self._application)
		dialog.set_title(_('Unlock keyring'))
		dialog.set_label(_('Please enter your keyring password:'))
		dialog.set_password()

		response = dialog.get_response()

		if response[0] == gtk.RESPONSE_OK:
			# try to unlock keyring
			keyring.unlock_sync(self.KEYRING_NAME, response[1])

			# update status information
			self.__update_info()

			if not self.is_locked():
				# set timeout for automatic locking
				self.__reset_timeout()
				result = True

		return result

	def __get_entry_info(self, entry):
		"""Get entry info object"""
		result = None

		for item_id in keyring.list_item_ids_sync(self.KEYRING_NAME):
			info = keyring.item_get_info_sync(self.KEYRING_NAME, item_id)

			if info.get_display_name() == entry:
				result = info
				break

		return result

	def __get_entry_id(self, entry):
		"""Get entry ID"""
		result = None

		for item_id in keyring.list_item_ids_sync(self.KEYRING_NAME):
			info = keyring.item_get_info_sync(self.KEYRING_NAME, item_id)

			if info.get_display_name() == entry:
				result = item_id
				break

		return result

	def lock_keyring(self):
		"""Lock keyring"""
		if self.keyring_exists():
			self.__lock_keyring()

	def keyring_exists(self):
		"""Check if keyring exists"""
		result = False

		if self.is_available():
			result = self.KEYRING_NAME in keyring.list_keyring_names_sync()

		return result

	def is_available(self):
		"""Return true if we are able to use Gnome keyring"""
		return keyring is not None and keyring.is_available()

	def is_locked(self):
		"""Return true if current keyring is locked"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		return self._info.get_is_locked()

	def rename_entry(self, entry, new_name):
		"""Rename entry"""
		if not self.keyring_exists():
			raise InvalidKeyringError('Keyring does not exist!')

		result = False

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return result

		# get entry information
		entry_id = self.__get_entry_id(entry)
		info = keyring.item_get_info_sync(self.KEYRING_NAME, entry_id)

		if info is not None:
			info.set_display_name(new_name)
			keyring.item_set_info_sync(self.KEYRING_NAME, entry_id, info)
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
		info = keyring.item_get_info_sync(self.KEYRING_NAME, entry_id)

		if info is not None:
			info.set_secret(secret)
			keyring.item_set_info_sync(self.KEYRING_NAME, entry_id, info)
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
		entry_id = self.__get_entry_id(entry)

		if entry_id is not None:
			keyring.item_delete_sync(self.KEYRING_NAME, entry_id)
			result = True

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
		for item_id in keyring.list_item_ids_sync(self.KEYRING_NAME):
			info = keyring.item_get_info_sync(self.KEYRING_NAME, item_id)
			result.append((item_id, info.get_display_name(), info.get_mtime()))

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
		item_info = self.__get_entry_info(entry)

		if item_info is not None:
			result = item_info.get_secret()

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
		item_info = self.__get_entry_info(entry)

		if item_info is not None:
			result = item_info.get_attributes()

		# reset autolock timeout
		self.__reset_timeout()

	def store_password(self, entry, password, attributes=None, entry_type=EntryType.GENERIC):
		"""Create new entry in keyring with specified data"""
		assert self.is_available()

		# create a new keyring if it doesn't exist
		if not self.KEYRING_NAME in keyring.list_keyring_names_sync():
			dialog = PasswordDialog(self._application)
			dialog.set_title(_('New keyring'))
			dialog.set_label(_(
						'We need to create a new keyring to safely '
						'store your passwords. Choose the password you '
						'want to use for it.'
					))

			response = dialog.get_response()

			if response[0] == gtk.RESPONSE_OK \
			and response[1] == response[2]:
				# create new keyring
				keyring.create_sync(self.KEYRING_NAME, response[1])
				self.__update_info()

			else:
				# wrong password
				raise KeyringCreateError('No keyring to store password to.')

		# if keyring is locked, try to unlock it
		if self.is_locked() and not self.__unlock_keyring():
			return False 

		# store password to existing keyring
		keyring.item_create_sync(
					self.KEYRING_NAME,
					self.KEYRING_TYPE[entry_type],
					entry,
					attributes if attributes is not None else {},
					password,
					True  # update if exists
				)

		return True
