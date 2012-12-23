import gtk

from widgets.settings_page import SettingsPage


class Column:
	ICON = 0
	NAME = 1
	COMMAND = 2


class ViewEditOptions(SettingsPage):
	"""View & Edit options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'view_and_edit', _('View & Edit'))

		# viewer options
		frame_view = gtk.Frame(_('View'))

		label_not_implemented = gtk.Label('This option is not implemented yet.')
		label_not_implemented.set_sensitive(False)

		# editor options
		frame_edit = gtk.Frame(_('Edit'))

		vbox_edit = gtk.VBox(False, 0)
		vbox_edit.set_border_width(5)

		# installed application
		self._radio_application = gtk.RadioButton(label=_('Use installed application'))
		self._radio_application.connect('toggled', self._parent.enable_save)

		align_application = gtk.Alignment(xscale=1)
		align_application.set_padding(0, 10, 15, 15)
		vbox_application = gtk.VBox(False, 0)
		vbox_application.set_border_width(5)

		self._store = gtk.ListStore(str, str, str)
		self._combobox_application = gtk.ComboBox(model=self._store)
		self._combobox_application.connect('changed', self._parent.enable_save)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()

		self._combobox_application.pack_start(cell_icon, False)
		self._combobox_application.pack_start(cell_name, True)

		self._combobox_application.add_attribute(cell_icon, 'icon-name', Column.ICON)
		self._combobox_application.add_attribute(cell_name, 'text', Column.NAME)

		# external options
		self._radio_external = gtk.RadioButton(group=self._radio_application, label=_('Use external command'))
		self._radio_external.connect('toggled', self._parent.enable_save)

		align_external = gtk.Alignment(xscale=1)
		align_external.set_padding(0, 10, 15, 15)
		vbox_external = gtk.VBox(False, 0)
		vbox_external.set_border_width(5)

		label_editor = gtk.Label(_('Command line:'))
		label_editor.set_alignment(0, 0.5)
		label_editor.set_use_markup(True)
		self._entry_editor = gtk.Entry()
		self._entry_editor.connect('changed', self._parent.enable_save)

		self._checkbox_terminal_command = gtk.CheckButton(_('Execute command in terminal tab'))
		self._checkbox_terminal_command.connect('toggled', self._parent.enable_save)

		# pack ui
		vbox_application.pack_start(self._combobox_application, False, False, 0)
		align_application.add(vbox_application)

		vbox_external.pack_start(label_editor, False, False, 0)
		vbox_external.pack_start(self._entry_editor, False, False, 0)
		vbox_external.pack_start(self._checkbox_terminal_command, False, False, 0)
		align_external.add(vbox_external)

		vbox_edit.pack_start(self._radio_application, False, False, 0)
		vbox_edit.pack_start(align_application, False, False, 0)
		vbox_edit.pack_start(self._radio_external, False, False, 0)
		vbox_edit.pack_start(align_external, False, False, 0)

		frame_view.add(label_not_implemented)
		frame_edit.add(vbox_edit)

		self.pack_start(frame_view, False, False, 0)
		self.pack_start(frame_edit, False, False, 0)

	def _populate_list(self, selected_application):
		"""Populate list of applications available for editing"""
		self._store.clear()

		selected_index = None
		application_list = self._application.associations_manager.get_application_list_for_type('text/plain')

		for application in application_list:
			# if names match store index for later use
			if application.name == selected_application:
				selected_index = len(self._store)

			# add application to the list
			self._store.append((
					application.icon,
					application.name,
					application.command_line
				))

		# make selected aplication active
		if selected_index is not None:
			self._combobox_application.set_active(selected_index)

	def _load_options(self):
		"""Load options"""
		options = self._application.options.section('editor')

		# populate application list
		self._populate_list(options.get('application'))

		# select proper radio button
		if options.get('type') == 0:
			self._radio_application.set_active(True)

		else:
			self._radio_external.set_active(True)

		# configure user interface
		editor_command = options.get('external_command')
		if editor_command is not None:
			self._entry_editor.set_text(editor_command)

		self._checkbox_terminal_command.set_active(options.get('terminal_command'))

	def _save_options(self):
		"""Save options"""
		options = self._application.options.section('editor')

		# get external command
		external_command = self._entry_editor.get_text()

		# get selected application
		selected_index = self._combobox_application.get_active()
		application_name = None
		application_command = None
		
		if selected_index > -1:
			row = self._store[selected_index]
			application_name = row[Column.NAME]
			application_command = row[Column.COMMAND]

		# get command based
		editor_type = 0 if self._radio_application.get_active() else 1
		command = application_command if editor_type == 0 else external_command

		# store options to config
		options.set('type', editor_type)
		options.set('default_editor', command)
		options.set('application', application_name)
		options.set('external_command', external_command)
		options.set('terminal_command', self._checkbox_terminal_command.get_active())
