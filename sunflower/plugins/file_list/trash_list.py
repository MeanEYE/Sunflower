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
		self._empty_button = Gtk.Button.new_from_icon_name('user-trash-symbolic', Gtk.IconSize.MENU)
		self._empty_button.set_focus_on_click(False)
		self._empty_button.set_tooltip_text(_('Empty trash'))
		self._empty_button.connect('clicked', self.empty_trash)
		self._title_bar.add_control(self._empty_button)

	def empty_trash(self, widget=None, data=None):
		"""Empty trash can."""
		# ask user to confirm
		dialog = Gtk.MessageDialog(
								self._parent,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.QUESTION,
								Gtk.ButtonsType.YES_NO,
								_(
									"All items in the Trash will be permanently deleted. "
									"Are you sure?"
								)
							)
		dialog.set_default_response(Gtk.ResponseType.YES)
		result = dialog.run()
		dialog.destroy()

		# remove all items in trash
		if result == Gtk.ResponseType.YES:
			provider = self.get_provider()

			# create delete operation
			operation = DeleteOperation(
									self._parent,
									provider
								)

			operation.set_force_delete(True)
			operation.set_selection(provider.list_dir(provider.get_root_path(None)))

			# perform removal
			operation.start()

	def change_path(self, path=None, selected=None):
		"""Change file list path."""
		if path is not None and not path.startswith('trash://'):
			path = 'trash:///'

		FileList.change_path(self, path, selected)
