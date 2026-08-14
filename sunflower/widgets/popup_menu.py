import os

from gi.repository import Gtk, Gdk, Gio, GLib

from sunflower.emblems import get_emblem_icon
from sunflower.plugin_base.monitor import MonitorSignals


class PopupMenu:
	"""Popup menu with path related functions."""

	def __init__(self, application, plugin):
		self._application = application
		self._plugin = plugin
		self._provider = None
		self._selected_path = None

		self._popover_visible = False
		self._show_emblems_pending = False
		self._menu_parent = None
		self._menu_rectangle = None

		# emblem selection grid is shared by both implementations
		self._emblem_map = {}
		self._emblems = Gtk.Grid.new()
		self._emblems.set_row_spacing(2)
		self._emblems.set_column_spacing(2)
		self._emblems.set_row_homogeneous(True)
		self._emblems.set_column_homogeneous(True)
		self.__populate_emblem_menu()

		if Gtk.get_major_version() == 3:
			self._create_widget_menu(application, plugin)

		else:
			self._create_model_menu(application, plugin)

	def _create_widget_menu(self, application, plugin):
		"""Create menu from individual widgets inside of a stack. (GTK 3)"""
		self._popover = Gtk.Popover.new()
		self._popover.get_style_context().add_class('menu')
		set_border_width(self._popover, 5)
		self._popover.set_size_request(250, -1)
		self._popover.set_modal(True)
		self._popover.connect('closed', self.__handle_popover_close)

		left_object = application.get_left_object()
		self._popover.set_position(Gtk.PositionType.RIGHT if plugin is left_object else Gtk.PositionType.LEFT)

		# create stack to allow submenus
		self._stack = Gtk.Stack.new()
		self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
		self._stack.set_vhomogeneous(False)
		self._stack.set_interpolate_size(True)
		self._popover.add(self._stack)

		# main menu box
		box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		self._stack.add_named(box, 'main')

		# operation items
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
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
		button, menu = self._create_menu_item(_('Emblems'), box, 'emblems')
		menu.pack_start(self._emblems, True, True, 0)

		box.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), False, False, 2)
		self._create_menu_item(_('Properties'), box, handler=plugin._item_properties)

		# show all widgets
		self._stack.show_all()

	def _create_model_menu(self, application, plugin):
		"""Create menu from menu model. (GTK 4)

		Rows must come from a Gio.Menu so the theme creates real model
		buttons; hand-rolled Gtk.Button rows never match the `modelbutton`
		styling. Actions simply forward to the existing plugin handlers.

		"""
		self._actions = Gio.SimpleActionGroup.new()
		self._open_with_actions = []

		for name, handler in (
				('open', plugin._execute_selected_item),
				('open-tab', plugin._open_in_new_tab),
				('copy-to-other', plugin._copy_files),
				('move-to-other', plugin._move_files),
				('send-to', plugin._send_to),
				('make-link', plugin._create_link),
				('copy-file-name', plugin.copy_selected_item_name_to_clipboard),
				('copy-path', plugin.copy_selected_path_to_clipboard),
				('properties', plugin._item_properties),
				):
			action = Gio.SimpleAction.new(name, None)
			action.connect('activate', self.__handle_action, handler)
			self._actions.add_action(action)

		# emblem grid can not be a submenu page, it opens as its own popover
		action = Gio.SimpleAction.new('show-emblems', None)
		action.connect('activate', self.__handle_emblems_action)
		self._actions.add_action(action)

		menu = Gio.Menu.new()

		# clipboard operations are rendered as a row of icon buttons
		operations_section = Gio.Menu.new()
		operations_item = Gio.MenuItem.new(None, None)
		operations_item.set_attribute_value('custom', GLib.Variant.new_string('operations'))
		operations_section.append_item(operations_item)
		menu.append_section(None, operations_section)

		# options for opening path
		open_section = Gio.Menu.new()
		open_section.append(_('Open'), 'popup.open')
		open_section.append(_('Open in new tab'), 'popup.open-tab')
		self._open_with_menu = Gio.Menu.new()
		open_section.append_submenu(_('Open with'), self._open_with_menu)
		menu.append_section(None, open_section)

		transfer_section = Gio.Menu.new()
		transfer_section.append(_('Copy to other'), 'popup.copy-to-other')
		transfer_section.append(_('Move to other'), 'popup.move-to-other')
		menu.append_section(None, transfer_section)

		# path operations
		path_menu = Gio.Menu.new()
		path_section = Gio.Menu.new()
		if self._application.NAUTILUS_SEND_TO_INSTALLED:
			path_section.append(_('Send to...'), 'popup.send-to')
		path_section.append(_('Make link'), 'popup.make-link')
		path_menu.append_section(None, path_section)

		clipboard_section = Gio.Menu.new()
		clipboard_section.append(_('Copy file name'), 'popup.copy-file-name')
		clipboard_section.append(_('Copy path'), 'popup.copy-path')
		path_menu.append_section(None, clipboard_section)

		# additional options
		other_section = Gio.Menu.new()
		other_section.append_submenu(_('Path operations'), path_menu)
		other_section.append(_('Emblems'), 'popup.show-emblems')
		menu.append_section(None, other_section)

		properties_section = Gio.Menu.new()
		properties_section.append(_('Properties'), 'popup.properties')
		menu.append_section(None, properties_section)

		self._popover = Gtk.PopoverMenu.new_from_model(menu)
		self._popover.set_size_request(250, -1)
		self._popover.insert_action_group('popup', self._actions)
		self._popover.connect('closed', self.__handle_popover_close)

		left_object = application.get_left_object()
		position = Gtk.PositionType.RIGHT if plugin is left_object else Gtk.PositionType.LEFT
		self._popover.set_position(position)

		# create row of icon buttons for clipboard operations
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
		hbox.get_style_context().add_class('inline-buttons')

		for icon_name, handler in (
				('edit-cut-symbolic', plugin._cut_files_to_clipboard),
				('edit-copy-symbolic', plugin._copy_files_to_clipboard),
				('edit-paste-symbolic', plugin._paste_files_from_clipboard),
				('edit-delete-symbolic', plugin._delete_files),
				('document-edit-symbolic', plugin._rename_file),
				):
			button = Gtk.Button.new_from_icon_name(icon_name)
			button.get_style_context().add_class('image-button')
			button.get_style_context().add_class('model')
			button.set_hexpand(True)
			button.connect('clicked', self.__handle_operation_click, handler)
			hbox.append(button)

		self._popover.add_child(hbox, 'operations')

		# emblem selection lives in a separate popover since a widget can
		# not be inserted into a menu model
		self._emblem_popover = Gtk.Popover.new()
		set_border_width(self._emblems, 5)
		self._emblem_popover.set_child(self._emblems)
		self._emblem_popover.set_position(position)
		self._emblem_popover.connect('closed', self.__handle_emblem_popover_close)

	def __populate_emblem_menu(self):
		"""Populate emblem menu with options."""
		emblem_list = self._application.emblem_manager.get_available_emblems()
		for index, emblem in enumerate(emblem_list):
			icon_name = get_emblem_icon(emblem)

			if icon_name is None:
				continue

			image = Gtk.Image.new()
			if Gtk.get_major_version() == 3:
				image.set_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)

			else:
				image.set_from_icon_name(icon_name)
				image.set_pixel_size(24)

			button = Gtk.ToggleButton.new()
			if Gtk.get_major_version() == 3:
				button.add(image)

			else:
				button.set_child(image)
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
		active_emblems = manager.get_emblems(path, item_name) or ()

		for emblem, button in self._emblem_map.items():
			button.handler_block_by_func(self.__handle_emblem_toggle)
			button.set_active(emblem in active_emblems)
			button.handler_unblock_by_func(self.__handle_emblem_toggle)

	def __populate_open_with_menu(self, path, mime_type):
		"""Populate submenu for application selection."""
		associations_manager = self._application.associations_manager
		application_list = associations_manager.get_application_list_for_type(mime_type)
		custom_commands = self._application.association_options.get(mime_type)

		if Gtk.get_major_version() != 3:
			self.__populate_open_with_model(path, application_list, custom_commands)
			return

		container = self._stack.get_child_by_name('open-with')

		# remove old items skipping first which returns to main menu
		old_items = container.get_children()[1:]
		list(map(lambda item: container.remove(item), old_items))

		# populate list with globally assigned applications
		for application in application_list:
			menu_item = Gtk.ModelButton.new()
			menu_item.set_property('text', application.name)

			# assign icon if available
			if application.icon:
				icon = Gio.Icon.new_for_string(application.icon)
				menu_item.set_property('icon', icon)
				menu_item.get_child().get_children()[0].set_visible(True)  # show it the hard way

			# connect click handler
			handler_data = {
					'selection': [path,],
					'application': application
					}
			menu_item.connect('clicked', self.__handle_open_with_click, handler_data)
			container.pack_start(menu_item, False, True, 0)

		# add custom associations to the menu
		if custom_commands:
			# add menu separator so user can differentiate
			separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
			container.pack_start(separator, False, True, 0)

			# add custom commands to menu
			for custom_command in custom_commands:
				# create menu item
				menu_item = Gtk.ModelButton.new()
				menu_item.set_property('text', custom_command['name'])

				# prepare data for item
				handler_data = {
						'selection': [path,],
						'command': custom_command['command']
						}
				menu_item.connect('clicked', self.__handle_open_with_click, handler_data)
				container.pack_start(menu_item, False, True, 0)

		container.show_all()

	def __populate_open_with_model(self, path, application_list, custom_commands):
		"""Rebuild menu model for application selection. (GTK 4)"""
		self._open_with_menu.remove_all()

		# remove actions from previous selection
		for action_name in self._open_with_actions:
			self._actions.remove_action(action_name)
		self._open_with_actions = []

		def add_option(section, label, icon_name, handler_data):
			action_name = 'open-with-{0}'.format(len(self._open_with_actions))
			action = Gio.SimpleAction.new(action_name, None)
			action.connect('activate', self.__handle_open_with_activate, handler_data)
			self._actions.add_action(action)
			self._open_with_actions.append(action_name)

			menu_item = Gio.MenuItem.new(label, 'popup.{0}'.format(action_name))
			if icon_name:
				try:
					menu_item.set_icon(Gio.Icon.new_for_string(icon_name))
				except GLib.Error:
					pass
			section.append_item(menu_item)

		# populate list with globally assigned applications
		application_section = Gio.Menu.new()
		for application in application_list:
			handler_data = {
					'selection': [path,],
					'application': application
					}
			add_option(application_section, application.name, application.icon, handler_data)
		self._open_with_menu.append_section(None, application_section)

		# add custom associations in their own section so user can differentiate
		if custom_commands:
			custom_section = Gio.Menu.new()
			for custom_command in custom_commands:
				handler_data = {
						'selection': [path,],
						'command': custom_command['command']
						}
				add_option(custom_section, custom_command['name'], None, handler_data)
			self._open_with_menu.append_section(None, custom_section)

	def __handle_open_with_click(self, widget, data):
		"""Handle clicking on application in open with menu."""
		associations_manager = self._application.associations_manager

		if 'application' in data:
			associations_manager.open_file(data['selection'], application_info=data['application'])

		elif 'command' in data:
			associations_manager.open_file(data['selection'], exec_command=data['command'])

		return True

	def __handle_open_with_activate(self, action, parameter, data):
		"""Handle activating application action in open with menu. (GTK 4)"""
		self._popover_visible = False
		self.__handle_open_with_click(None, data)

	def __handle_action(self, action, parameter, handler):
		"""Forward menu action to plugin handler. (GTK 4)

		Handlers check `visible` to avoid reacting to key presses meant for
		the menu, so the flag is cleared before the handler runs.

		"""
		self._popover_visible = False
		self._popover.popdown()
		handler(None)

	def __handle_operation_click(self, widget, handler):
		"""Handle clicking on button in operations row. (GTK 4)"""
		self._popover_visible = False
		self._popover.popdown()
		handler(widget)

	def __handle_emblems_action(self, action, parameter):
		"""Switch from main menu to emblem popover. (GTK 4)"""
		self._show_emblems_pending = True
		self._popover.popdown()
		self.__show_emblem_popover()

	def __show_emblem_popover(self):
		"""Show emblem selection popover at last menu position. (GTK 4)"""
		self._show_emblems_pending = False
		self._popover_visible = True

		self.__attach_popover(self._emblem_popover, self._menu_parent)
		self._emblem_popover.set_pointing_to(self._menu_rectangle)
		self._emblem_popover.popup()

	def __handle_popover_open(self):
		"""Handle popover opening."""
		self._popover_visible = True

	def __handle_popover_close(self, widget, data=None):
		"""Handle popover closing."""
		self._popover_visible = False

		# emblem popover is about to open for the same selection
		if self._show_emblems_pending:
			return

		# GTK 3 modal popover returns focus on its own, GTK 4 hands it to
		# the nearest focusable ancestor instead of the item list
		if Gtk.get_major_version() != 3:
			self._plugin.focus_main_object()

		# remove references to help clear memory
		self._provider = None
		self._selected_path = None

	def __handle_emblem_popover_close(self, widget, data=None):
		"""Handle emblem popover closing. (GTK 4)"""
		self._popover_visible = False
		self._provider = None
		self._selected_path = None
		self._plugin.focus_main_object()

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
		"""Create menu item and pack in provided container. (GTK 3)"""
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
		"""Create submenu for provided button and return its container. (GTK 3)"""
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
			container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
			container.pack_start(back_button, False, False, 0)
		self._stack.add_named(container, name)

		return container

	def __attach_popover(self, popover, parent):
		"""Make sure popover is parented to provided widget. (GTK 4)"""
		current_parent = popover.get_parent()

		if current_parent is parent:
			return

		if current_parent is not None:
			popover.unparent()
		popover.set_parent(parent)

	def _translate_rectangle(self, source, target, rectangle):
		"""Return rectangle expressed in target widget coordinates. (GTK 4)"""
		if source is target:
			return rectangle

		# result is either (x, y) or (valid, x, y) depending on binding version
		translated = source.translate_coordinates(target, rectangle.x, rectangle.y)

		if not translated or len(translated) < 2:
			return rectangle

		x, y = translated[-2:]

		result = Gdk.Rectangle()
		result.x = x
		result.y = y
		result.width = rectangle.width
		result.height = rectangle.height

		return result

	def prepare(self, path, provider):
		"""Allow popup to prepare for provided path."""
		self._provider = provider
		self._selected_path = path

		# parent directory row has no path to inspect
		if path is None:
			return

		associations_manager = self._application.associations_manager
		mime_type = associations_manager.get_mime_type(path)

		# try to detect by content
		if associations_manager.is_mime_type_unknown(mime_type):
			try:
				data = associations_manager.get_sample_data(path, provider)
				mime_type = associations_manager.get_mime_type(data=data)
			except GLib.Error as error:
				if error.matches(Gio.io_error_quark(), Gio.IOErrorEnum.IS_DIRECTORY):
					mime_type = 'inode/directory'
				else:
					raise error
			except IsADirectoryError:
				mime_type = 'inode/directory'

		self.__update_emblem_selection(path)
		self.__populate_open_with_menu(path, mime_type)

	def show(self, widget, position, page='main'):
		"""Show menu relative to provided rectangle."""
		self.__handle_popover_open()

		if Gtk.get_major_version() == 3:
			self._popover.set_relative_to(widget)
			self._popover.set_pointing_to(position)
			self._stack.set_visible_child_name(page)
			self._popover.popup()
			return

		# popover can not be hosted by a tree view, inserting one into its
		# css node tree fails and leaves the popover without working states;
		# scrolled window focus traversal only descends into its scrollable
		# child, so a popover parented there loses arrow key navigation
		parent = widget

		while parent is not None and isinstance(parent, (Gtk.TreeView, Gtk.ScrolledWindow)):
			parent = parent.get_parent()

		if parent is None:
			parent = widget

		self._menu_parent = parent
		self._menu_rectangle = self._translate_rectangle(widget, parent, position)

		if page == 'emblems':
			self.__show_emblem_popover()
			return

		self.__attach_popover(self._popover, parent)
		self._popover.set_pointing_to(self._menu_rectangle)
		self._popover.popup()

		# popping up resets menu back to main page
		if page == 'open-with':
			self._popover.set_property('visible-submenu', _('Open with'))

	visible = property(lambda self: self._popover_visible)
