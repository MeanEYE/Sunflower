import gtk


class SambaCreate:

	def __init__(self, parent):
		self._dialog = gtk.Dialog(parent=parent)

		# configure dialog
		self.set_title(_('Create Samba mount'))
		self._dialog.set_default_size(340, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		self._dialog.vbox.set_spacing(0)
		self._dialog.set_default_response(gtk.RESPONSE_OK)

		# create user interface
		self._container = gtk.VBox(False, 5)
		self._container.set_border_width(5)

		vbox_name = gtk.VBox(False, 0)

		label_name = gtk.Label(_('Name:'))
		label_name.set_alignment(0, 0.5)
		self._entry_name = gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)

		hseparator = gtk.HSeparator()

		vbox_server = gtk.VBox(False, 0)

		label_server = gtk.Label(_('Server:'))
		label_server.set_alignment(0, 0.5)
		self._entry_server = gtk.Entry()
		self._entry_server.connect('activate', self._confirm_entry)

		# create controls
		button_save = gtk.Button(stock=gtk.STOCK_SAVE)
		button_save.connect('clicked', self._confirm_entry)
		button_save.set_can_default(True)

		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

		# pack user interface
		vbox_name.pack_start(label_name, False, False, 0)
		vbox_name.pack_start(self._entry_name, False, False, 0)

		self._container.pack_start(vbox_name, False, False, 0)
		self._container.pack_start(hseparator, False, False, 0)
		self._container.pack_start(vbox_server, False, False, 0)

		self._dialog.action_area.pack_end(button_save, False, False, 0)
		self._dialog.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)

		self._dialog.vbox.pack_start(self._container, True, True, 0)
		self._dialog.show_all()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		self._dialog.response(gtk.RESPONSE_OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = self._dialog.run()
		result = None

		self._dialog.destroy()

		return (code, result)
