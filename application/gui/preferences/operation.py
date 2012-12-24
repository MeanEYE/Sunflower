import gtk

from widgets.settings_page import SettingsPage


class OperationOptions(SettingsPage):
	"""Operation options extension class"""
	
	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'operation', _('Operation'))

		# create frames
		frame_general = gtk.Frame(_('General'))
		vbox_general = gtk.VBox(False, 0)
		vbox_general.set_border_width(5)

		frame_mounts = gtk.Frame(_('Mounts'))
		vbox_mounts = gtk.VBox(False, 0)
		vbox_mounts.set_border_width(5)

		frame_confirmations = gtk.Frame(_('Confirmation'))
		vbox_confirmations = gtk.VBox(False, 0)
		vbox_confirmations.set_border_width(5)

		# create components
		self._checkbox_trash_files = gtk.CheckButton(_('Delete items to trashcan'))
		self._checkbox_reserve_size = gtk.CheckButton(_('Reserve free space on copy/move'))
		self._checkbox_automount_on_start = gtk.CheckButton(_('Automount drives on start up'))
		self._checkbox_automount_on_insert = gtk.CheckButton(_('Automount removable drives when inserted'))
		self._checkbox_confirm_delete = gtk.CheckButton(_('Show confirmation dialog before deleting items'))

		self._checkbox_trash_files.connect('toggled', self._parent.enable_save)
		self._checkbox_reserve_size.connect('toggled', self._parent.enable_save)
		self._checkbox_automount_on_start.connect('toggled', self._parent.enable_save)
		self._checkbox_automount_on_insert.connect('toggled', self._parent.enable_save)
		self._checkbox_confirm_delete.connect('toggled', self._confirm_delete_toggle)

		# pack user interface
		vbox_general.pack_start(self._checkbox_trash_files, False, False, 0)
		vbox_general.pack_start(self._checkbox_reserve_size, False, False, 0)

		vbox_mounts.pack_start(self._checkbox_automount_on_start, False, False, 0)
		vbox_mounts.pack_start(self._checkbox_automount_on_insert, False, False, 0)

		vbox_confirmations.pack_start(self._checkbox_confirm_delete, False, False, 0)

		frame_general.add(vbox_general)
		frame_mounts.add(vbox_mounts)
		frame_confirmations.add(vbox_confirmations)

		self.pack_start(frame_general, False, False, 0)
		self.pack_start(frame_mounts, False, False, 0)
		self.pack_start(frame_confirmations, False, False, 0)

	def _confirm_delete_toggle(self, widget, data=None):
		"""Make sure user really wants to disable confirmation dialog"""
		if not widget.get_active() and not self._checkbox_trash_files.get_active():
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_QUESTION,
									gtk.BUTTONS_YES_NO,
									_(
										'With trashing disabled you will not be able to '
										'restore accidentally deleted items. Are you sure '
										'you want to disable confirmation dialog when '
										'deleting items?'
									)
								)
			dialog.set_default_response(gtk.RESPONSE_YES)
			result = dialog.run()
			dialog.destroy()

			if result == gtk.RESPONSE_NO:
				# user changed his mind, restore original value
				widget.handler_block_by_func(self._confirm_delete_toggle)
				widget.set_active(True)
				widget.handler_unblock_by_func(self._confirm_delete_toggle)

			else:
				# user really wants to disable this option
				self._parent.enable_save(widget, data)

		else:
			# normal operation, just notify parent
			self._parent.enable_save(widget, data)


	def _load_options(self):
		"""Load item list options"""
		options = self._application.options
		operations = options.section('operations')
		confirmations = options.section('confirmations')

		# load options
		self._checkbox_trash_files.set_active(operations.get('trash_files'))
		self._checkbox_reserve_size.set_active(operations.get('reserve_size'))
		self._checkbox_automount_on_start.set_active(operations.get('automount_start'))
		self._checkbox_automount_on_insert.set_active(operations.get('automount_insert'))
		self._checkbox_confirm_delete.set_active(confirmations.get('delete_items'))

	def _save_options(self):
		"""Save item list options"""
		options = self._application.options
		operations = options.section('operations')
		confirmations = options.section('confirmations')

		# save settings
		operations.set('trash_files', self._checkbox_trash_files.get_active())
		operations.set('reserve_size', self._checkbox_reserve_size.get_active())
		operations.set('automount_start', self._checkbox_automount_on_start.get_active())
		operations.set('automount_insert', self._checkbox_automount_on_insert.get_active())
		confirmations.set('delete_items', self._checkbox_confirm_delete.get_active())
