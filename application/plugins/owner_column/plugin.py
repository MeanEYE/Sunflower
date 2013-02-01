import gtk

from plugin_base.item_list import ItemList
from plugin_base.column_extension import ColumnExtension


def register_plugin(application):
	"""Register plugin class with application"""
	application.register_column_extension(ItemList, OwnerColumn)


class OwnerColumn(ColumnExtension):
	"""Adds support for displaying owner and group in item list"""

	def __init__(self, parent, store):
		ColumnExtension.__init__(self, parent, store)

		# create column object
		self._create_column()

	def __set_cell_data(self, column, cell, store, selected_iter, data=None):
		"""Set column value"""
		is_parent = store.get_value(selected_iter, 10)

		value = (store.get_value(selected_iter, 14), '')[is_parent]
		cell.set_property('text', value)

	def _create_column(self):
		"""Create column"""
		cell_renderer = gtk.CellRendererText()
		cell_renderer.set_property('size-points', 8)

		self._column = gtk.TreeViewColumn(_('Owner'))
		self._column.pack_start(cell_renderer, True)
		self._column.set_data('name', 'owner')
		self._column.set_resizable(True)
		self._column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self._column.connect('clicked', self._parent._set_sort_function, 14)
		self._column.set_cell_data_func(cell_renderer, self.__set_cell_data)

	def get_column(self):
		"""Get column object to be added to the list"""
		return self._column
