import gtk

from widgets.settings_page import SettingsPage


class ToolsOptions(SettingsPage):
	"""Tools options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'tools', _('Tools Menu'))

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._tools = gtk.ListStore(str, str)

		self._list = gtk.TreeView()
		self._list.set_model(self._tools)
		self._list.set_rules_hint(True)

		# create and configure cell renderers
		cell_title = gtk.CellRendererText()
		cell_title.set_property('editable', True)
		cell_title.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_title.connect('edited', self._edited_tool, 0)

		cell_command = gtk.CellRendererText()
		cell_command.set_property('editable', True)
		cell_command.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_command.connect('edited', self._edited_tool, 1)

		# create and pack columns
		col_title = gtk.TreeViewColumn(_('Title'), cell_title, text=0)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn(_('Command'), cell_command, text=1)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)

		container.add(self._list)

		# create controls
		button_box = gtk.HBox(False, 5)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_tool)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_tool)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_move_up = gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._move_tool, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_move_down = gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._move_tool, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_tool(self, widget, data=None):
		"""Add new tool to the store"""
		if data is None:
			data = ('New tool', '')

		# add new item to store
		self._tools.append(data)

		# enable save button on parent
		self._parent.enable_save()

	def _edited_tool(self, cell, path, text, column):
		"""Record edited text"""
		iter_ = self._tools.get_iter(path)
		self._tools.set_value(iter_, column, text)

		# enable save button
		self._parent.enable_save()

	def _delete_tool(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# remove item from the list
			list_.remove(iter_)

			# enable save button in case item was removed
			self._parent.enable_save()

	def _move_tool(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get iter index
			index = list_.get_path(iter_)[0]

			# swap iters depending on specified direction
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list_) - 1):
				list_.swap(iter_, list_[index + direction].iter)

			# it items were swapped, enable save button
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		tool_options = self._application.tool_options

		# load and parse tools
		if tool_options.has_section('tools'):
			item_list = tool_options.options('tools')
			self._tools.clear()

			for index in range(1, (len(item_list) / 2) + 1):
				tool_title = tool_options.get('tools', 'title_{0}'.format(index))
				tool_command = tool_options.get('tools', 'command_{0}'.format(index))

				# add item to the store
				self._tools.append((tool_title, tool_command))

	def _save_options(self):
		"""Save bookmarks to file"""
		tool_options = self._application.tool_options

		# save bookmars
		tool_options.remove_section('tools')
		tool_options.add_section('tools')

		for index, tool in enumerate(self._tools, 1):
			tool_options.set('tools', 'title_{0}'.format(index), tool[0])
			tool_options.set('tools', 'command_{0}'.format(index), tool[1])
