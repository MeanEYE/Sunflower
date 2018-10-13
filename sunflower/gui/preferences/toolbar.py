from gi.repository import Gtk
from sunflower.widgets.settings_page import SettingsPage


class Column:
	NAME = 0
	DESCRIPTION = 1
	TYPE = 2
	ICON = 3


class ToolbarOptions(SettingsPage):
	"""Toolbar options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'toolbar', _('Toolbar'))

		self._toolbar_manager = self._application.toolbar_manager

		# create list box
		container = Gtk.ScrolledWindow()
		container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		container.set_shadow_type(Gtk.ShadowType.IN)

		self._store = Gtk.ListStore(str, str, str, str)
		self._list = Gtk.TreeView()
		self._list.set_model(self._store)

		cell_icon = Gtk.CellRendererPixbuf()
		cell_name = Gtk.CellRendererText()
		cell_type = Gtk.CellRendererText()

		# create name column
		col_name = Gtk.TreeViewColumn(_('Name'))
		col_name.set_min_width(200)
		col_name.set_resizable(True)

		# pack and configure renderes
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'text', Column.NAME)

		# create type column
		col_type = Gtk.TreeViewColumn(_('Type'), cell_type, markup=Column.DESCRIPTION)
		col_type.set_resizable(True)
		col_type.set_expand(True)

		# add columns to the list
		self._list.append_column(col_name)
		self._list.append_column(col_type)

		container.add(self._list)

		# create controls
		button_box = Gtk.HBox(False, 5)

		button_add = Gtk.Button(stock=Gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_widget)

		button_delete = Gtk.Button(stock=Gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._delete_widget)

		button_edit = Gtk.Button(stock=Gtk.STOCK_EDIT)
		button_edit.connect('clicked', self._edit_widget)

		image_up = Gtk.Image()
		image_up.set_from_stock(Gtk.STOCK_GO_UP, Gtk.IconSize.BUTTON)

		button_move_up = Gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._move_widget, -1)

		image_down = Gtk.Image()
		image_down.set_from_stock(Gtk.STOCK_GO_DOWN, Gtk.IconSize.BUTTON)

		button_move_down = Gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._move_widget, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_start(button_edit, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		# toolbar style
		label_style = Gtk.Label(label=_('Toolbar style:'))
		list_styles = Gtk.ListStore(str, int)
		list_styles.append((_('Icons'), Gtk.ToolbarStyle.ICONS))
		list_styles.append((_('Text'), Gtk.ToolbarStyle.TEXT))
		list_styles.append((_('Both'), Gtk.ToolbarStyle.BOTH))
		list_styles.append((_('Both horizontal'), Gtk.ToolbarStyle.BOTH_HORIZ))

		renderer = Gtk.CellRendererText()

		self._combobox_styles = Gtk.ComboBox(model=list_styles)
		self._combobox_styles.pack_start(renderer, True)
		self._combobox_styles.add_attribute(renderer, 'text', 0)
		self._combobox_styles.connect('changed', self._parent.enable_save)

		# toolbar icon size
		label_icon_size = Gtk.Label(label=_('Icon size:'))
		list_icon_size = Gtk.ListStore(str, int)
		list_icon_size.append((_('Same as menu item'), Gtk.IconSize.MENU))
		list_icon_size.append((_('Small toolbar icon'), Gtk.IconSize.SMALL_TOOLBAR))
		list_icon_size.append((_('Large toolbar icon'), Gtk.IconSize.LARGE_TOOLBAR))
		list_icon_size.append((_('Same as buttons'), Gtk.IconSize.BUTTON))
		list_icon_size.append((_('Same as drag icons'), Gtk.IconSize.DND))
		list_icon_size.append((_('Same as dialog'), Gtk.IconSize.DIALOG))

		renderer = Gtk.CellRendererText()

		self._combobox_icon_size = Gtk.ComboBox(model=list_icon_size)
		self._combobox_icon_size.pack_start(renderer, True)
		self._combobox_icon_size.add_attribute(renderer, 'text', 0)
		self._combobox_icon_size.connect('changed', self._parent.enable_save)

		style_box = Gtk.HBox(False, 5)
		style_box.pack_start(label_style, False, False, 0)
		style_box.pack_start(self._combobox_styles, False, False, 0)

		size_box = Gtk.HBox(False, 5)
		size_box.pack_start(label_icon_size, False, False, 0)
		size_box.pack_start(self._combobox_icon_size, False, False, 0)

		self.pack_start(style_box, False, False, 0)
		self.pack_start(size_box, False, False, 0)
		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_widget(self, widget, data=None):
		"""Show dialog for creating toolbar widget"""
		widget_added = self._toolbar_manager.show_create_widget_dialog(self._parent)

		if widget_added:
			# reload configuratin file
			self._load_options()

			# enable save button
			self._parent.enable_save()

	def _delete_widget(self, widget, data=None):
		"""Delete selected toolbar widget"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# remove item from list
			list_.remove(iter_)

			# enable save button if item was removed
			self._parent.enable_save()

	def _edit_widget(self, widget, data=None):
		"""Edit selected toolbar widget"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			name = list_.get_value(iter_, 0)
			widget_type = list_.get_value(iter_, 2)

			edited = self._toolbar_manager.show_configure_widget_dialog(
			                                                name,
			                                                widget_type,
			                                                self._parent
			                                            )

			# enable save button
			if edited:
				self._parent.enable_save()

	def _move_widget(self, widget, direction):
		"""Move selected bookmark up"""
		selection = self._list.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get iter index
			index = list_.get_path(iter_)[0]

			# depending on direction, swap iters
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list_) - 1):
				list_.swap(iter_, list_[index + direction].iter)

			# enable save button if iters were swapped
			self._parent.enable_save()

	def _load_options(self):
		"""Load options from file"""
		options = self._application.toolbar_options

		self._combobox_styles.set_active(options.get('style'))
		self._combobox_icon_size.set_active(options.get('icon_size'))

		# clear list store
		self._store.clear()

		for name in options.get_sections():
			section = options.section(name)
			widget_type = section.get('type')
			data = self._toolbar_manager.get_widget_data(widget_type)

			if data is not None:
				icon = data[1]
				description = data[0]

			else:  # failsafe, display raw widget type
				icon = ''
				description = '{0} <small><i>({1})</i></small>'.format(widget_type, _('missing plugin'))

			self._store.append((name, description, widget_type, icon))

	def _save_options(self):
		"""Save settings to config file"""
		options = self._application.toolbar_options

		options.set('style', self._combobox_styles.get_active())
		options.set('icon_size', self._combobox_icon_size.get_active())
		# get section list, we'll use this
		# list to remove orphan configurations
		section_list = options.get_sections()

		# get list from configuration window
		new_list = []
		for data in self._store:
			new_list.append(data[Column.NAME])

		for name in section_list:
			if name not in new_list:
				options.remove_section(name)
