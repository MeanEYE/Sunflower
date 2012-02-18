import gtk

from widgets.settings_page import SettingsPage


class TerminalOptions(SettingsPage):
	"""Terminal options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'terminal', _('Terminal'))

		# create vte terminal options
		align_vte = gtk.Alignment(xscale=1)
		align_vte.set_padding(0, 10, 15, 15)
		self._vbox_vte = gtk.VBox(False, 5)

		self._radio_vte = gtk.RadioButton(label=_('VTE based terminal'))
		self._radio_vte.connect('toggled', self._parent.enable_save)

		self._checkbox_scrollbars_visible = gtk.CheckButton(_('Show scrollbars when needed'))
		self._checkbox_scrollbars_visible.connect('toggled', self._parent.enable_save)

		# create external terminal options
		align_external = gtk.Alignment(xscale=1)
		align_external.set_padding(0, 0, 15, 15)
		self._vbox_external = gtk.VBox(False, 5)

		self._radio_external = gtk.RadioButton(group=self._radio_vte, label=_('External terminal'))

		vbox_command = gtk.VBox(False, 0)
		label_command = gtk.Label(_('Command line:'))
		label_command.set_alignment(0, 0.5)
		self._entry_command = gtk.Entry()
		self._entry_command.connect('changed', self._parent.enable_save)

		label_note = gtk.Label(_(
					'<small><i>Note: {0} will be replaced with socket/window id.'
					'\nXterm has problems with embeding so it might not work.</i></small>'
				));
		label_note.set_alignment(0, 0)
		label_note.set_use_markup(True)

		# pack interface
		vbox_command.pack_start(label_command, False, False, 0)
		vbox_command.pack_start(self._entry_command, False, False, 0)
		vbox_command.pack_start(label_note, False, False, 0)

		self._vbox_vte.pack_start(self._checkbox_scrollbars_visible, False, False, 0)

		self._vbox_external.pack_start(vbox_command, False, False, 0)

		align_vte.add(self._vbox_vte)
		align_external.add(self._vbox_external)

		self.pack_start(self._radio_vte, False, False, 0)
		self.pack_start(align_vte, False, False, 0)
		self.pack_start(self._radio_external, False, False, 0)
		self.pack_start(align_external, False, False, 0)

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options

		self._checkbox_scrollbars_visible.set_active(options.getboolean('main', 'terminal_scrollbars'))
		self._entry_command.set_text(options.get('main', 'terminal_command'))

		# apply terminal type
		terminal_type = options.getint('main', 'terminal_type')
		if terminal_type == 0:
			self._radio_vte.set_active(True)

		else:
			self._radio_external.set_active(True)

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options
		_bool = ('False', 'True')

		options.set('main', 'terminal_scrollbars', _bool[self._checkbox_scrollbars_visible.get_active()])
		options.set('main', 'terminal_command', self._entry_command.get_text())

		# save terminal type
		terminal_type = 0 if self._radio_vte.get_active() else 1
		options.set('main', 'terminal_type', terminal_type)
