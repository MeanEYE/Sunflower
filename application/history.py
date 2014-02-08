

class HistoryManager:
	"""Class used for management and maintenance of item list history."""

	def __init__(self, parent, storage_list):
		self._list = storage_list
		self._index = 0
		self._parent = parent

	def record(self, path):
		"""Record new path in history"""
		if not path in self._list:
			self._list.insert(self._index, path)

		else:
			self._index = self._list.index(path)

	def back(self):
		"""Go back in history one step"""
		if self._index >= len(self._list):
			return

		new_index = self._index + 1
		self._parent.change_path(self._list[new_index])

	def forward(self):
		"""Go forward in history one step"""
		if self._index < 1:
			return

		new_index = self._index - 1
		self._parent.change_path(self._list[new_index])
