import os


class HistoryManager:
	"""Class used for management and maintenance of item list history."""

	def __init__(self, parent, storage_list):
		self._list = storage_list
		self._index = 0
		self._parent = parent

	def _change_to_index(self, index):
		"""Change parent path to specified index"""
		new_path = self._list[index]
		current_path = self._parent._options.get('path')

		# determine if row needs to be selected
		selection = None
		if current_path.startswith(new_path):
			selection = os.path.basename(current_path)

		# change path
		self._parent.change_path(new_path, selection)

	def record(self, path):
		"""Record new path in history"""
		if not path in self._list:
			self._list.insert(self._index, path)

		else:
			self._index = self._list.index(path)

	def back(self):
		"""Go back in history one step"""
		if self._index >= len(self._list) - 1:
			return

		# change path
		self._change_to_index(self._index + 1)

	def forward(self):
		"""Go forward in history one step"""
		if self._index < 1:
			return

		# change path
		self._change_to_index(self._index - 1)
