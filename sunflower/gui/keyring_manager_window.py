import time

from gi.repository import Gtk
from .input_dialog import PasswordDialog


class Column:
	ID = 0
	NAME = 1
	MODIFIED = 2


class KeyringManagerWindow:
	"""Keyring manager window is used to give user control over
	passwords stored in our own keyring.

	"""

	def __init__(self, application):
		self._application = application
		self._active_keyring = application.keyring_manager.KEYRING_NAME

		# create window
		self._window = Gtk.Window(Gtk.WindowType.TOPLEVEL)

		# configure window
		self._window.set_title(_('Keyring manager'))
		self._window.set_size_request(500, 300)
		self._window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self._window.set_skip_taskbar_hint(False)
		self._window.set_modal(False)
		self._window.set_wmclass('Sunflower', 'Sunflower')
		self._window.set_border_width(7)

		# connect signals
		self._window.connect('delete-event', self.__delete_event)

		# create user interface
		vbox = Gtk.VBox(homogeneous=False, spacing=5)
		container = Gtk.ScrolledWindow()
		container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		container.set_shadow_type(Gtk.ShadowType.IN)

		self._store = Gtk.ListStore(long, str, str)
		self._list = Gtk.TreeView(model=self._store)

		cell_id = Gtk.CellRendererText()
		cell_name = Gtk.CellRendererText()
		cell_modified = Gtk.CellRendererText()

		col_id = Gtk.TreeViewColumn(_('ID'), cell_id, text=Column.ID)
		col_name = Gtk.TreeViewColumn(_('Name'), cell_name, text=Column.NAME)
		col_name.set_expand(True)
		col_modified = Gtk.TreeViewColumn(_('Modified'), cell_modified, text=Column.MODIFIED)

		self._list.append_column(col_id)
		self._list.append_column(col_name)
		self._list.append_column(col_modified)

		# create controls
		hbox = Gtk.HBox(homogeneous=False, spacing=5)

		button_edit = Gtk.Button(stock=Gtk.STOCK_EDIT)
		button_edit.connect('clicked', self.__edit_selected)

		button_delete = Gtk.Button(stock=Gtk.STOCK_DELETE)
		button_delete.connect('clicked', self.__delete_selected)

		button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
		button_close.connect('clicked', self.__handle_close)

		# pack components
		hbox.pack_start(button_edit, False, False, 0)
		hbox.pack_start(button_delete, False, False, 0)
		hbox.pack_end(button_close, False, False, 0)

		container.add(self._list)

		vbox.pack_start(container, True, True, 0)
		vbox.pack_start(hbox, False, False, 0)

		self._window.add(vbox)

		# populate list
		self.__populate_list()

		# show window
		self._window.show_all()

	def __populate_list(self, keyring_name=None):
		"""Populate list with items from specified keyring"""
		if keyring_name is not None:
			self._active_keyring = keyring_name

		self._store.clear()

		section = self._application.options.section('item_list')
		keyring_manager = self._application.keyring_manager
		time_format = section.get('time_format')

		for uid, name, modified in keyring_manager.get_entries():
			formatted_time = time.strftime(time_format, time.localtime(modified))
			self._store.append((uid, name, formatted_time))

	def __delete_event(self, widget, data=None):
		"""Cleanup on window delete event"""
		self._application.keyring_manager.lock_keyring()

	def __handle_close(self, widget, data=None):
		"""Handle clicking on close button"""
		self._application.keyring_manager.lock_keyring()
		self._window.destroy()
		return True

	def __delete_selected(self, widget, data=None):
		"""Delete selected entry in keyring"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# show error if no entry is selected
		if selected_iter is None:
			dialog = Gtk.MessageDialog(
									self._window,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Please select an entry to delete!')
								)
			dialog.run()
			dialog.destroy()
			return True

		# get data, we'll need them later
		entry_name = item_list.get_value(selected_iter, Column.NAME)

		# ask confirmation from user
		dialog = Gtk.MessageDialog(
								self._window,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.WARNING,
								Gtk.ButtonsType.YES_NO,
								_(
									'You are about to remove the following '
									'entry from your keyring. If you do this '
									'you will have to provide password '
									'manually when needed. Are you sure?\n\n{0}'
								).format(entry_name)
							)
		dialog.set_default_response(Gtk.ResponseType.YES)
		response = dialog.run()
		dialog.destroy()

		if response == Gtk.ResponseType.YES:
			self._application.keyring_manager.remove_entry(entry_name)
			self.__populate_list()

		return True

	def __edit_selected(self, widget, data=None):
		"""Edit selected entry in keyring"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# show error if no entry is selected
		if selected_iter is None:
			dialog = Gtk.MessageDialog(
									self._window,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.WARNING,
									Gtk.ButtonsType.OK,
									_('Please select an entry to change!')
								)
			dialog.run()
			dialog.destroy()
			return True

		dialog = PasswordDialog(self._window)
		dialog.set_title(_('Change password'))
		dialog.set_label(_('Enter new password for selected keyring entry.'))

		response = dialog.get_response()

		if response[0] == Gtk.ResponseType.OK:
			if response[1] == response[2]:
				# passwords match, change value
				item_id = item_list.get_value(selected_iter, Column.ID)
				self._application.keyring_manager.change_secret(item_id, response[1])

				dialog = Gtk.MessageDialog(
										self._window,
										Gtk.DialogFlags.DESTROY_WITH_PARENT,
										Gtk.MessageType.INFO,
										Gtk.ButtonsType.OK,
										_('Password was changed!')
									)
				dialog.run()
				dialog.destroy()

				# refresh list
				self.__populate_list()

			else:
				# passwords don't match, notify user
				dialog = Gtk.MessageDialog(
										self._window,
										Gtk.DialogFlags.DESTROY_WITH_PARENT,
										Gtk.MessageType.ERROR,
										Gtk.ButtonsType.OK,
										_('Passwords do not match! Please try again.')
									)
				dialog.run()
				dialog.destroy()

		return True
