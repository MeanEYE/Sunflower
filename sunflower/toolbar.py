from __future__ import absolute_import

from gi.repository import Gtk
from sunflower.gui.input_dialog import CreateToolbarWidgetDialog


class ToolbarManager:
	"""Manager for toolbar widget factories"""

	def __init__(self, application):
		self._application = application

		self._config = None
		self._widget_types = {}
		self._factory_cache = {}
		self._factories = []

		self._toolbar = Gtk.Toolbar()

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

		if widget_type in self._widget_types:
			result = self._widget_types[widget_type]

		return result

	def load_config(self, config):
		"""Set config parser for toolbar"""
		self._config = config

	def create_widgets(self):
		"""Create widgets for toolbar"""
		# remove existing widgets
		self._toolbar.foreach(lambda item: self._toolbar.remove(item))

		# create new widgets
		for item in self._config.get('items'):
			widget_name = item['name']
			widget_type = item['type']

			# skip creating widget if there's no factory for specified type
			if not widget_type in self._factory_cache: continue

			# get factory from cache
			factory = self._factory_cache[widget_type]

			# get config
			config = item['config']
			widget = factory.get_widget(widget_name, widget_type, config)

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

		if response == Gtk.ResponseType.ACCEPT:
			if None in (name, widget_type) or name == '':
				# user didn't input all the data
				dialog = Gtk.MessageDialog(
					self._application,
					Gtk.DialogFlags.DESTROY_WITH_PARENT,
					Gtk.MessageType.ERROR,
					Gtk.ButtonsType.OK,
					_(
						"Error adding widget. You need to enter unique "
						"name and select widget type."
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
					result = {
						'name': name,
						'type': widget_type,
						'config': config,
					}

		return result

	def show_configure_widget_dialog(self, name, widget_type, widget_config, window=None):
		"""Show blocking configuration dialog for specified widget"""
		if not widget_type in self._factory_cache:
			# there is no factory for specified type, show error and return
			dialog = Gtk.MessageDialog(
				self._application,
				Gtk.DialogFlags.DESTROY_WITH_PARENT,
				Gtk.MessageType.ERROR,
				Gtk.ButtonsType.OK,
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
		config = factory.configure_widget(name, widget_type, widget_config)
		if config:
			return config

		return {}

	def apply_settings(self):
		"""Apply toolbar settings"""
		self._toolbar.set_style(self._config.get('style'))
		self._toolbar.set_icon_size(self._config.get('icon_size'))
