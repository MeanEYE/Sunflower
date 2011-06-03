import gtk

from widgets.settings_page import SettingsPage

VISIBLE_ALWAYS		= 0
VISIBLE_WHEN_NEEDED	= 1
VISIBLE_NEVER		= 2


class DisplayOptions(SettingsPage):
	"""Display options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'display', _('Display'))

		# main window options
		frame_main_window = gtk.Frame(_('Main window'))
		vbox_main_window = gtk.VBox(False, 0)
		vbox_main_window.set_border_width(5)

		self._checkbox_hide_on_close = gtk.CheckButton(_('Hide main window on close'))
		self._checkbox_show_toolbar = gtk.CheckButton(_('Show toolbar'))
		self._checkbox_show_command_bar = gtk.CheckButton(_('Show command bar'))
		self._checkbox_show_command_entry = gtk.CheckButton(_('Show command entry'))

		self._checkbox_hide_on_close.connect('toggled', self._parent.enable_save, True)
		self._checkbox_show_toolbar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_bar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_entry.connect('toggled', self._parent.enable_save)

		# tab options
		frame_tabs = gtk.Frame(_('Tabs'))
		vbox_tabs = gtk.VBox(False, 0)
		vbox_tabs.set_border_width(5)

		self._checkbox_focus_new_tab = gtk.CheckButton(_('Focus new tab after opening'))
		self._checkbox_button_relief = gtk.CheckButton(_('Show normal button relief'))
		self._checkbox_button_icons = gtk.CheckButton(_('Show icons instead of text in tab buttons'))
		self._checkbox_tab_close_button = gtk.CheckButton(_('Show close button'))
		self._checkbox_always_show_tabs = gtk.CheckButton(_('Show tab(s) even if there is only one'))
		self._checkbox_ubuntu_coloring = gtk.CheckButton(_('Use Ubuntu coloring method for tab title bars'))

		self._checkbox_focus_new_tab.connect('toggled', self._parent.enable_save)
		self._checkbox_button_relief.connect('toggled', self._parent.enable_save)
		self._checkbox_button_icons.connect('toggled', self._parent.enable_save, True)
		self._checkbox_tab_close_button.connect('toggled', self._parent.enable_save)
		self._checkbox_always_show_tabs.connect('toggled', self._parent.enable_save)
		self._checkbox_ubuntu_coloring.connect('toggled', self._parent.enable_save)

		vbox_status_bar = gtk.VBox(False, 0)
		vbox_status_bar.set_border_width(5)

		label_status_bar = gtk.Label(_('Show status bar:'))
		label_status_bar.set_alignment(0, 0.5)

		list_status_bar = gtk.ListStore(str, int)
		list_status_bar.append((_('Always'), VISIBLE_ALWAYS))
		list_status_bar.append((_('When needed'), VISIBLE_WHEN_NEEDED))
		list_status_bar.append((_('Never'), VISIBLE_NEVER))

		cell_status_bar = gtk.CellRendererText()

		self._combobox_status_bar = gtk.ComboBox(list_status_bar)
		self._combobox_status_bar.connect('changed', self._parent.enable_save)
		self._combobox_status_bar.pack_start(cell_status_bar)
		self._combobox_status_bar.add_attribute(cell_status_bar, 'text', 0)

		# operation options
		frame_operation = gtk.Frame(_('Other'))
		vbox_operation = gtk.VBox(False, 0)
		vbox_operation.set_border_width(5)

		self._checkbox_hide_window_on_minimize = gtk.CheckButton(_('Hide operation window on minimize'))
		self._checkbox_human_readable_size = gtk.CheckButton(_('Show sizes in human readable format'))

		self._checkbox_hide_window_on_minimize.connect('toggled', self._parent.enable_save)
		self._checkbox_human_readable_size.connect('toggled', self._parent.enable_save)

		# pack ui
		vbox_status_bar.pack_start(label_status_bar, False, False, 0)
		vbox_status_bar.pack_start(self._combobox_status_bar, False, False, 0)

		vbox_main_window.pack_start(self._checkbox_hide_on_close, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_toolbar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_bar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_entry, False, False, 0)

		vbox_tabs.pack_start(self._checkbox_focus_new_tab, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_button_relief, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_button_icons, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_tab_close_button, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_always_show_tabs, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_ubuntu_coloring, False, False, 0)
		vbox_tabs.pack_start(vbox_status_bar, False, False, 0)

		vbox_operation.pack_start(self._checkbox_hide_window_on_minimize, False, False, 0)
		vbox_operation.pack_start(self._checkbox_human_readable_size, False, False, 0)

		frame_main_window.add(vbox_main_window)
		frame_tabs.add(vbox_tabs)
		frame_operation.add(vbox_operation)

		self.pack_start(frame_main_window, False, False, 0)
		self.pack_start(frame_tabs, False, False, 0)
		self.pack_start(frame_operation, False, False, 0)

	def _load_options(self):
		"""Load display options"""
		options = self._application.options

		self._checkbox_hide_on_close.set_active(options.getboolean('main', 'hide_on_close'))
		self._checkbox_focus_new_tab.set_active(options.getboolean('main', 'focus_new_tab'))
		self._checkbox_show_toolbar.set_active(options.getboolean('main', 'show_toolbar'))
		self._checkbox_show_command_bar.set_active(options.getboolean('main', 'show_command_bar'))
		self._checkbox_show_command_entry.set_active(options.getboolean('main', 'show_command_entry'))
		self._checkbox_button_relief.set_active(bool(options.getint('main', 'button_relief')))
		self._checkbox_button_icons.set_active(options.getboolean('main', 'tab_button_icons'))
		self._checkbox_tab_close_button.set_active(options.getboolean('main', 'tab_close_button'))
		self._checkbox_always_show_tabs.set_active(options.getboolean('main', 'always_show_tabs'))
		self._checkbox_ubuntu_coloring.set_active(options.getboolean('main', 'ubuntu_coloring'))
		self._checkbox_hide_window_on_minimize.set_active(options.getboolean('main', 'hide_operation_on_minimize'))
		self._checkbox_human_readable_size.set_active(options.getboolean('main', 'human_readable_size'))
		self._combobox_status_bar.set_active(options.getint('main', 'show_status_bar'))

	def _save_options(self):
		"""Save display options"""
		options = self._application.options

		# for config parser to get boolean, you need to set string :/. makes sense?
		_bool = ('False', 'True')

		# save options
		options.set('main', 'hide_on_close', _bool[self._checkbox_hide_on_close.get_active()])
		options.set('main', 'focus_new_tab', _bool[self._checkbox_focus_new_tab.get_active()])
		options.set('main', 'show_toolbar', _bool[self._checkbox_show_toolbar.get_active()])
		options.set('main', 'show_command_bar', _bool[self._checkbox_show_command_bar.get_active()])
		options.set('main', 'show_command_entry', _bool[self._checkbox_show_command_entry.get_active()])
		options.set('main', 'button_relief', int(self._checkbox_button_relief.get_active()))
		options.set('main', 'tab_button_icons', _bool[self._checkbox_button_icons.get_active()])
		options.set('main', 'tab_close_button', _bool[self._checkbox_tab_close_button.get_active()])
		options.set('main', 'always_show_tabs', _bool[self._checkbox_always_show_tabs.get_active()])
		options.set('main', 'ubuntu_coloring', _bool[self._checkbox_ubuntu_coloring.get_active()])
		options.set('main', 'hide_operation_on_minimize', _bool[self._checkbox_hide_window_on_minimize.get_active()])
		options.set('main', 'human_readable_size', _bool[self._checkbox_human_readable_size.get_active()])
		options.set('main', 'show_status_bar', self._combobox_status_bar.get_active())
