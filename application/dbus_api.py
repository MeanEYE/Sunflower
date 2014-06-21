import dbus, dbus.service, dbus.glib
from parameters import Parameters

class DBus(dbus.service.Object):
	def __init__(self, app):
		self._app = app
		bus_name = dbus.service.BusName('org.sunflower.API', bus = dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, '/org/sunflower/API')

	@dbus.service.method(dbus_interface='org.sunflower.API')
	def show_window(self):
		self._app.set_visible(True)
		self._app.indicator.adjust_visibility_items(True)

	@dbus.service.method(dbus_interface='org.sunflower.API', utf8_strings=True)
	def create_tab(self, path, position):
		options = Parameters()
		options.set('path', path)
		notebook = self._app.left_notebook if position == 'left' else self._app.right_notebook
		self._app.create_tab(notebook, self._app.plugin_classes['file_list'], options)

	@dbus.service.method(dbus_interface='org.sunflower.API')
	def create_terminal(self, path, position):
		options = Parameters()
		options.set('path', path)
		notebook = self._app.left_notebook if position == 'left' else self._app.right_notebook
		self._app.create_tab(notebook, self._app.plugin_classes['system_terminal'], options)