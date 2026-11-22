from __future__ import absolute_import

import grp
import pwd

from gi.repository import Gtk
from sunflower.plugins.file_list.file_list import Column
from sunflower.plugins.file_list.plugin import FileList
from sunflower.plugin_base.column_extension import ColumnExtension


def register_plugin(application):
	"""Register plugin class with application"""
	application.register_column_extension(FileList, OwnerColumn)
	application.register_column_extension(FileList, GroupColumn)


class BaseColumn(ColumnExtension):
	"""Base class for extending owner and group for item list"""

	def __init__(self, parent, store):
		ColumnExtension.__init__(self, parent, store)
		self._parent = parent
		self._names = {}  # cache as looking names up can be slow

		# create column object
		self._create_column()

	def _create_column(self):
		"""Create column"""
		self._cell_renderer = Gtk.CellRendererText()
		self._parent.set_default_font_size(self._get_column_name(), 8)

		self._column = Gtk.TreeViewColumn(self._get_column_title())
		self._column.pack_start(self._cell_renderer, True)
		self._column.name = self._get_column_name()

	def _get_column_name(self):
		"""Returns column name"""
		return None

	def _get_column_title(self):
		"""Returns column title"""
		return None

	def __set_cell_data(self, column, cell, store, selected_iter, data=None):
		"""Set column value"""
		pass


class OwnerColumn(BaseColumn):
	"""Adds support for displaying owner in item list"""

	def __set_cell_data(self, column, cell, store, selected_iter, data=None):
		"""Set column value"""
		is_parent = store.get_value(selected_iter, Column.IS_PARENT_DIR)

		if is_parent:
			cell.set_property('text', '')
			return

		user_id = store.get_value(selected_iter, Column.USER_ID)

		if user_id not in self._names:
			try:
				self._names[user_id] = pwd.getpwuid(user_id).pw_name

			except (KeyError, OverflowError):
				# there's no user with this id on the system
				self._names[user_id] = str(user_id)

		cell.set_property('text', self._names[user_id])

	def _create_column(self):
		"""Configure column"""
		BaseColumn._create_column(self)
		self._column.set_cell_data_func(self._cell_renderer, self.__set_cell_data)

	def _get_column_name(self):
		"""Returns column name"""
		return 'owner'

	def _get_column_title(self):
		"""Returns column title"""
		return _('Owner')

	def get_sort_column(self):
		"""Return sort column"""
		return Column.USER_ID


class GroupColumn(BaseColumn):
	"""Adds support for displaying group in item list"""

	def __set_cell_data(self, column, cell, store, selected_iter, data=None):
		"""Set column value"""
		is_parent = store.get_value(selected_iter, Column.IS_PARENT_DIR)

		if is_parent:
			cell.set_property('text', '')
			return

		group_id = store.get_value(selected_iter, Column.GROUP_ID)

		if group_id not in self._names:
			try:
				self._names[group_id] = grp.getgrgid(group_id).gr_name

			except (KeyError, OverflowError):
				# there's no group with this id on the system
				self._names[group_id] = str(group_id)

		cell.set_property('text', self._names[group_id])

	def _create_column(self):
		"""Configure column"""
		BaseColumn._create_column(self)
		self._column.set_cell_data_func(self._cell_renderer, self.__set_cell_data)

	def _get_column_name(self):
		"""Returns column name"""
		return 'group'

	def _get_column_title(self):
		"""Returns column title"""
		return _('Group')

	def get_sort_column(self):
		"""Return sort column"""
		return Column.GROUP_ID
