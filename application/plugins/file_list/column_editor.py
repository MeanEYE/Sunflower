from plugin_base.column_editor_extension import ColumnEditorExtension


class FileList_ColumnEditor(ColumnEditorExtension):
	"""Column editor for file list plugin"""

	def __init__(self, parent, config):
		ColumnEditorExtension.__init__(self, parent, config)

		self._columns = []
		self._visible = []
		self._sizes = {}
		self._font_sizes = {}

	def __update_column_list(self):
		"""Update list of available columns"""
		self._columns = []

		for column in self._parent._columns:
			self._columns.append(column.get_data('name'))

	def _save_settings(self):
		"""Save values to config"""
		section = self._config.create_section(self._parent_name)

		# save column order and visibility
		section.set('columns', self._visible[:])

		# save column sizes
		for name, size in self._sizes.items():
			section.set('size_{0}'.format(name), size)

		# save font sizes
		for name, size in self._font_sizes.items():
			section.set('font_size_{0}'.format(name), size)

	def _load_settings(self):
		"""Load values from config"""
		section = self._config.section(self._parent_name)

		# update columns
		self.__update_column_list()

		if section is None:
			return

		# get list of visible columns
		self._visible = section.get('columns')

		# make sure we have list of visible columns
		if self._visible is None:
			self._visible = self._columns

		# get sizes
		for column_name in self._columns:
			size = section.get('size_{0}'.format(column_name))

			if size is not None:
				self._sizes[column_name] = size

		# get font sizes
		for column_name in self._columns:
			size = section.get('font_size_{0}'.format(column_name))

			if size is not None:
				self._font_sizes[column_name] = size

	def get_name(self):
		"""Return name of extension"""
		return _('Item List'), self._parent_name

	def get_columns(self, only_visible=False):
		"""Get column names"""
		result = self._columns[:]

		if only_visible:
			result = filter(lambda column_name: column_name in self._visible, result)

		return result

	def get_size(self, column):
		"""Get column size"""
		return self._sizes[column] if column in self._sizes else None

	def get_font_size(self, column):
		"""Get column font size"""
		return self._font_sizes[column] if column in self._font_sizes else None

	def get_visible(self, column):
		"""Get column visibility"""
		return column in self._visible

	def set_size(self, column, size):
		"""Set column size"""
		if column in self._columns:
			self._sizes[column] = size

	def set_font_size(self, column, size):
		"""Set column font size"""
		if column in self._columns:
			self._font_sizes[column] = size

	def set_visible(self, column, visible):
		"""Set column visibility"""
		if visible:
			# column was hidden, visible now
			if column in self._columns:
				index = self._columns.index(column)
				self._visible.insert(index, column)

			else:
				self._visible.append(column)
		
		else:
			# column was visible, hidden now
			try:
				self._visible.remove(column)

			except ValueError:
				pass
