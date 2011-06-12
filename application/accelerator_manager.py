import gtk


class AcceleratorManager:

	def __init__(self, application):
		self._application = application
		self._config = None

		self._groups = []
		self._group_names = []

	def _save_accelerator(self, section, name, accelerator=None, primary=True, can_overwrite=False):
		"""Save accelerator to config file"""
		if not primary:
			name = '{0}_2'.format(name)

		label = ''
		if accelerator is not None:
			label = gtk.accelerator_name(*accelerator)

		# don't allow overwriting user's configuration unless strictly specified
		if not self._config.has_option(section, name) \
		or (self._config.has_option(section, name) and can_overwrite):
			self._config.set(section, name, label)

	def _load_accelerator(self, section, name, primary=True):
		"""Load accelerator from config file"""
		result = None

		if not primary:
			name = '{0}_2'.format(name)

		# try to load only if config has accelerator specified
		if self._config.has_section(section) \
		and self._config.has_option(section, name):
			accelerator = gtk.accelerator_parse(self._config.get(section, name))

			if gtk.accelerator_valid(*accelerator):
				result = accelerator

		return result

	def register_group(self, group):
		"""Register group with manager"""
		if not self._config.has_section(group._name):
			self._config.add_section(group._name)

		# add all the methods to config file
		for name in group._methods:

			# save primary accelerator
			if group._primary.has_key(name):
				self._save_accelerator(group._name, name, group._primary[name])

			else:
				self._save_accelerator(group._name, name)

			# save secondary accelerator
			if group._secondary.has_key(name):
				self._save_accelerator(group._name, name, group._secondary[name], primary=False)

	def get_groups(self):
		"""Get list of unique group names"""
		pass

	def get_methods(self, name):
		"""Get list of methods for a specific group"""
		pass

	def get_accelerator(self, group, name, primary=True):
		"""Get saved accelerator"""
		return self._load_accelerator(group, name, primary)

	def load(self, config):
		"""Load accelerator map"""
		self._config = config

	def save(self):
		"""Save accelerator map"""
		pass
