import os

from random import choice
from gi.repository import Gtk, Gdk

from sunflower.plugin_base.monitor import MonitorSignals


class PopupMenu:
	"""Popup menu with path related functions."""

	def __init__(self, application, plugin):
		self._application = application
		self._provider = None
		self._selected_path = None

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
		self._stack.set_vhomogeneous(False)
		self._stack.set_interpolate_size(True)
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
		cut_button.connect('clicked', plugin._cut_files_to_clipboard)
		hbox.pack_start(cut_button, True, True, 0)

		copy_button = Gtk.Button.new_from_icon_name('edit-copy-symbolic', Gtk.IconSize.MENU)
		copy_button.connect('clicked', plugin._copy_files_to_clipboard)
		hbox.pack_start(copy_button, True, True, 0)

		paste_button = Gtk.Button.new_from_icon_name('edit-paste-symbolic', Gtk.IconSize.MENU)
		paste_button.connect('clicked', plugin._paste_files_from_clipboard)
		hbox.pack_start(paste_button, True, True, 0)

		remove_button = Gtk.Button.new_from_icon_name('edit-delete-symbolic', Gtk.IconSize.MENU)
		remove_button.connect('clicked', plugin._delete_files)
		hbox.pack_start(remove_button, True, True, 0)

		rename_button = Gtk.Button.new_from_icon_name('document-edit-symbolic', Gtk.IconSize.MENU)
		rename_button.connect('clicked', plugin._rename_file)
		hbox.pack_start(rename_button, True, True, 0)

		# options for opening path
		self._create_menu_item(_('Open'), box, handler=plugin._execute_selected_item)
		self._create_menu_item(_('Open in new tab'), box, handler=plugin._open_in_new_tab)

		button, open_with = self._create_menu_item(_('Open with'), box, 'open-with')
		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)

		self._create_menu_item(_('Copy to other'), box, handler=plugin._copy_files)
		self._create_menu_item(_('Move to other'), box, handler=plugin._move_files)

		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)

		# path operations
		button, path_operations = self._create_menu_item(_('Path operations'), box, 'path-operations')

		if self._application.NAUTILUS_SEND_TO_INSTALLED:
			self._create_menu_item(_('Send to...'), path_operations, handler=plugin._send_to)
		self._create_menu_item(_('Make link'), path_operations, handler=plugin._create_link)

		path_operations.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)
		self._create_menu_item(
				_('Copy file name'),
				path_operations,
				handler=plugin.copy_selected_item_name_to_clipboard
				)
		self._create_menu_item(
				_('Copy path'),
				path_operations,
				handler=plugin.copy_selected_path_to_clipboard
				)

		# additional options
		self._emblem_map = {}
		self._emblems = Gtk.Grid.new()
		self._emblems.set_row_spacing(2)
		self._emblems.set_column_spacing(2)
		self._emblems.set_row_homogeneous(True)
		self._emblems.set_column_homogeneous(True)
		button, menu = self._create_menu_item(_('Emblems'), box, 'emblems')
		menu.pack_start(self._emblems, True, True, 0)

		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)
		self._create_menu_item(_('Properties'), box, handler=plugin._item_properties)

		self.__populate_emblem_menu()

		# show all widgets
		self._stack.show_all()

	def __populate_emblem_menu(self):
		"""Populate emblem menu with options."""
		emblem_list = self._application.emblem_manager.get_available_emblems()
		for index, emblem in enumerate(emblem_list):
			image = Gtk.Image.new()
			image.set_from_icon_name(emblem, Gtk.IconSize.LARGE_TOOLBAR)

			button = Gtk.ToggleButton.new()
			button.add(image)
			button.get_style_context().add_class('flat')
			button.connect('toggled', self.__handle_emblem_toggle, emblem)
			self._emblem_map[emblem] = button

			top = index // 5
			left = index - (top * 5)
			self._emblems.attach(button, left-1, top-1, 1, 1)

	def __update_emblem_selection(self, full_path):
		"""Update which emblems are selected for provided path."""
		manager = self._application.emblem_manager
		path, item_name = os.path.split(full_path)
		active_emblems = manager.get_emblems(path, item_name)

		if not active_emblems:
			return

		for emblem, button in self._emblem_map.items():
			button.handler_block_by_func(self.__handle_emblem_toggle)
			button.set_active(emblem in active_emblems)
			button.handler_unblock_by_func(self.__handle_emblem_toggle)

	def __populate_open_with_menu(self, path, mime_type):
		"""Populate submenu for application selection."""
		container = self._stack.get_child_by_name('open-with')

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

		# remove references to help clear memory
		self._provider = None
		self._selected_path = None

	def __handle_emblem_toggle(self, widget, emblem=None):
		"""Handle toggling emblem for current path."""
		manager = self._application.emblem_manager
		path, item_name = os.path.split(self._selected_path)

		update_method = (
					self._application.emblem_manager.remove_emblem,
					self._application.emblem_manager.add_emblem
				)[widget.get_active()]
		update_method(path, item_name, emblem)

		# notify monitor of our change
		parent = self._provider.get_parent()
		parent_path = self._provider.get_path()

		if parent_path == self._provider.get_root_path(parent_path):
			item_path = self._selected_path[len(parent_path):]
		else:
			item_path = self._selected_path[len(parent_path) + 1:]

		queue = parent.get_monitor().get_queue()
		queue.put((MonitorSignals.EMBLEM_CHANGED, item_path, None))

	def _create_menu_item(self, label, container, submenu_name=None, handler=None):
		"""Create menu item and pack in provided container."""
		menu_item = Gtk.ModelButton.new()
		menu_item.set_property('text', label)
		container.pack_start(menu_item, False, False, 0)

		submenu = None
		if submenu_name:
			menu_item.set_property('menu-name', submenu_name)
			if self._stack.get_child_by_name(submenu_name) is None:
				submenu = self._create_submenu(submenu_name, menu_item)

		if handler:
			menu_item.connect('clicked', handler)

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

	def prepare(self, path, provider):
		"""Allow popup to prepare for provided path."""
		self._provider = provider
		self._selected_path = path
		associations_manager = self._application.associations_manager
		mime_type = associations_manager.get_mime_type(path)

		# try to detect by content
		if associations_manager.is_mime_type_unknown(mime_type):
			try:
				data = associations_manager.get_sample_data(path, provider)
				mime_type = associations_manager.get_mime_type(data=data)
			except IsADirectoryError:
				mime_type = 'inode/directory'

		self.__update_emblem_selection(path)
		self.__populate_open_with_menu(path, mime_type)

	def show(self, widget, position, page='main'):
		"""Show menu relative to provided rectangle."""
		# self.__handle_popover_open()
		self._popover.set_relative_to(widget)
		self._popover.set_pointing_to(position)
		self._stack.set_visible_child_name(page)
		self._popover.popup()
