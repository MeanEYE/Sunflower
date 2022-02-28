from gi.repository import Gtk
from sunflower.widgets.settings_page import SettingsPage
from sunflower.plugin_base.terminal import TerminalType, CursorShape


class TerminalOptions(SettingsPage):
	"""Terminal options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'terminal', _('Terminal'))

		# create vte terminal options
		vbox_vte = Gtk.VBox.new(False, 0)
		self._radio_vte = self._create_radio_section(_('VTE based terminal'), vbox_vte)
		self._radio_vte.connect('toggled', self._parent.enable_save)

		# option for showing scrollbars
		self._checkbox_scrollbars_visible = Gtk.CheckButton(_('Show scrollbars when needed'))
		self._checkbox_scrollbars_visible.connect('toggled', self._parent.enable_save)

		# option for custom font
		hbox_font = Gtk.HBox.new(False, 5)

		self._checkbox_system_font = Gtk.CheckButton(_('Use the system fixed width font'))
		self._checkbox_system_font.connect('toggled', self.__toggled_system_font)

		label_font = Gtk.Label(label=_('Font:'))
		label_font.set_alignment(0, 0.5)

		self._button_font = Gtk.FontButton()
		self._button_font.connect('font-set', self._parent.enable_save)

		# option for cursor shape
		hbox_cursor_shape = Gtk.HBox(False, 5)

		label_cursor_shape = Gtk.Label(label=_('Cursor shape:'))
		label_cursor_shape.set_alignment(0, 0.5)

		list_cursor_shape = Gtk.ListStore(str, int)
		list_cursor_shape.append((_('Block'), CursorShape.BLOCK))
		list_cursor_shape.append((_('I-Beam'), CursorShape.IBEAM))
		list_cursor_shape.append((_('Underline'), CursorShape.UNDERLINE))

		cell_cursor_shape = Gtk.CellRendererText()

		self._combobox_cursor_shape = Gtk.ComboBox(model=list_cursor_shape)
		self._combobox_cursor_shape.connect('changed', self._parent.enable_save)
		self._combobox_cursor_shape.pack_start(cell_cursor_shape, True)
		self._combobox_cursor_shape.add_attribute(cell_cursor_shape, 'text', 0)

		# option for allowing bold text in terminal
		self._checkbox_allow_bold = Gtk.CheckButton(_('Allow bold text'))
		self._checkbox_allow_bold.connect('toggled', self._parent.enable_save)

		# option for automatically hiding mouse when typing
		self._checkbox_autohide_mouse = Gtk.CheckButton(_('Automatically hide mouse when typing'))
		self._checkbox_autohide_mouse.connect('toggled', self._parent.enable_save)

		# create external terminal options
		vbox_external = Gtk.VBox(False, 5)
		self._radio_external = self._create_radio_section(
				_('External terminal'),
				vbox_external,
				self._radio_vte
				)

		vbox_command = Gtk.VBox(False, 0)
		label_command = Gtk.Label(label=_('Command line:'))
		label_command.set_alignment(0, 0.5)
		self._entry_command = Gtk.Entry()
		self._entry_command.connect('changed', self._parent.enable_save)

		vbox_command2 = Gtk.VBox(False, 0)
		label_command2 = Gtk.Label(label=_('Command line for executing specific program:'))
		label_command2.set_alignment(0, 0.5)
		self._entry_command2 = Gtk.Entry()
		self._entry_command2.connect('changed', self._parent.enable_save)

		label_note = Gtk.Label(label=_(
					'<small><i>Note:'
					'\n\tOmitting {0} will open new terminal application instead of tab.'
					'\n\t{0} will be replaced with socket/window id.'
					'\n\t{1} will be replaced with specified command and its parameters.'
					'\n\t{2} will be replaced with current working directory.'
					'</i></small>'
				))
		label_note.set_alignment(0, 0)
		label_note.set_use_markup(True)

		# pack interface
		hbox_font.pack_start(label_font, False, False, 0)
		hbox_font.pack_start(self._button_font, True, True, 0)

		hbox_cursor_shape.pack_start(label_cursor_shape, False, False, 0)
		hbox_cursor_shape.pack_start(self._combobox_cursor_shape, False, False, 0)

		vbox_command.pack_start(label_command, False, False, 0)
		vbox_command.pack_start(self._entry_command, False, False, 0)
		vbox_command2.pack_start(label_command2, False, False, 0)
		vbox_command2.pack_start(self._entry_command2, False, False, 0)

		vbox_vte.pack_start(self._checkbox_scrollbars_visible, False, False, 0)
		vbox_vte.pack_start(self._checkbox_system_font, False, False, 0)
		vbox_vte.pack_start(hbox_font, False, False, 0)
		vbox_vte.pack_start(hbox_cursor_shape, False, False, 5)
		vbox_vte.pack_start(self._checkbox_allow_bold, False, False, 0)
		vbox_vte.pack_start(self._checkbox_autohide_mouse, False, False, 0)

		vbox_external.pack_start(vbox_command, False, False, 0)
		vbox_external.pack_start(vbox_command2, False, False, 0)
		vbox_external.pack_start(label_note, False, False, 0)

	def __toggled_system_font(self, widget, data=None):
		"""Handle toggle of system font checkbox"""
		self._parent.enable_save()

	def _load_options(self):
		"""Load terminal tab options"""
		options = self._application.options.section('terminal')

		self._checkbox_scrollbars_visible.set_active(options.get('show_scrollbars'))
		self._entry_command.set_text(options.get('command'))
		self._entry_command2.set_text(options.get('command2'))
		self._checkbox_system_font.set_active(options.get('use_system_font'))
		self._combobox_cursor_shape.set_active(options.get('cursor_shape'))
		self._checkbox_allow_bold.set_active(options.get('allow_bold'))
		self._checkbox_autohide_mouse.set_active(options.get('mouse_autohide'))
		self._button_font.set_font_name(options.get('font'))

		# apply terminal type
		terminal_type = options.get('type')
		if terminal_type == TerminalType.VTE:
			self._radio_vte.set_active(True)

		else:
			self._radio_external.set_active(True)

	def _save_options(self):
		"""Save terminal tab options"""
		options = self._application.options.section('terminal')

		options.set('show_scrollbars', self._checkbox_scrollbars_visible.get_active())
		options.set('command', self._entry_command.get_text())
		options.set('command2', self._entry_command2.get_text())
		options.set('use_system_font', self._checkbox_system_font.get_active())
		options.set('cursor_shape', self._combobox_cursor_shape.get_active())
		options.set('allow_bold', self._checkbox_allow_bold.get_active())
		options.set('mouse_autohide', self._checkbox_autohide_mouse.get_active())
		options.set('font', self._button_font.get_font_name())

		# save terminal type
		terminal_type = TerminalType.VTE if self._radio_vte.get_active() else TerminalType.EXTERNAL
		options.set('type', terminal_type)
