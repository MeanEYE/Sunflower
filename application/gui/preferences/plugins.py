import os
import gtk
import locale

from ConfigParser import ConfigParser
from widgets.settings_page import SettingsPage


class Column:
	ACTIVE = 0
	LOCATION = 1
	NAME = 2
	AUTHOR = 3
	VERSION = 4
	CONTACT = 5
	SITE = 6
	DESCRIPTION = 7


class Section:
	NAME = 'Name'
	DESCRIPTION = 'Description'
	VERSION = 'Version'
	AUTHOR = 'Author'


class PluginsOptions(SettingsPage):
	"""Plugins options extension class"""

	NAME_SECTION = 'Name'
	AUTHOR_SECTION = 'Author'

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'plugins', _('Plugins'))

		# create interface
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		# create list box
		self._plugins = gtk.ListStore(
									bool,	# active
									str,	# location
									str,	# name
									str,	# author
									str,	# version
									str,	# contact
									str,	# site
									str		# description
								)

		self._list = gtk.TreeView()
		self._list.set_model(self._plugins)
		self._list.set_rules_hint(True)
		self._list.connect('cursor-changed', self.__handle_cursor_change)

		# create and configure cell renderers
		cell_active = gtk.CellRendererToggle()
		cell_active.connect('toggled', self._toggle_plugin)
		cell_name = gtk.CellRendererText()
		cell_author = gtk.CellRendererText()
		cell_version = gtk.CellRendererText()

		# create and pack columns
		col_active = gtk.TreeViewColumn(_('Active'), cell_active, active=Column.ACTIVE)

		col_name = gtk.TreeViewColumn(_('Plugin name'), cell_name, text=Column.NAME)
		col_name.set_resizable(True)
		col_name.set_expand(True)

		col_version = gtk.TreeViewColumn(_('Version'), cell_version, text=Column.VERSION)

		col_author = gtk.TreeViewColumn(_('Author'), cell_author, text=Column.AUTHOR)
		col_author.set_resizable(True)

		self._list.append_column(col_active)
		self._list.append_column(col_name)
		self._list.append_column(col_version)
		self._list.append_column(col_author)

		# create description
		self._label_description = gtk.Label()
		self._label_description.set_use_markup(True)
		self._label_description.set_line_wrap(True)
		self._label_description.set_selectable(True)
		self._label_description.set_padding(5, 5)
		self._label_description.connect('size-allocate', self.__adjust_label)

		self._expander_description = gtk.Expander(_('Description'))
		self._expander_description.add(self._label_description)

		# create controls
		hbox_controls = gtk.HBox(False, 5)

		image_contact = gtk.Image()
		image_contact.set_from_icon_name('gnome-stock-mail-new', gtk.ICON_SIZE_BUTTON)

		self._button_contact = gtk.Button()
		self._button_contact.set_label(_('Contact'))
		self._button_contact.set_image(image_contact)
		self._button_contact.set_sensitive(False)
		self._button_contact.connect('clicked', self.__handle_contact_button_click)

		image_home_page = gtk.Image()
		image_home_page.set_from_stock(gtk.STOCK_HOME, gtk.ICON_SIZE_BUTTON)

		self._button_home_page = gtk.Button()
		self._button_home_page.set_label(_('Visit site'))
		self._button_home_page.set_image(image_home_page)
		self._button_home_page.set_sensitive(False)
		self._button_home_page.connect('clicked', self.__handle_home_page_button_click)

		# pack containers
		container.add(self._list)

		hbox_controls.pack_start(self._button_contact, False, False, 0)
		hbox_controls.pack_start(self._button_home_page, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_start(self._expander_description, False, False, 0)
		self.pack_start(hbox_controls, False, False, 0)

	def __handle_cursor_change(self, widget, data=None):
		"""Update button state when list cursor changes"""
		selection = widget.get_selection()
		item_store, selected_iter = selection.get_selected()

		if selected_iter is not None:
			self._label_description.set_text(item_store.get_value(selected_iter, Column.DESCRIPTION))

			has_contact = item_store.get_value(selected_iter, Column.CONTACT) is not None
			has_site = item_store.get_value(selected_iter, Column.SITE) is not None

			self._button_contact.set_sensitive(has_contact)
			self._button_home_page.set_sensitive(has_site)
		
	def __handle_contact_button_click(self, widget, data=None):
		"""Create new contact email"""
		selection = self._list.get_selection()
		item_store, selected_iter = selection.get_selected()

		if selected_iter is not None:
			email = item_store.get_value(selected_iter, Column.CONTACT)
			email = 'xdg-open mailto:{0}'.format(email)

			os.system(email)

	def __handle_home_page_button_click(self, widget, data=None):
		"""Create new contact email"""
		selection = self._list.get_selection()
		item_store, selected_iter = selection.get_selected()

		if selected_iter is not None:
			url = item_store.get_value(selected_iter, Column.SITE)
			self._application.goto_web(self, url)

	def __adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)

	def _toggle_plugin(self, cell, path):
		"""Handle changing plugin state"""
		plugin = self._plugins[path][Column.LOCATION]
		plugin_name = self._plugins[path][Column.NAME]

		if plugin not in self._application.protected_plugins:
			# plugin is not protected, toggle it's state
			self._plugins[path][Column.ACTIVE] = not self._plugins[path][Column.ACTIVE]

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
										"{0} is required for "
										"normal program operation and therefore can "
										"not be deactivated!"
									).format(plugin_name)
								)

			dialog.run()
			dialog.destroy()

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options

		# clear existing list
		self._plugins.clear()

		# get list of plugins
		plugin_list = self._application._get_plugin_list()
		plugins_to_load = options.get('plugins')

		# extract current locale
		language = locale.getdefaultlocale()[0]

		# populate list
		for plugin in plugin_list:
			# default values
			plugin_name = plugin
			plugin_author = ''
			plugin_version = ''
			plugin_site = None
			plugin_contact = None
			plugin_description = _('This plugin has no description')

			system_plugin_config = os.path.join(self._application.system_plugin_path, plugin, 'plugin.conf')
			user_plugin_config = os.path.join(self._application.user_plugin_path, plugin, 'plugin.conf')

			# prefer user plugin over system version
			plugin_config = user_plugin_config if os.path.exists(user_plugin_config) else system_plugin_config

			# read plugin data from configuration file
			if os.path.exists(plugin_config):
				config = ConfigParser()
				config.read(plugin_config)

				if config.has_section(Section.NAME) and language is not None:
					if config.has_option(Section.NAME, language):
						# try to get plugin name for current language
						plugin_name = config.get(Section.NAME, language)

					elif config.has_option(Section.NAME, 'en'):
						# try to get plugin name for default language
						plugin_name = config.get(Section.NAME, 'en')

				if config.has_section(Section.AUTHOR):
					# get author name
					if config.has_option(Section.AUTHOR, 'name'):
						plugin_author = config.get(Section.AUTHOR, 'name')

					# get contact email
					if config.has_option(Section.AUTHOR, 'contact'):
						plugin_contact = config.get(Section.AUTHOR, 'contact')

					if config.has_option(Section.AUTHOR, 'site'):
						plugin_site = config.get(Section.AUTHOR, 'site')

				if config.has_section(Section.DESCRIPTION) and language is not None:
					if config.has_option(Section.DESCRIPTION, language):
						# try to get plugin description for current language
						plugin_description = config.get(Section.DESCRIPTION, language)

					elif config.has_option(Section.DESCRIPTION, 'en'):
						# try to get plugin description for default language
						plugin_description = config.get(Section.DESCRIPTION, 'en')

				if config.has_section(Section.VERSION) and config.has_option(Section.VERSION, 'number'):
					plugin_version = config.get(Section.VERSION, 'number')

			# add plugin data to list
			self._plugins.append((
							plugin in plugins_to_load,
							plugin,
							plugin_name,
							plugin_author,
							plugin_version,
							plugin_contact,
							plugin_site,
							plugin_description
						))

			# clear description
			self._label_description.set_text(_('No plugin selected'))
			self._expander_description.set_expanded(False)

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options

		# get only selected plugins
		plugin_list = filter(lambda row: row[Column.ACTIVE], self._plugins)

		# we need only plugin names
		plugin_list = [row[Column.LOCATION] for row in plugin_list]

		# save plugin list
		options.set('plugins', plugin_list)
