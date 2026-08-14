from gi.repository import Gtk


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
		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		self._controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

		separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		# pack interface
		if Gtk.get_major_version() == 3:
			self._container.pack_end(separator, False, False, 0)
			self._container.pack_end(self._controls, False, False, 0)

		else:
			# GTK 4 boxes have no end packing, controls are appended by
			# _pack_end_controls once descendant class packs its own widgets
			self._separator = separator

	def _pack_end_controls(self):
		"""Append controls at the bottom of the container.

		Descendant classes call this after they pack their own widgets. GTK 3
		keeps end packed children at the bottom regardless of when they were
		added, GTK 4 orders children by the time they were appended.

		"""
		if Gtk.get_major_version() == 3:
			return

		# order matches GTK 3 where end packed children are shown in reverse
		self._container.append(self._controls)
		self._container.append(self._separator)

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
