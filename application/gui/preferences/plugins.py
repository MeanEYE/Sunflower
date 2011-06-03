import gtk

from widgets.settings_page import SettingsPage


class PluginsOptions(SettingsPage):
	"""Plugins options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'plugins', _('Plugins'))

		# create interface
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		# create list box
		self._plugins = gtk.ListStore(bool, str)

		self._list = gtk.TreeView()
		self._list.set_model(self._plugins)
		self._list.set_rules_hint(True)

		# create and configure cell renderers
		cell_active = gtk.CellRendererToggle()
		cell_active.connect('toggled', self._toggle_plugin)
		cell_name = gtk.CellRendererText()

		# create and pack columns
		col_active = gtk.TreeViewColumn(_('Active'), cell_active, active=0)

		col_name = gtk.TreeViewColumn(_('Plugin file'), cell_name, text=1)
		col_name.set_resizable(True)
		col_name.set_expand(True)

		self._list.append_column(col_active)
		self._list.append_column(col_name)

		container.add(self._list)
		self.pack_start(container, True, True, 0)

	def _toggle_plugin(self, cell, path):
		"""Handle changing plugin state"""
		plugin = self._plugins[path][1]

		if plugin not in self._application.protected_plugins:
			# plugin is not protected, toggle it's state
			self._plugins[path][0] = not self._plugins[path][0]

			# enable save button
			self._parent.enable_save(show_restart=True)

		else:
			# plugin is protected, show appropriate message
			dialog = gtk.MessageDialog(
									self._application,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_INFO,
									gtk.BUTTONS_OK,
									_(
										"Specified plugin ('{0}') is required for "
										"normal program operation and therefore can "
										"not be deactivated!"
									).format(plugin)
								)

			dialog.run()
			dialog.destroy()

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options

		# clear existing list
		self._plugins.clear()

		# get list of plugins
		list_ = self._application._get_plugin_list()
		plugins_to_load = options.get('main', 'plugins').split(',')

		# populate list
		for plugin in list_:
			self._plugins.append((
							plugin in plugins_to_load,
							plugin
						))

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options

		# get only selected plugins
		list_ = filter(lambda row: row[0], self._plugins)

		# we need only plugin names
		list_ = [row[1] for row in list_]

		# save plugin list
		options.set('main', 'plugins', ','.join(list_))
