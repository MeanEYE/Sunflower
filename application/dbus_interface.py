import sys
import dbus, dbus.service, dbus.glib

from parameters import Parameters


class DBus_Client():

	def __init__(self, app):
		self._application = app
		self._bus_name = 'org.sunflower.API'
		self._path = '/org/sunflower/API'
		self._bus = dbus.SessionBus()
		self._proxy = None
		self.connect()

	def connect(self):
		"""Connect client to DBus service."""
		try:
			self._proxy = self._bus.get_object(self._bus_name, self._path)

		except dbus.exceptions.DBusException:
			self._proxy = None

	def disconnect(self):
		"""Disconnect from DBus service."""
		if self._proxy is not None:
			self._proxy.close()

	def is_connected(self):
		return True if self._proxy else False

	def show_window(self):
		"""Send request to show window through DBus."""
		assert self._proxy is not None
		self._proxy.get_dbus_method('show_window')()

	def create_tab(self, path, position=None):
		"""Create tab in running instance."""
		assert self._proxy is not None
		create_tab = self._proxy.get_dbus_method('create_tab')
		create_tab(path, position)

	def create_terminal(self, path, position=None):
		"""Create terminal tab in running instance."""
		assert self._proxy is not None
		create_terminal = self._proxy.get_dbus_method('create_terminal')
		create_terminal(path, position)

	def one_instance(self):
		"""Make create tabs, focus existing instance window and exit."""
		arguments = self._application.arguments

		if arguments is not None:
			if arguments.left_tabs is not None:
				map(self.create_tab, arguments.left_tabs, ['left'] * len(arguments.left_tabs))

			if arguments.right_tabs is not None:
				map(self.create_tab, arguments.right_tabs, ['right'] * len(arguments.right_tabs))

			if self._application.arguments.left_terminals is not None:
				map(self.create_terminal, arguments.left_terminals, ['left'] * len(arguments.left_terminals))

			if self._application.arguments.right_terminals is not None:
				map(self.create_terminal, arguments.right_terminals, ['right'] * len(arguments.right_terminals))

		self.show_window()
		sys.exit()


class DBus_Service(dbus.service.Object):
	"""Service provider object for DBus."""

	def __new__(cls, *args, **kwargs):
		try:
			dbus.SessionBus()
			return object.__new__(cls, args, kwargs)

		except dbus.exceptions.DBusException:
			return None

	def __init__(self, app):
		self._application = app
		bus_name = dbus.service.BusName('org.sunflower.API', bus = dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, '/org/sunflower/API')

	@dbus.service.method(dbus_interface='org.sunflower.API')
	def show_window(self):
		"""Expose method for showing main window."""
		self._application.set_visible(True)
		self._application.indicator.adjust_visibility_items(True)

	@dbus.service.method(dbus_interface='org.sunflower.API', utf8_strings=True)
	def create_tab(self, path, position=None):
		"""Expose method for creating standard tab."""
		options = Parameters()
		options.set('path', path)

		if position == 'left':
			notebook = self._application.left_notebook

		elif position == 'right':
			notebook = self._application.right_notebook

		else:
			notebook = self._application.get_active_notebook()

		self._application.create_tab(notebook, self._application.plugin_classes['file_list'], options)

	@dbus.service.method(dbus_interface='org.sunflower.API')
	def create_terminal(self, path, position=None):
		"""Expose method for creating terminal tab."""
		options = Parameters()
		options.set('path', path)

		if position == 'left':
			notebook = self._application.left_notebook

		elif position == 'right':
			notebook = self._application.right_notebook

		else:
			notebook = self._application.get_active_notebook()

		self._application.create_tab(notebook, self._application.plugin_classes['system_terminal'], options)
