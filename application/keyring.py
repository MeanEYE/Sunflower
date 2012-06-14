import gtk
import threading

from gui.input_dialog import PasswordDialog

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

	KEYRING_NAME = 'Sunflower'
	TIMEOUT = 10

	def __init__(self, application):
		self._application = application
		self._thread = None

	def __lock_keyring(self):
		"""Method called after specified amount of time has passed"""
		pass

	def __unlock_keyring(self):
		"""Unlock keyring and schedule automatic lock"""
		pass

	def is_available(self):
		"""Return true if we are able to use Gnome keyring"""
		return keyring is not None and keyring.is_available()

	def get_entries(self):
		"""Return list of tuples containing entry names and description"""
		assert self.is_available()

	def get_password(self, entry):
		"""Return password for specified entry"""
		assert self.is_available()

	def store_password(self, entry, description, password, entry_type=EntryType.GENERIC):
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
				pass

			else:
				# wrong password
				raise KeyringCreateError('No keyring to store password to.')
