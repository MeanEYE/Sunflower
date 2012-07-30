import gtk

from widgets.settings_page import SettingsPage


class Column:
	TITLE = 0
	COMMAND = 1


class CommandsOptions(SettingsPage):
	"""Commands options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'commands', _('Commands'))

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._commands = gtk.ListStore(str, str)

		self._list = gtk.TreeView()
		self._list.set_model(self._commands)
		self._list.set_rules_hint(True)

		# create and configure cell renderers
		cell_title = gtk.CellRendererText()
		cell_title.set_property('editable', True)
		cell_title.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_title.connect('edited', self._edited_command, 0)

		cell_command = gtk.CellRendererText()
		cell_command.set_property('editable', True)
		cell_command.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_command.connect('edited', self._edited_command, 1)

		# create and pack columns
		col_title = gtk.TreeViewColumn(_('Title'), cell_title, text=Column.TITLE)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn(_('Command'), cell_command, text=Column.COMMAND)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)

		container.add(self._list)

		# create controls
		button_box = gtk.HBox(False, 5)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_command)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_command)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_move_up = gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._move_command, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_move_down = gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._move_command, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_command(self, widget, data=None):
		"""Add new command to the store"""
		if data is None:
			data = ('New command', '')

		# add new item to store
		self._commands.append(data)

		# enable save button on parent
		self._parent.enable_save()

	def _edited_command(self, cell, path, text, column):
		"""Record edited text"""
		selected_iter = self._commands.get_iter(path)
		self._commands.set_value(selected_iter, column, text)

		# enable save button
		self._parent.enable_save()

	def _delete_command(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# remove item from the list
			item_list.remove(selected_iter)

			# enable save button in case item was removed
			self._parent.enable_save()

	def _move_command(self, widget, direction):
		"""Move selected command"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			# get iter index
			index = item_list.get_path(selected_iter)[0]

			# swap iters depending on specified direction
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(item_list) - 1):
				item_list.swap(selected_iter, item_list[index + direction].iter)

			# it items were swapped, enable save button
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		options = self._application.command_options

		# load and parse commands
		self._commands.clear()

		command_list = options.get('commands')

		for command in command_list:
			self._commands.append((
						command['title'],
						command['command']	
					))

	def _save_options(self):
		"""Save commands to file"""
		options = self._application.command_options
		commands = []

		# save commands
		for data in self._commands:
			commands.append({
					'title': data[Column.TITLE],
					'command': data[Column.COMMAND]
				})

		options.set('commands', commands)
