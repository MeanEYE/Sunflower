import gtk


class ExtensionFeatures:
	SYSTEM_WIDE = 0


class MountManagerExtension:
	"""Base class for mount manager extensions.
	
	Mount manager has only one instance and is created on program startup. 
	Methods defined in this class are called automatically by the mount manager 
	so you need to implement them.

	"""

	# features extension supports
	features = ()
	
	def __init__(self, parent, window):
		self._parent = parent
		self._window = window
		self._application = self._parent._application

		# create user interface
		self._container = gtk.VBox(False, 5)
		self._controls = gtk.HBox(False, 5)

		separator = gtk.HSeparator()

		# pack interface
		self._container.pack_end(separator, False, False, 0)
		self._container.pack_end(self._controls, False, False, 0)

	def can_handle(self, uri):
		"""Returns boolean denoting if specified URI can be handled by this extension"""
		return False

	def get_container(self):
		"""Return container widget"""
		return self._container

	def get_information(self):
		"""Returns information about extension"""
		icon = None
		name = None

		return icon, name

	def unmount(self, uri):
		"""Method called by the mount manager for unmounting the selected URI"""
		pass

	def focus_object(self):
		"""Method called by the mount manager for focusing main object"""
		pass

	@classmethod
	def get_features(cls):
		"""Returns set of features supported by extension"""
		return cls.features
