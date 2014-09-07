from file_list import FileList
from gio_provider import TrashProvider


class TrashList(FileList):
	"""Trash file list plugin

	Generic operations related to trash management are provided with this
	class. By extending FileList standard features such as drag and drop are
	supported.

	"""

	def __init__(self, parent, notebook, options):
		FileList.__init__(self, parent, notebook, options)

	def change_path(self, path=None, selected=None):
		"""Change file list path."""
		if path is not None and not path.startswith('trash:'):
			path = self.get_provider().get_root_path(None)

		FileList.change_path(self, path, selected)

	def get_provider(self):
		"""Get list provider object."""
		if self._provider is None:
			self._provider = TrashProvider(self)

		return self._provider

