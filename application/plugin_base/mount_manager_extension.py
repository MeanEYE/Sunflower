
class MountManagerExtension:
	"""Base class for mount manager extensions.
	
	After initialization you need to call self._register_extension method
	to implement your class in main object. Mount manager has only one instance 
	and is created on program startup.

	"""
	
	def __init__(self, application):
		self._application = application
		self._parent = self._application.mount_manager

		self._protocol_name = None
		self._title = None
		self._mountable = False

	def _register_extension(self):
		"""Register extension with mount manager"""
		self._application.register_mount_manager_extension(self)

	def is_mountable(self):
		"""Return value indicating extension support for mountable items"""
		return self._mountable

	def get_protocol_name(self):
		"""Get associated protocol name"""
		return self._protocol_name

	def get_title(self):
		"""Get extension title"""
		return self._title
