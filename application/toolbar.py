import gtk

from gui.input_dialog import CreateToolbarWidgetDialog


class ToolbarManager:
	"""Manager for toolbar widget factories"""

	def __init__(self, application):
		self._application = application

		self._config = None
		self._widget_types = {}
		self._factory_cache = {}
		self._factories = []

		self._toolbar = gtk.Toolbar()

	def _widget_exists(self, name):
		"""Check if widget with specified name exists"""
		return self._config.has_section(self.get_section_name(name))

	def _add_widget(self, name, widget_type):
		"""Add widget to list"""
		number = len(self._config.options('widgets')) / 2

		self._config.set('widgets', 'name_{0}'.format(number), name)
		self._config.set('widgets', 'type_{0}'.format(number), widget_type)

	def get_toolbar(self):
		"""Return toolbar widget"""
		return self._toolbar

	def get_description(self, widget_type):
		"""Get widget description for specified type"""
		result = None

		data = self.get_widget_data(widget_type)
		if data is not None:
			result = data[0]

		return result

	def get_icon(self, widget_type):
		"""Get icon name for specified widget type"""
		result = None

		data = self.get_widget_data(widget_type)
		if data is not None:
			result = data[1]

		return result

	def get_widget_data(self, widget_type):
		"""Get data for specified widget type"""
		result = None

		if self._widget_types.has_key(widget_type):
			result = self._widget_types[widget_type]

		return result

	def get_section_name(self, name):
		"""Create section name"""
		return 'widget_{0}'.format(name.lower().replace(' ', '_'))

	def load_config(self, config_parser):
		"""Set config parser for toolbar"""
		self._config = config_parser

		if not self._config.has_section('widgets'):
			self._config.add_section('widgets')

	def create_widgets(self):
		"""Create widgets for toolbar"""
		count = len(self._config.options('widgets')) / 2

		# remove existing widgets
		self._toolbar.foreach(lambda item: self._toolbar.remove(item))

		# create new widgets
		for number in range(0, count):
			name = self._config.get('widgets', 'name_{0}'.format(number))
			widget_type = self._config.get('widgets', 'type_{0}'.format(number))

			# skip creating widget if there's no factory for specified type
			if not self._factory_cache.has_key(widget_type): continue

			# get factory from cache
			factory = self._factory_cache[widget_type]

			# get config
			section_name = self.get_section_name(name)
			config = {}

			for option in self._config.options(section_name):
				config[option] = self._config.get(section_name, option)

			widget = factory.get_widget(name, widget_type, config)

			if widget is not None:
				widget.show()
				self._toolbar.add(widget)

	def register_factory(self, FactoryClass):
		"""Register and create new factory"""
		factory = FactoryClass(self._application)

		# add factory to local storage
		self._factories.append(factory)

		# get widget list
		widgets = factory.get_types()

		# update types and factory cache
		if widgets is not None:
			self._widget_types.update(widgets)

			for widget_type in widgets.keys():
				self._factory_cache[widget_type] = factory

	def show_create_widget_dialog(self, window=None):
		"""Show dialog with type selection and name input"""
		result = False
		dialog = CreateToolbarWidgetDialog(self._application)

		# update dialog type list
		dialog.update_type_list(self._widget_types)

		# set transient window if specified
		if window is not None:
			dialog.set_transient_for(window)

		# get user response
		response, name, widget_type = dialog.get_response()

		if response == gtk.RESPONSE_ACCEPT:
			if None in (name, widget_type) or name == '':
				# user didn't input all the data
				dialog = gtk.MessageDialog(
					                    self._application,
					                    gtk.DIALOG_DESTROY_WITH_PARENT,
					                    gtk.MESSAGE_ERROR,
					                    gtk.BUTTONS_OK,
					                    _(
					                        "Error adding widget. You need to enter unique "
				                            "name and select widget type."
					                    )
					                )
				dialog.run()
				dialog.destroy()

			elif self._widget_exists(name):
				# item with the same name already exists
				dialog = gtk.MessageDialog(
					                    self._application,
					                    gtk.DIALOG_DESTROY_WITH_PARENT,
					                    gtk.MESSAGE_ERROR,
					                    gtk.BUTTONS_OK,
					                    _(
				                            "Widget with specified name already exists. "
				                            "You need to enter unique name and select widget type."
				                        )
					                )
				dialog.run()
				dialog.destroy()

			else:
				# get factory from cache
				factory = self._factory_cache[widget_type]

				# present configuration dialog
				config = factory.create_widget(name, widget_type, window)

				# save config
				if config is not None:
					self._add_widget(name, widget_type)

					# create config section
					section_name = self.get_section_name(name)
					self._config.add_section(section_name)

					for key, value in config.items():
						self._config.set(section_name, key, value)

					result = True

		return result

	def show_configure_widget_dialog(self, name, widget_type, window=None):
		"""Show blocking configuration dialog for specified widget"""
		if not self._factory_cache.has_key(widget_type):
			# there is no factory for specified type, show error and return
			dialog = gtk.MessageDialog(
		                            self._application,
		                            gtk.DIALOG_DESTROY_WITH_PARENT,
		                            gtk.MESSAGE_ERROR,
		                            gtk.BUTTONS_OK,
		                            _(
		                                "Plugin used to create selected toolbar widget is not active "
			                            "or not present. In order to edit this entry you need to activate "
			                            "plugin used to create it."
		                            )
		                        )
			dialog.run()
			dialog.destroy()

			return False

		# get factory
		factory = self._factory_cache[widget_type]

		# load config
		config = {}
		section_name = self.get_section_name(name)

		for option in self._config.options(section_name):
			config[option] = self._config.get(section_name, option)

		# get user input
		config = factory.configure_widget(name, widget_type, config)

		if config is not None:
			# clear configuration section
			self._config.remove_section(section_name)
			self._config.add_section(section_name)

			# record new values
			for key, value in config.items():
				self._config.set(section_name, key, value)

		return config is not None
