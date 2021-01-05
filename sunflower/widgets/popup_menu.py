from gi.repository import Gtk, Gdk


class PopupMenu:
	"""Popup menu with path related functions."""

	def __init__(self, application, plugin, path):
		self._application = application

		self._popover_visible = False
		self._popover = Gtk.Popover.new()
		self._popover.get_style_context().add_class('menu')
		self._popover.set_border_width(5)
		self._popover.set_size_request(250, -1)
		self._popover.set_modal(True)
		# self._popover.connect('closed', self.__handle_popover_close)

		left_object = application.get_left_object()
		self._popover.set_position(Gtk.PositionType.RIGHT if plugin is left_object else Gtk.PositionType.LEFT)

		# create stack to allow submenus
		self._stack = Gtk.Stack.new()
		self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
		self._popover.add(self._stack)

		# main menu box
		box = Gtk.VBox.new(False, 0)
		self._stack.add_named(box, 'main')

		# operation items
		hbox = Gtk.HBox.new(True, 0)
		hbox.get_style_context().add_class('linked')
		hbox.get_style_context().add_class('flat')
		hbox.set_margin_bottom(5)
		box.pack_start(hbox, True, False, 0)

		cut_button = Gtk.Button.new_from_icon_name('edit-cut-symbolic', Gtk.IconSize.MENU)
		hbox.pack_start(cut_button, True, True, 0)

		copy_button = Gtk.Button.new_from_icon_name('edit-copy-symbolic', Gtk.IconSize.MENU)
		hbox.pack_start(copy_button, True, True, 0)

		paste_button = Gtk.Button.new_from_icon_name('edit-paste-symbolic', Gtk.IconSize.MENU)
		hbox.pack_start(paste_button, True, True, 0)

		remove_button = Gtk.Button.new_from_icon_name('edit-delete-symbolic', Gtk.IconSize.MENU)
		hbox.pack_start(remove_button, True, True, 0)

		rename_button = Gtk.Button.new_from_icon_name('document-edit-symbolic', Gtk.IconSize.MENU)
		hbox.pack_start(rename_button, True, True, 0)

		# options for opening path
		self._create_menu_item(_('Open'), box)
		self._create_menu_item(_('Open in new tab'), box)

		button, open_with = self._create_menu_item(_('Open with'), box, 'open-with')
		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)

		self._create_menu_item(_('Copy to other'), box)
		self._create_menu_item(_('Move to other'), box)

		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)

		# path operations
		button, path_operations = self._create_menu_item(_('Path operations'), box, 'path-operations')

		self._create_menu_item(_('Send to...'), path_operations)
		self._create_menu_item(_('Make link'), path_operations)
		path_operations.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)
		self._create_menu_item(_('Copy file name'), path_operations)
		self._create_menu_item(_('Copy path'), path_operations)

		# additional options
		self._emblems = Gtk.FlowBox.new()
		self._emblems.set_selection_mode(Gtk.SelectionMode.NONE)
		emblems_menu = self._create_submenu('emblems', label=_('Emblems'), container=self._emblems)
		button, menu = self._create_menu_item(_('Emblems'), box, 'emblems')

		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)
		self._create_menu_item(_('Properties'), box)

		self.__populate_emblem_menu()

		# show all widgets
		self._stack.show_all()

	def __populate_emblem_menu(self):
		"""Populate emblem menu with options."""
		back_button = Gtk.ModelButton.new()
		back_button.set_property('inverted', True)
		back_button.set_property('menu-name', 'main')
		self._emblems.add(back_button)

		# populate list
		emblem_list = self._application.emblem_manager.get_available_emblems()
		for emblem in emblem_list:
			image = Gtk.Image.new()
			image.set_from_icon_name(emblem, Gtk.IconSize.LARGE_TOOLBAR)

			self._emblems.add(image)

	def __handle_popover_open(self):
		"""Handle popover opening."""
		self._popover_visible = True

		# disable plugin accelerators
		groups = self._application.accelerator_manager.get_groups()
		for group_name in groups:
			group = self._application.accelerator_manager._get_group_by_name(group_name)
			group.deactivate()

	def __handle_popover_close(self, widget, data=None):
		"""Handle popover closing."""
		self._popover_visible = False

		# enable plugin accelerators
		groups = self._application.accelerator_manager.get_groups()
		for group_name in groups:
			group = self._application.accelerator_manager._get_group_by_name(group_name)
			group.activate(self._application)

	def _create_menu_item(self, label, container, submenu_name=None):
		"""Create menu item and pack in provided container."""
		menu_item = Gtk.ModelButton.new()
		menu_item.set_property('text', label)
		container.pack_start(menu_item, False, False, 0)

		submenu = None
		if submenu_name:
			menu_item.set_property('menu-name', submenu_name)
			if self._stack.get_child_by_name(submenu_name) is None:
				submenu = self._create_submenu(submenu_name, menu_item)

		return menu_item, submenu

	def _create_submenu(self, name, button=None, label=None, container=None):
		"""Create submenu for provided button and return its container."""
		back_button = Gtk.ModelButton.new()
		back_button.set_property('inverted', True)
		back_button.set_property('menu-name', 'main')

		# set menu item label
		if button:
			back_button.set_label(button.get_property('text'))
		elif label:
			back_button.set_label(label)

		# add container to the stack
		if not container:
			container = Gtk.VBox.new(False, 0)
			container.pack_start(back_button, False, False, 0)
		self._stack.add_named(container, name)

		return container

	def show(self, widget, position, page='main'):
		"""Show menu `relative_to` rectangle."""
		self._popover.set_relative_to(widget)
		self._popover.set_pointing_to(position)
		# self.__handle_popover_open()
		self._stack.set_visible_child_name(page)
		self._popover.popup()
