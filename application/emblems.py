import os
import gtk
import user
import sqlite3 as sql

from common import get_cache_directory


class EmblemManager:
	"""Manager class for item emblems.

	This object is used for managing emblems for items as well as rendering Pixbuffs.

	"""
	default_emblems = (
			'emblem-default',
			'emblem-documents',
			'emblem-downloads',
			'emblem-favorite',
			'emblem-important',
			'emblem-mail',
			'emblem-photos',
			'emblem-readonly',
			'emblem-shared',
			'emblem-symbolic-link',
			'emblem-system',
			'emblem-unreadable'
		)

	def __init__(self, parent):
		self._parent = parent
		self._icon_manager = self._parent.icon_manager

		# connect to database
		self._connection = self._connect_to_database()

		# make sure we have tables to work with
		if not self._check_database():
			self._create_database()

	def _connect_to_database(self):
		"""Create a connection to database."""
		cache_directory = get_cache_directory()

		# generate database file name
		if os.path.isdir(cache_directory):
			database_file = os.path.join(cache_directory, 'sunflower_emblems.db')
		else:
			database_file = os.path.join(user.home, '.sunflower_emblems.db')

		# connect to database
		result = sql.connect(database_file, check_same_thread=False)
		result.text_factory = str

		return result

	def _table_exists(self, cursor, table_name):
		"""Check if specified table exist in current database."""
		result = False

		cursor.execute('SELECT count(*) FROM sqlite_master WHERE type="table" AND name=?', (table_name, ))
		result = cursor.fetchone()[0] > 0

		return result

	def _check_database(self):
		"""Check storage database integrity."""
		result = False

		cursor = self._get_cursor()
		result = self._table_exists(cursor, 'items')
		result = result and self._table_exists(cursor, 'emblems')

		return result

	def _create_database(self):
		"""Create database tables."""
		cursor = self._get_cursor()

		cursor.executescript('''
				CREATE TABLE items (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					path TEXT NOT NULL,
					name TEXT NOT NULL
				);
				CREATE INDEX items_by_path ON items(path);
				CREATE INDEX items_by_path_and_name ON items(path, name);

				CREATE TABLE emblems (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					item INTEGER NOT NULL,
					value TEXT NOT NULL
				);
				CREATE INDEX emblems_by_item ON emblems(item);
			''')

		# commit changes
		self._connection.commit()

	def _get_cursor(self):
		"""Return new cursor for database."""
		assert self._connection is not None
		return self._connection.cursor()

	def add_emblem(self, path, item_name, emblem):
		"""Add emblems for specified path."""
		result = False
		cursor = self._get_cursor()

		# find item id
		cursor.execute('SELECT id FROM items WHERE path=? AND name=? LIMIT 1', (path, item_name))
		data = cursor.fetchone()

		if data is None:
			# item doesn't exist, insert new one
			cursor.execute('INSERT INTO items(path, name) VALUES(?, ?)', (path, item_name))
			item_id = cursor.lastrowid

		else:
			item_id = data[0]

		# find emblem id
		cursor.execute('SELECT id FROM emblems WHERE item=? AND value=? LIMIT 1', (item_id, emblem))
		data = cursor.fetchone()

		# emblem already exists
		if data is not None:
			return result

		# add new emblem to item
		cursor.execute('INSERT INTO emblems(item, value) VALUES(?, ?)', (item_id, emblem))
		result = True

		# commit changes
		self._connection.commit()

		return result

	def toggle_emblem(self, path, item_name, emblem):
		"""Toggle emblem on specified item."""
		emblems = self.get_emblems(path, item_name)

		if emblems is not None and emblem in emblems:
			self.remove_emblem(path, item_name, emblem)

		else:
			self.add_emblem(path, item_name, emblem)

	def set_emblems(self, path, item_name, emblems):
		"""Set multiple emblems at the same time."""
		self.clear_emblems(path, item_name, remove_item=False)
		cursor = self._get_cursor()

		# find item id
		cursor.execute('SELECT id FROM items WHERE path=? AND name=? LIMIT 1', (path, item_name))
		data = cursor.fetchone()

		if data is None:
			# item doesn't exist, insert new one
			cursor.execute('INSERT INTO items(path, name) VALUES(?, ?)', (path, item_name))
			item_id = cursor.lastrowid

		else:
			item_id = data[0]

		# store new emblems
		data = tuple((item_id, emblem) for emblem in emblems)
		cursor.executemany('INSERT INTO emblems(item, value) VALUES(?, ?)', data)
		self._connection.commit()

	def remove_emblem(self, path, item_name, emblem):
		"""Remove emblem from path."""
		result = False
		cursor = self._get_cursor()

		# find item id
		cursor.execute('SELECT id FROM items WHERE path=? AND name=? LIMIT 1', (path, item_name))
		data = cursor.fetchone()

		# item doesn't exist
		if data is None:
			return result

		# find emblem id
		cursor.execute('SELECT id FROM emblems WHERE item=? AND value=? LIMIT 1', (data[0], emblem))
		data = cursor.fetchone()

		# emblem doesn't exist
		if data is None:
			return result

		# remove emblem
		cursor.execute('DELETE FROM emblems WHERE id=?', (data[0],))
		self._connection.commit()
		result = True

		return result

	def clear_emblems(self, path, item_name, remove_item=True):
		"""Clear all emblems for path."""
		result = False
		cursor = self._get_cursor()

		# find item id
		cursor.execute('SELECT id FROM items WHERE path=? AND name=? LIMIT 1', (path, item_name))
		data = cursor.fetchone()

		# remove emblems
		if data is not None:
			cursor.execute('DELETE FROM emblems WHERE item=?', (data[0],))

			# remove item if requested
			if remove_item:
				cursor.execute('DELETE FROM items WHERE id=?', (data[0],))

			# commit changes
			self._connection.commit()
			result = True

		return result

	def get_emblems(self, path, item_name):
		"""Get all emblem names for item in path."""
		result = None
		cursor = self._get_cursor()

		# find path in database
		cursor.execute('SELECT id FROM items WHERE path=? AND name=? LIMIT 1', (path, item_name))
		row = cursor.fetchone()

		# no emblems for this path
		if row is None:
			return result

		# get emblems for this item
		item_id = row[0]
		cursor.execute('SELECT value FROM emblems WHERE item=?', (item_id,))

		# prepare result
		icom_theme = gtk.icon_theme_get_default()
		result = tuple(row[0] for row in cursor.fetchall())
		result = filter(lambda icon: icom_theme.has_icon(icon), result)

		return result

	def get_available_emblems(self):
		"""Get all available emblems."""
		return self.default_emblems

	def get_emblems_for_path(self, path):
		"""Get emblems for all items in specified path."""
		result = {}
		cursor = self._get_cursor()

		# get all the items in path
		cursor.execute('SELECT id, name FROM items WHERE path=?', (path,))
		items = cursor.fetchall()

		# exit if there are no items in path
		if len(items) == 0:
			return result

		# get emblems for each item
		for item_id, item_name in items:
			cursor.execute('SELECT value FROM emblems WHERE item=?', (item_id,))
			icom_theme = gtk.icon_theme_get_default()
			emblems = tuple(row[0] for row in cursor.fetchall())
			result[item_name] = filter(lambda icon: icom_theme.has_icon(icon), emblems)

		return result
