import gtk
import threading

try:
	import gnomekeyring as keyring

except:
	keyring = None


class EntryType:
	NO_TYPE = 0
	GENERIC = 1
	NETWORK = 2
	NOTE = 3


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
		pass

	def get_password(self, entry):
		"""Return password for specified entry"""
		pass

	def store_password(self, entry, description, password, entry_type=EntryType.GENERIC):
		"""Create new entry in keyring with specified data"""
		pass
