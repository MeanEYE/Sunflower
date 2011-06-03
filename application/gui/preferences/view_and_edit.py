import gtk

from widgets.settings_page import SettingsPage


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

		# external options
		radio_external = gtk.RadioButton(label=_('Use external editor'))

		vbox_external = gtk.VBox(False, 0)
		vbox_external.set_border_width(10)

		label_editor = gtk.Label(_('Command line:'))
		label_editor.set_alignment(0, 0.5)
		label_editor.set_use_markup(True)
		self._entry_editor = gtk.Entry()
		self._entry_editor.connect('activate', self._parent.enable_save)

		self._checkbox_wait_for_editor = gtk.CheckButton(_('Wait for editor process to end'))
		self._checkbox_wait_for_editor.connect('toggled', self._parent.enable_save)

		# internal options
		radio_internal = gtk.RadioButton(
									group=radio_external,
									label=_('Use internal editor') + ' (not implemented)'
								)
		radio_internal.set_sensitive(False)

		vbox_internal = gtk.VBox(False, 0)
		vbox_internal.set_border_width(5)

		# pack ui
		vbox_external.pack_start(label_editor, False, False, 0)
		vbox_external.pack_start(self._entry_editor, False, False, 0)
		vbox_external.pack_start(self._checkbox_wait_for_editor, False, False, 0)

		vbox_edit.pack_start(radio_external, False, False, 0)
		vbox_edit.pack_start(vbox_external, False, False, 0)
		vbox_edit.pack_start(radio_internal, False, False, 0)
		vbox_edit.pack_start(vbox_internal, False, False, 0)

		frame_view.add(label_not_implemented)
		frame_edit.add(vbox_edit)

		self.pack_start(frame_view, False, False, 0)
		self.pack_start(frame_edit, False, False, 0)

	def _load_options(self):
		"""Load options"""
		options = self._application.options

		self._entry_editor.set_text(options.get('main', 'default_editor'))
		self._checkbox_wait_for_editor.set_active(options.getboolean('main', 'wait_for_editor'))

	def _save_options(self):
		"""Save options"""
		options = self._application.options
		bool = ('False', 'True')

		options.set('main', 'default_editor', self._entry_editor.get_text())
		options.set('main', 'wait_for_editor', bool[self._checkbox_wait_for_editor.get_active()])
