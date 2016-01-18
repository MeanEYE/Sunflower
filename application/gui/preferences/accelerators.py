import gtk

from accelerator_manager import GroupType
from widgets.settings_page import SettingsPage


class Column:
	NAME = 0
	TITLE = 1
	PRIMARY_KEY = 2
	PRIMARY_MODS = 3
	SECONDARY_KEY = 4
	SECONDARY_MODS = 5


class AcceleratorOptions(SettingsPage):
	"""Accelerator options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'accelerators', _('Key bindings'))

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._accels = gtk.TreeStore(str, str, int, int, int, int)
		self._accels.set_sort_column_id(Column.TITLE, gtk.SORT_ASCENDING)

		self._list = gtk.TreeView()
		self._list.set_model(self._accels)
		self._list.set_rules_hint(True)
		self._list.set_enable_search(True)
		self._list.set_search_column(Column.TITLE)

		# create and configure cell renderers
		cell_name = gtk.CellRendererText()
		cell_primary = gtk.CellRendererAccel()
		cell_secondary = gtk.CellRendererAccel()

		cell_primary.set_property('accel-mode', gtk.CELL_RENDERER_ACCEL_MODE_OTHER)
		cell_primary.set_property('editable', True)

		cell_primary.connect('accel-edited', self.__accel_edited, True)
		cell_primary.connect('accel-cleared', self.__accel_cleared, True)

		cell_secondary.set_property('accel-mode', gtk.CELL_RENDERER_ACCEL_MODE_OTHER)
		cell_secondary.set_property('editable', True)

		cell_secondary.connect('accel-edited', self.__accel_edited, False)
		cell_secondary.connect('accel-cleared', self.__accel_cleared, False)

		# create and pack columns
		col_name = gtk.TreeViewColumn(_('Description'), cell_name, markup=Column.TITLE)
		col_name.set_min_width(200)
		col_name.set_resizable(True)
		col_name.set_sort_column_id(Column.TITLE)
		col_name.set_sort_order(gtk.SORT_ASCENDING)

		col_primary = gtk.TreeViewColumn(
									_('Primary'),
									cell_primary,
									accel_key=Column.PRIMARY_KEY,
									accel_mods=Column.PRIMARY_MODS
								)
		col_primary.set_min_width(100)

		col_secondary = gtk.TreeViewColumn(
									_('Secondary'),
									cell_secondary,
									accel_key=Column.SECONDARY_KEY,
									accel_mods=Column.SECONDARY_MODS
								)
		col_secondary.set_min_width(100)

		self._list.append_column(col_name)
		self._list.append_column(col_primary)
		self._list.append_column(col_secondary)

		# warning label
		label_warning = gtk.Label(_(
							'<b>Note:</b> You can only edit accelerators from '
							'objects created at least once in current session. '
							'To disable accelerator press <i>Backspace</i> '
							'in assign mode.'
						))
		label_warning.set_alignment(0, 0)
		label_warning.set_use_markup(True)
		label_warning.set_line_wrap(True)
		label_warning.connect('size-allocate', self._adjust_label)

		label_note = gtk.Label(_('Double click on accelerator to assign new one.'))
		label_note.set_alignment(0, 0)

		# pack interface
		container.add(self._list)

		self.pack_start(label_warning, False, False, 0)
		self.pack_start(container, True, True, 0)
		self.pack_start(label_note, False, False, 0)

	def __find_iter_by_group_name(self, group_name):
		"""Find group iter by its name"""
		result = None

		for row in self._accels:
			iter_name = self._accels.get_value(row.iter, Column.NAME)

			if iter_name == group_name:
				result = row.iter
				break

		return result

	def __find_iter_by_method_name(self, group_name, method_name):
		"""Find iter by method name"""
		result = None
		group_iter = self.__find_iter_by_group_name(group_name)

		# get group children
		if group_iter is not None:
			accelerator_iter = self._accels.iter_children(group_iter)

			while accelerator_iter is not None:
				iter_name = self._accels.get_value(accelerator_iter, Column.NAME)

				# exit loop if we found the result
				if iter_name == method_name:
					result = accelerator_iter
					break

				accelerator_iter = self._accels.iter_next(accelerator_iter)

		return result

	def __change_accelerator(self, accelerator_iter, keyval, modifier, primary):
		"""Change accelerator value in the list"""
		column_key = Column.PRIMARY_KEY if primary else Column.SECONDARY_KEY
		column_mods = Column.PRIMARY_MODS if primary else Column.SECONDARY_MODS

		# save changes to local list
		self._accels.set_value(accelerator_iter, column_key, keyval)
		self._accels.set_value(accelerator_iter, column_mods, modifier)

		# enable save button
		self._parent.enable_save(show_restart=True)

	def __check_collisions(self, keyval, modifier):
		"""Check specified keyval/modifier combination against other key bindings for collisions."""
		result = []
		accelerator_manager = self._application.accelerator_manager

		# don't check empty values
		if (keyval, modifier) == (0, 0):
			return result

		# check against already defined accelerators
		for row in self._accels:
			group_name = self._accels.get_value(row.iter, Column.NAME)
			group = accelerator_manager._get_group_by_name(group_name)

			for child in row.iterchildren():
				name = self._accels.get_value(child.iter, Column.NAME)
				p_key = self._accels.get_value(child.iter, Column.PRIMARY_KEY)
				p_mod = self._accels.get_value(child.iter, Column.PRIMARY_MODS)
				s_key = self._accels.get_value(child.iter, Column.SECONDARY_KEY)
				s_mod = self._accels.get_value(child.iter, Column.SECONDARY_MODS)

				if (keyval, modifier) == (p_key, p_mod):
					result.append((group, name, True))
				if (keyval, modifier) == (s_key, s_mod):
					result.append((group, name, False))

		return result

	def __accel_edited(self, widget, path, keyval, modifier, hwcode, primary):
		"""Handle editing accelerator"""
		selected_iter = self._accels.get_iter(path)
		accelerator_label = gtk.accelerator_get_label(keyval, modifier)

		# get list of collisions
		collisions = self.__check_collisions(keyval, modifier)

		# ask user what to do with collisions
		if len(collisions) > 0:
			method_list = []
			for group, method_name, colliding_primary in collisions:
				method_list.append(group.get_method_title(method_name))
			methods = '\n'.join([method_name for method_name in method_list])

			# show dialog
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_QUESTION,
									gtk.BUTTONS_YES_NO,
									_(
										'Selected accelerator "{0}" is already being '
										'used. Would you still like to assign accelerator '
										'to this function? This will reset listed '
										'functions.\n\n'
										'Collisions:\n'
										'{1}'
									).format(accelerator_label, methods)
								)
			dialog.set_default_response(gtk.RESPONSE_NO)
			result = dialog.run()
			dialog.destroy()

			if result == gtk.RESPONSE_YES:
				# reset other accelerators
				for group, method_name, colliding_primary in collisions:
					colliding_iter = self.__find_iter_by_method_name(
														group.get_name(),
														method_name
													)

					if colliding_iter is not None:
						self.__change_accelerator(colliding_iter, 0, 0, colliding_primary)

				# save new accelerator
				self.__change_accelerator(selected_iter, keyval, modifier, primary)

		else:
			# no collisions detected
			self.__change_accelerator(selected_iter, keyval, modifier, primary)

	def __accel_cleared(self, widget, path, primary):
		"""Handle clearing accelerator"""
		accel_iter = self._accels.get_iter(path)

		if accel_iter is not None:
			column_key = Column.PRIMARY_KEY if primary else Column.SECONDARY_KEY
			column_mods = Column.PRIMARY_MODS if primary else Column.SECONDARY_MODS

			keyval = self._accels.get_value(accel_iter, column_key)
			modifier = self._accels.get_value(accel_iter, column_mods)

			if keyval == 0 and modifier == 0:
				self.__accel_edited(widget, path, gtk.keysyms.BackSpace, 0, None, primary)
			else:
				self.__change_accelerator(accel_iter, 0, 0, primary)

	def _populate_list(self):
		"""Update accelerator list"""
		manager = self._application.accelerator_manager
		bookmarks = self._application.bookmark_options.get('bookmarks')
		groups = manager.get_groups()
		groups.sort()

		# clear accelerator list
		self._accels.clear()

		# create rename list
		replace_list = {}

		key_name = '{0}.bookmark_home'.format('item_list')
		replace_list[key_name] = _('Home directory')

		# add bookmarks to the replace list
		for number in range(1, 11):
			key_name = '{0}.{1}_{2}'.format('item_list', 'bookmark', number)

			if number < len(bookmarks):
				# bookmark exists
				bookmark_value = bookmarks[number-1]['name']

			else:
				# bookmark doesn't exist, add generic name
				bookmark_value = 'Bookmark #{0}'.format(number)

			replace_list[key_name] = bookmark_value

		# add methods
		for group_name in groups:
			title, methods = manager.get_group_data(group_name)

			method_names = methods.keys()
			method_names.sort()

			# add group and save iter for later use
			group_iter = self._accels.append(None, (group_name, '<b>{0}</b>'.format(title), 0, 0, 0 ,0))

			for method_name in method_names:
				# add all methods from the group
				title = methods[method_name]['title']

				# check if specified method name has a rename value
				key_name = '{0}.{1}'.format(group_name, method_name)
				if key_name in replace_list:
					title = title.format(replace_list[key_name])

				# get accelerators
				primary = manager.get_accelerator(group_name, method_name, True)
				secondary = manager.get_accelerator(group_name, method_name, False)

				# make sure we have something to display
				if primary is None:
					primary = (0, 0)

				if secondary is None:
					secondary = (0, 0)

				# append to the list
				data = (method_name, title, primary[0], primary[1], secondary[0], secondary[1])
				self._accels.append(group_iter, data)

	def _adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)

	def _load_options(self):
		"""Load options and update interface"""
		self._populate_list()

	def _save_options(self):
		"""Method called when save button is clicked"""
		manager = self._application.accelerator_manager

		# iterate over groups
		for row in self._accels:
			group_name = self._accels.get_value(row.iter, Column.NAME)
			children = row.iterchildren()

			# store accelerators for current group
			for child in children:
				name = self._accels.get_value(child.iter, Column.NAME)

				# save primary accelerator
				manager._save_accelerator(
									group_name,
									name,
									(
										self._accels.get_value(child.iter, Column.PRIMARY_KEY),
										self._accels.get_value(child.iter, Column.PRIMARY_MODS)
									),
									primary=True,
									can_overwrite=True
								)

				# save secondary accelerator
				manager._save_accelerator(
									group_name,
									name,
									(
										self._accels.get_value(child.iter, Column.SECONDARY_KEY),
										self._accels.get_value(child.iter, Column.SECONDARY_MODS)
									),
									primary=False,
									can_overwrite=True
								)

