import gtk


class MountManagerExtension:
	"""Base class for mount manager extensions.
	
	Mount manager has only one instance and is created on program startup. 
	Methods defined in this class are called automatically by the mount manager 
	so you need to implement them.

	"""
	
	def __init__(self, parent, window):
		self._parent = parent
		self._window = window
		self._application = self._parent._application

		# create user interface
		self._container = gtk.VBox(False, 5)
		self._controls = gtk.HBox(False, 5)

		# create buttons
		self._button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		self._button_close.connect('clicked', self._window._hide)

		# pack interface
		self._controls.pack_end(self._button_close, False, False, 0)
		self._container.pack_end(self._controls, False, False, 0)

	def _get_container(self):
		"""Return container widget"""
		return self._container
