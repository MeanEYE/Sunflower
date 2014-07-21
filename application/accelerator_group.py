import gtk


class AcceleratorGroup:
	"""Accelerator group provides customizable keyboard shortcuts for plugins
	with automatically generated configuration."""

	def __init__(self, application):
		self._application = application
		self._manager = self._application.accelerator_manager
		self._active = False

		self._name = None
		self._title = None
		self._window = None
		self._menus = []

		# accelerator containers
		self._methods = {}
		self._primary = {}
		self._secondary = {}
		self._paths = {}
		self._disabled = []

		# method name cache
		self._method_names = {}

		# accelerator implementation
		self._accel_group = None

	def _register_group(self):
		"""Register group with manager"""
		self._manager.register_group(self)

	def _create_group(self):
		"""Create group and connect accelerators"""
		self._accel_group = gtk.AccelGroup()

		# create accelerators
		self._create_accelerators()
		self._create_accelerators(primary=False)

		# connect paths
		self._connect_paths()

		# register group with manager
		self._register_group()

	def _connect_paths(self):
		"""Connect accelerator paths with callbacks"""
		for method_name, path in self._paths.items():
			callback = self._methods[method_name]['callback']
			self._accel_group.connect_by_path(path, callback)

	def _create_accelerators(self, primary=True):
		"""Create accelerators from specified list"""
		accelerator_list = (self._secondary, self._primary)[primary]

		# connect all methods in list
		for method_name in self._methods.keys():
			if method_name in self._disabled:
				continue  # skip if method is disabled

			# try to get saved key combination from manager
			accelerator = self._manager.get_accelerator(self._name, method_name, primary)

			# if we don't have saved key combination, use default
			if accelerator is None and method_name in accelerator_list:
				accelerator = accelerator_list[method_name]

			# finally connect accelerator to specified method
			if accelerator is not None and accelerator[0] > 0:
				keyval = accelerator[0]
				modifier = accelerator[1]
	
				# create method name cache based on key combination
				label = gtk.accelerator_get_label(keyval, modifier)
				self._method_names[label] = method_name
	
				# connect accelerator
				self._accel_group.connect_group(keyval, modifier, 0, self._handle_activate)

	def _handle_activate(self, group, widget, keyval, modifier):
		"""Handle accelerator activation"""
		label = gtk.accelerator_get_label(keyval, modifier)
		name = self._method_names[label]

		data = self._methods[name]['data']
		callback_method = self._methods[name]['callback']

		# call user method
		if data is None:
			result = callback_method(widget, label)

		else:
			result = callback_method(widget, data)

		return result

	def activate(self, window):
		"""Activate accelerator group for specified window"""
		if not self._active:
			self._window = window
	
			# connect accelerators if they are not already
			if self._accel_group is None:
				self._create_group()
	
			# add accelerator group to specified window
			self._window.add_accel_group(self._accel_group)

			# activate menus
			for menu in self._menus:
				menu.set_accel_group(self._accel_group)

			self._active = True

	def deactivate(self):
		"""Deactivate accelerator group"""
		if self._active:
			# remove accelerator group from window
			self._window.remove_accel_group(self._accel_group)

			# deactivate menus
			for menu in self._menus:
				menu.set_accel_group(None)

			self._active = False

	def invalidate(self):
		"""Force reloading accelerators"""
		pass

	def set_name(self, name):
		"""Set accelerator group name"""
		self._name = name.replace(' ', '_')

	def get_name(self):
		"""Get group name"""
		return self._name

	def set_title(self, title):
		"""Set accelerator group title"""
		self._title = title

	def add_method(self, name, title, callback, data=None):
		"""Add new method to group"""
		self._methods[name] = {
						'title': title,
						'callback': callback,
						'data': data
					}

	def add_menu(self, menu):
		"""Add menu to be connected with accelerator group on activate"""
		self._menus.append(menu)

	def set_accelerator(self, name, keyval, modifier):
		"""Set primary accelerator for specified method name"""
		self._primary[name] = (keyval, modifier)

	def set_alt_accelerator(self, name, keyval, modifier):
		"""Set secondary accelerator for specified method name"""
		self._secondary[name] = (keyval, modifier)

	def set_path(self, name, path):
		"""Set activation path for specified method name"""
		self._paths[name] = path

	def get_accelerator(self, name, primary=True):
		"""Get accelerator for specified method"""
		result = None
		group = (self._secondary, self._primary)[primary]

		if name in group:
			result = group[name]

		return result

	def get_method_title(self, name):
		"""Get title for specified accelerator"""
		result = None

		if name in self._methods:
			result = self._methods[name]['title']

		return result

	def reset_accelerator(self, name):
		"""Resets accelerator shortcuts"""
		if name in self._primary:
			del self._primary[name]

		if name in self._secondary:
			del self._secondary[name]

		# remove any cache
		for label in self._method_names:
			if self._method_names[label] == name:
				del self._method_names[label]

	def disable_accelerator(self, name):
		"""Disable specified accelerator"""
		self._disabled.append(name)

	def trigger_accelerator(self, keyval, modifier):
		"""Manually trigger accelerator"""
		result = False

		modifier = modifier & gtk.accelerator_get_default_mod_mask() # filter out unneeded mods
		label = gtk.accelerator_get_label(keyval, modifier)

		# trigger accelerator only if we have method connected
		if label in self._method_names:
			result = self._handle_activate(self._accel_group, self._window, keyval, modifier)

		return result

	def get_collisions(self, keyval, modifier):
		"""Get list of colliding accelerators"""
		result = []

		# check for collisions in primary accelerators
		for name, data in self._primary.items():
			if cmp((keyval, modifier), data) == 0:
				result.append((self, name, True))

		# check for collisions in secondary accelerators
		for name, data in self._secondary.items():
			if cmp((keyval, modifier), data) == 0:
				result.append((self, name, False))

		return result

