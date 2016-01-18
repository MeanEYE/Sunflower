import gtk

from common import SizeFormat
from widgets.settings_page import SettingsPage


class StatusVisible:
	ALWAYS = 0
	WHEN_NEEDED = 1
	NEVER = 2


class TabExpand:
	NONE = 0
	ACTIVE = 1
	ALL = 2


class DisplayOptions(SettingsPage):
	"""Display options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'display', _('Display'))

		notebook = gtk.Notebook()

		# main window options
		label_main_window = gtk.Label(_('Main window'))
		vbox_main_window = gtk.VBox(False, 0)
		vbox_main_window.set_border_width(5)

		self._checkbox_hide_on_close = gtk.CheckButton(_('Hide main window on close'))
		self._checkbox_multiple_instances = gtk.CheckButton(_('Allow multiple instances'))
		self._checkbox_show_toolbar = gtk.CheckButton(_('Show toolbar'))
		self._checkbox_show_command_bar = gtk.CheckButton(_('Show command bar'))
		self._checkbox_show_command_entry = gtk.CheckButton(_('Show command entry'))
		self._checkbox_horizontal_split = gtk.CheckButton(_('Horizontal split'))

		self._checkbox_hide_on_close.connect('toggled', self._parent.enable_save, True)
		self._checkbox_multiple_instances.connect('toggled', self._parent.enable_save, True)
		self._checkbox_show_toolbar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_bar.connect('toggled', self._parent.enable_save)
		self._checkbox_show_command_entry.connect('toggled', self._parent.enable_save)
		self._checkbox_horizontal_split.connect('toggled', self._parent.enable_save)

		# tab options
		label_tabs = gtk.Label(_('Tabs'))
		vbox_tabs = gtk.VBox(False, 0)
		vbox_tabs.set_border_width(5)

		self._checkbox_focus_new_tab = gtk.CheckButton(_('Focus new tab after opening'))
		self._checkbox_button_relief = gtk.CheckButton(_('Show normal button relief'))
		self._checkbox_button_icons = gtk.CheckButton(_('Show icons instead of text in tab buttons'))
		self._checkbox_tab_close_button = gtk.CheckButton(_('Show close button'))
		self._checkbox_always_show_tabs = gtk.CheckButton(_('Show tab(s) even if there is only one'))
		self._checkbox_ubuntu_coloring = gtk.CheckButton(_('Use Ubuntu coloring method for tab title bars'))
		self._checkbox_superuser_notification = gtk.CheckButton(_('Change title bar color when started as super user'))

		self._checkbox_focus_new_tab.connect('toggled', self._parent.enable_save)
		self._checkbox_button_relief.connect('toggled', self._parent.enable_save)
		self._checkbox_button_icons.connect('toggled', self._parent.enable_save, True)
		self._checkbox_tab_close_button.connect('toggled', self._parent.enable_save)
		self._checkbox_always_show_tabs.connect('toggled', self._parent.enable_save)
		self._checkbox_ubuntu_coloring.connect('toggled', self._parent.enable_save)
		self._checkbox_superuser_notification.connect('toggled', self._parent.enable_save)

		# status bar
		table = gtk.Table(2, 2, False)
		table.set_col_spacing(0, 5)
		table.set_row_spacings(5)

		label_status_bar = gtk.Label(_('Show status bar:'))
		label_status_bar.set_alignment(0, 0.5)

		list_status_bar = gtk.ListStore(str, int)
		list_status_bar.append((_('Always'), StatusVisible.ALWAYS))
		list_status_bar.append((_('When needed'), StatusVisible.WHEN_NEEDED))
		list_status_bar.append((_('Never'), StatusVisible.NEVER))

		cell_status_bar = gtk.CellRendererText()

		self._combobox_status_bar = gtk.ComboBox(list_status_bar)
		self._combobox_status_bar.connect('changed', self._parent.enable_save)
		self._combobox_status_bar.pack_start(cell_status_bar)
		self._combobox_status_bar.add_attribute(cell_status_bar, 'text', 0)

		# expand tabs
		label_expand_tab = gtk.Label(_('Expanded tabs:'))
		label_expand_tab.set_alignment(0, 0.5)

		list_expand_tab = gtk.ListStore(str, int)
		list_expand_tab.append((_('None'), TabExpand.NONE))
		list_expand_tab.append((_('Active'), TabExpand.ACTIVE))
		list_expand_tab.append((_('All'), TabExpand.ALL))

		cell_expand_tab = gtk.CellRendererText()

		self._combobox_expand_tabs = gtk.ComboBox(list_expand_tab)
		self._combobox_expand_tabs.connect('changed', self._parent.enable_save)
		self._combobox_expand_tabs.pack_start(cell_expand_tab)
		self._combobox_expand_tabs.add_attribute(cell_expand_tab, 'text', 0)

		# other options
		label_other = gtk.Label(_('Other'))
		vbox_other = gtk.VBox(False, 0)
		vbox_other.set_border_width(5)

		self._checkbox_hide_window_on_minimize = gtk.CheckButton(_('Hide operation window on minimize'))
		self._checkbox_show_notifications = gtk.CheckButton(_('Show notifications'))
		self._checkbox_network_path_completion = gtk.CheckButton(_('Use path completion on non-local paths'))

		self._checkbox_hide_window_on_minimize.connect('toggled', self._parent.enable_save)
		self._checkbox_show_notifications.connect('toggled', self._parent.enable_save)
		self._checkbox_network_path_completion.connect('toggled', self._parent.enable_save)

		# size format
		hbox_size_format = gtk.HBox(False, 5)
		label_size_format = gtk.Label(_('Size format:'))
		label_size_format.set_alignment(0, 0.5)

		list_size_format = gtk.ListStore(str, int)
		list_size_format.append((_('Localized'), SizeFormat.LOCAL))
		list_size_format.append((_('SI <small>(1 kB = 1000 B)</small>'), SizeFormat.SI))
		list_size_format.append((_('IEC <small>(1 KiB = 1024 B)</small>'), SizeFormat.IEC))

		cell_size_format = gtk.CellRendererText()

		self._combobox_size_format = gtk.ComboBox(list_size_format)
		self._combobox_size_format.connect('changed', self._parent.enable_save)
		self._combobox_size_format.pack_start(cell_size_format)
		self._combobox_size_format.add_attribute(cell_size_format, 'markup', 0)

		# pack ui
		hbox_size_format.pack_start(label_size_format, False, False, 0)
		hbox_size_format.pack_start(self._combobox_size_format, False, False, 0)

		table.attach(label_status_bar, 0, 1, 0, 1, xoptions=gtk.FILL)
		table.attach(self._combobox_status_bar, 1, 2, 0, 1, xoptions=gtk.FILL)

		table.attach(label_expand_tab, 0, 1, 1, 2, xoptions=gtk.FILL)
		table.attach(self._combobox_expand_tabs, 1, 2, 1, 2, xoptions=gtk.FILL)

		vbox_main_window.pack_start(self._checkbox_hide_on_close, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_multiple_instances, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_toolbar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_bar, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_show_command_entry, False, False, 0)
		vbox_main_window.pack_start(self._checkbox_horizontal_split, False, False, 0)

		vbox_tabs.pack_start(self._checkbox_focus_new_tab, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_button_relief, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_button_icons, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_tab_close_button, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_always_show_tabs, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_ubuntu_coloring, False, False, 0)
		vbox_tabs.pack_start(self._checkbox_superuser_notification, False, False, 0)
		vbox_tabs.pack_start(table, False, False, 5)

		vbox_other.pack_start(self._checkbox_hide_window_on_minimize, False, False, 0)
		vbox_other.pack_start(self._checkbox_show_notifications, False, False, 0)
		vbox_other.pack_start(self._checkbox_network_path_completion, False, False, 0)
		vbox_other.pack_start(hbox_size_format, False, False, 0)

		notebook.append_page(vbox_main_window, label_main_window)
		notebook.append_page(vbox_tabs, label_tabs)
		notebook.append_page(vbox_other, label_other)

		self.pack_start(notebook, True, True, 0)

	def _load_options(self):
		"""Load display options"""
		options = self._application.options
		window_options = self._application.window_options

		self._checkbox_hide_on_close.set_active(window_options.section('main').get('hide_on_close'))
		self._checkbox_multiple_instances.set_active(options.get('multiple_instances'))
		self._checkbox_focus_new_tab.set_active(options.get('focus_new_tab'))
		self._checkbox_show_toolbar.set_active(options.get('show_toolbar'))
		self._checkbox_show_command_bar.set_active(options.get('show_command_bar'))
		self._checkbox_show_command_entry.set_active(options.get('show_command_entry'))
		self._checkbox_button_relief.set_active(options.get('button_relief'))
		self._checkbox_button_icons.set_active(options.get('tab_button_icons'))
		self._checkbox_tab_close_button.set_active(options.get('tab_close_button'))
		self._checkbox_always_show_tabs.set_active(options.get('always_show_tabs'))
		self._checkbox_ubuntu_coloring.set_active(options.get('ubuntu_coloring'))
		self._checkbox_superuser_notification.set_active(options.get('superuser_notification'))
		self._checkbox_hide_window_on_minimize.set_active(options.section('operations').get('hide_on_minimize'))
		self._checkbox_show_notifications.set_active(options.get('show_notifications'))
		self._checkbox_network_path_completion.set_active(options.get('network_path_completion'))
		self._combobox_status_bar.set_active(options.get('show_status_bar'))
		self._combobox_expand_tabs.set_active(options.get('expand_tabs'))
		self._combobox_size_format.set_active(options.get('size_format'))
		self._checkbox_horizontal_split.set_active(options.get('horizontal_split'))

	def _save_options(self):
		"""Save display options"""
		options = self._application.options
		window_options = self._application.window_options

		# save options
		window_options.section('main').set('hide_on_close', self._checkbox_hide_on_close.get_active())
		options.set('multiple_instances', self._checkbox_multiple_instances.get_active())
		options.set('focus_new_tab', self._checkbox_focus_new_tab.get_active())
		options.set('show_toolbar', self._checkbox_show_toolbar.get_active())
		options.set('show_command_bar', self._checkbox_show_command_bar.get_active())
		options.set('show_command_entry', self._checkbox_show_command_entry.get_active())
		options.set('button_relief', self._checkbox_button_relief.get_active())
		options.set('tab_button_icons', self._checkbox_button_icons.get_active())
		options.set('tab_close_button', self._checkbox_tab_close_button.get_active())
		options.set('always_show_tabs', self._checkbox_always_show_tabs.get_active())
		options.set('ubuntu_coloring', self._checkbox_ubuntu_coloring.get_active())
		options.set('superuser_notification', self._checkbox_superuser_notification.get_active())
		options.section('operations').set('hide_on_minimize', self._checkbox_hide_window_on_minimize.get_active())
		options.set('show_notifications', self._checkbox_show_notifications.get_active())
		options.set('network_path_completion', self._checkbox_network_path_completion.get_active())
		options.set('show_status_bar', self._combobox_status_bar.get_active())
		options.set('expand_tabs', self._combobox_expand_tabs.get_active())
		options.set('size_format', self._combobox_size_format.get_active())
		options.set('horizontal_split', self._checkbox_horizontal_split.get_active())
