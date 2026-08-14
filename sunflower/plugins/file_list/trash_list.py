from gi.repository import Gtk

from .file_list import FileList
from .gio_provider import TrashProvider
from sunflower.operation import DeleteOperation


class TrashList(FileList):
	"""Trash file list plugin

	Generic operations related to trash management are provided with this
	class. By extending FileList standard features such as drag and drop are
	supported.

	"""

	def __init__(self, parent, notebook, options):
		FileList.__init__(self, parent, notebook, options)

	def _create_buttons(self):
		"""Create titlebar buttons."""
		options = self._parent.options

		# empty trash button
		if Gtk.get_major_version() == 3:
			self._empty_button = Gtk.Button.new_from_icon_name('user-trash-symbolic', Gtk.IconSize.MENU)

		else:
			self._empty_button = Gtk.Button.new_from_icon_name('user-trash-symbolic')
		self._empty_button.set_focus_on_click(False)
		self._empty_button.set_tooltip_text(_('Empty trash'))
		self._empty_button.connect('clicked', self.empty_trash)
		self._title_bar.add_control(self._empty_button)

	def empty_trash(self, widget=None, data=None):
		"""Empty trash can."""
		# ask user to confirm
		dialog = Gtk.MessageDialog(
								transient_for=self._parent,
								destroy_with_parent=True,
								message_type=Gtk.MessageType.QUESTION,
								buttons=Gtk.ButtonsType.YES_NO,
								text=_(
									"All items in the Trash will be permanently deleted. "
									"Are you sure?"
								)
							)
		dialog.set_default_response(Gtk.ResponseType.YES)
		result = run_dialog(dialog)
		dialog.destroy()

		# remove all items in trash
		if result == Gtk.ResponseType.YES:
			provider = self.get_provider()
			root_path = provider.get_root_path(None)

			# create delete operation
			operation = DeleteOperation(
									self._parent,
									provider
								)

			operation.set_force_delete(True)
			# items are top level trash entries, resolve them against the
			# trash root instead of the currently displayed directory
			operation.set_source_path(root_path)
			operation.set_selection(provider.list_dir(root_path))

			# perform removal
			operation.start()

	def change_path(self, path=None, selected=None):
		"""Change file list path."""
		if path is not None and not path.startswith('trash://'):
			path = 'trash:///'

		FileList.change_path(self, path, selected)
