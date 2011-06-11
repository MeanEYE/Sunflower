import gtk


class InvalidMethodError(Exception): pass

class AcceleratorGroup:
	"""Accelerator group is used to provide users with customizable
	keyboard shortcuts for plugins.

	This class will automatically provide configuration interface.

	"""

	def __init__(self, application):
		self._name = None
		self._title = None

		self._methods = {}
		self._method_names = {}
		self._method_accels = {}

		self._accels = gtk.AccelGroup()

	def _handle_accelerator_activate(self, group, widget, keyval, modifier):
		"""Handle accelerator activation"""
		label = gtk.accelerator_get_label(keyval, modifier)
		name = self._method_names[label]

		# call user method
		self._methods[name]['callback'](widget)

	def set_name(self, name):
		"""Set accelerator group name

		This name will be used in config files.

		"""
		self._name = name.replace(' ', '_')

	def set_title(self, title):
		"""Set accelerator group title

		This title will be used in configuration page.

		"""
		self._title = title

	def add_method(self, name, title, callback):
		"""Add accelerator to group"""
		self._methods[name] = {
						'title': title,
						'callback': callback
					}

	def set_accelerator(self, name, key, mods):
		"""Set accelerator for specified method name

		key - Integer value for a key
		mods - Modifier mask (eg. gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)

		"""
		if not self._methods.has_key:
			raise InvalidMethodError('Specified method name ({0}) is not valid!'.format(name))

		# connect method name to accelerator label
		label = gtk.accelerator_get_label(key, mods)
		self._method_names[label] = name

		# connect accelerator to local method
		self._accels.connect_group(key, mods, 0, self._handle_accelerator_activate)

	def get_accel_group(self):
		"""Return GTK+ accel group"""
		return self._accels
