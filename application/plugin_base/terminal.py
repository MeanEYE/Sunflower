import gi

from gi.repository import Gtk, Gdk, Vte

try:
	from gi.repository import GConf as gconf
except:
	gconf = None

from plugin_base.plugin import PluginBase
from accelerator_group import AcceleratorGroup


class ButtonText:
	MENU = u'\u2699'
	TERMINAL = u'\u2605'
	ITEM_LIST = u'\u2600'


class TerminalType:
	VTE = 0
	EXTERNAL = 1


class CursorShape:
	BLOCK = 0
	IBEAM = 1
	UNDERLINE = 2


class Terminal(PluginBase):
	"""Base class for terminal based plugins

	This class provides access to VTE GTK+ widget. In cases where VTE is
	not present on the system you can use Gtk.Socket to embed external
	application.

	You are strongly encouraged to use predefined methods rather than
	defining your own.

	"""

	def __init__(self, parent, notebook, options):
		PluginBase.__init__(self, parent, notebook, options)

		# make options available in local namespace
		options = self._parent.options
		section = options.section('terminal')

		self._menu = None

		# change list icon
		self._title_bar.set_icon_from_name('terminal')

		# pack buttons
		self._title_bar.add_control(self._menu_button)

		# terminal button
		self._terminal_button = Gtk.Button()

		if options.get('tab_button_icons'):
			# set icon
			image_terminal = Gtk.Image()
			image_terminal.set_from_icon_name('terminal', Gtk.IconSize.MENU)
			self._terminal_button.set_image(image_terminal)
		else:
			# set text
			self._terminal_button.set_label(ButtonText.TERMINAL)

		self._terminal_button.set_focus_on_click(False)
		self._terminal_button.set_tooltip_text(_('Terminal'))
		self._terminal_button.connect('clicked', self._create_terminal)

		self._title_bar.add_control(self._terminal_button)

		# file list button
		self._file_list_button = Gtk.Button()

		if options.get('tab_button_icons'):
			# set icon
			image_folder = Gtk.Image()
			image_folder.set_from_icon_name('folder', Gtk.IconSize.MENU)
			self._file_list_button.set_image(image_folder)
		else:
			# set text
			self._file_list_button.set_label(ButtonText.ITEM_LIST)

		self._file_list_button.set_focus_on_click(False)
		self._file_list_button.set_tooltip_text(_('Open file list'))
		self._file_list_button.connect('clicked', self._create_file_list)

		self._title_bar.add_control(self._file_list_button)

		# create main object
		self._terminal_type = section.get('type')

		if self._terminal_type == TerminalType.VTE:
			self._terminal = Vte.Terminal.new()
			self._terminal.connect('window-title-changed', self._update_title)

			# unset drag source
			self._terminal.drag_source_unset()

			# configure terminal widget
			shape = section.get('cursor_shape')

			# Since Vte 0.38 Vte.TerminalCursorShape has been renamed Vte.CursorShape
			if hasattr(Vte, 'TerminalCursorShape'):
				cursorshape = Vte.TerminalCursorShape
			else:
				cursorshape = Vte.CursorShape

			shape_type = {
					CursorShape.BLOCK: cursorshape.BLOCK,
					CursorShape.IBEAM: cursorshape.IBEAM,
					CursorShape.UNDERLINE: cursorshape.UNDERLINE
				}
			self._terminal.set_cursor_shape(shape_type[shape])

			self._terminal.set_allow_bold(section.get('allow_bold'))
			self._terminal.set_mouse_autohide(section.get('mouse_autohide'))

			if section.get('use_system_font'):
				self.__set_system_font()

			else:
				self._terminal.set_font_from_string(section.get('font'))

		elif self._terminal_type == TerminalType.EXTERNAL:
			self._terminal = Gtk.Socket()

		else:
			# failsafe when VTE module is not present
			# NOTE: Cursor needs to be visible for 'close tab' accelerator.
			self._terminal = Gtk.TextView()
			text = _('\n\nPython VTE module is not installed on this system!')
			self._terminal.get_buffer().set_text(text)
			self._terminal.set_editable(False)
			self._terminal.set_justification(Gtk.Justification.CENTER)
			self._terminal.set_wrap_mode(Gtk.WrapMode.WORD)

		# terminal container
		if self._terminal_type == TerminalType.VTE:
			self._container = Gtk.ScrolledWindow()
			self._container.set_shadow_type(Gtk.ShadowType.IN)

			# apply scrollbar visibility
			show_scrollbars = section.get('show_scrollbars')
			scrollbar_vertical = self._container.get_vscrollbar()
			scrollbar_horizontal = self._container.get_hscrollbar()

			scrollbar_vertical.set_child_visible(show_scrollbars)
			scrollbar_horizontal.set_child_visible(False)

		elif self._terminal_type == TerminalType.EXTERNAL:
			self._container = Gtk.Viewport()
			self._container.set_shadow_type(Gtk.ShadowType.IN)

		# pack terminal
		self._container.add(self._terminal)
		self.pack_start(self._container, True, True, 0)

		# connect events to main object
		self._connect_main_object(self._terminal)

		# create menu
		self._create_menu()

	def __set_system_font(self, client=None, *args, **kwargs):
		"""Set system font to terminal"""

		if gconf is None:
			return

		path = '/desktop/gnome/interface'
		key = '{0}/monospace_font_name'.format(path)

		if client is None:
			if not hasattr(self._terminal, 'client'):
				# client wasn't assigned to widget, get default one and set events
				client = gconf.Client.get_default()
				client.add_dir(path, gconf.ClientPreloadType.PRELOAD_NONE)
				client.notify_add(key, self.__set_system_font)
				self._terminal.client = client

			else:
				# get assigned client
				client = self._terminal.client

		else:
			# try to get font and set it
			font_name = client.get_string(key)

			if font_name is not None:
				self._terminal.set_font_from_string(font_name)

	def _create_buttons(self):
		"""Create titlebar buttons."""
		options = self._parent.options

		# terminal menu button
		self._menu_button = Gtk.Button.new()

		if options.get('tab_button_icons'):
			# set icon
			image_menu = Gtk.Image.new_from_icon_name(Gtk.STOCK_EDIT, Gtk.IconSize.MENU)
			self._menu_button.set_image(image_menu)
		else:
			# set text
			self._menu_button = Gtk.Button(ButtonText.MENU)

		self._menu_button.set_focus_on_click(False)
		self._menu_button.set_tooltip_text(_('Terminal menu'))
		self._menu_button.connect('clicked', self._show_terminal_menu)

	def _update_title(self, widget, data=None):
		"""Update title with terminal window text"""
		self._change_title_text(self._terminal.get_window_title())
		return True

	def _update_terminal_status(self, widget, data=None):
		"""Update status bar text with terminal data"""
		self.update_status(self._terminal.get_status_line())

	def _create_terminal(self, widget, data=None):
		"""Create terminal tab in parent notebook"""
		self._parent.create_terminal_tab(self._notebook, self._options.copy())
		return True

	def _create_file_list(self, widget=None, data=None):
		"""Create file list in parent notebook"""
		DefaultList = self._parent.plugin_classes['file_list']
		self._parent.create_tab(self._notebook, DefaultList)
		return True

	def _create_menu(self):
		"""Create terminal menu"""
		self._menu = Gtk.Menu()

		# copy
		self._menu_item_copy = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_COPY)
		self._menu_item_copy.connect('activate', self._copy_selection)
		self._menu.append(self._menu_item_copy)

		# paste
		self._menu_item_paste = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_PASTE)
		self._menu_item_paste.connect('activate', self._paste_selection)
		self._menu.append(self._menu_item_paste)

		# show all items
		self._menu.show_all()

	def _prepare_menu(self):
		"""Prepare terminal menu before showing"""
		self._menu_item_copy.set_sensitive(self._terminal.get_has_selection())
		self._menu_item_paste.set_sensitive(self._parent.is_clipboard_text())

	def _duplicate_tab(self, widget, data=None):
		"""Creates new tab with same path"""
		PluginBase._duplicate_tab(self, None, self._options)
		return True

	def _get_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return pos_x, pos_y, True

	def _show_terminal_menu(self, widget, data=None):
		"""History button click event"""
		# prepare menu for drawing
		self._prepare_menu()

		# show the menu on calculated location

		self._menu.popup(None, None, self._get_menu_position, widget, 1, 0)

	def _configure_accelerators(self):
		"""Configure accelerator group"""
		group = AcceleratorGroup(self._parent)
		keyval = Gdk.keyval_from_name

		# give parent chance to register its own accelerator group
		PluginBase._configure_accelerators(self)

		# modify plugin accelerator group so we can have terminal auto-complete with tab
		plugin_group = self._accelerator_groups[0]
		plugin_group.disable_accelerator('focus_opposite_object')
		plugin_group.disable_accelerator('close_tab')

		# configure accelerator group
		group.set_name('terminal')
		group.set_title(_('Terminal'))

		# add all methods to group
		group.add_method('create_terminal', _('Create terminal tab'), self._create_terminal)
		group.add_method('copy_to_clipboard', _('Copy selection to clipboard'), self._copy_selection)
		group.add_method('paste_from_clipboard', _('Paste from clipboard'), self._paste_selection)
		group.add_method('focus_opposite_object', _('Focus opposite object'), self._parent.focus_opposite_object)
		group.add_method('close_tab', _('Close tab'), self._close_tab)

		# configure accelerators
		group.set_accelerator('create_terminal', keyval('z'), Gdk.ModifierType.CONTROL_MASK)
		group.set_accelerator('copy_to_clipboard', keyval('c'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
		group.set_accelerator('paste_from_clipboard', keyval('v'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
		group.set_accelerator('focus_opposite_object', keyval('Tab'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK)
		group.set_accelerator('close_tab', keyval('w'), Gdk.ModifierType.CONTROL_MASK)

		# add accelerator group to the list
		self._accelerator_groups.append(group)

	def _copy_selection(self, widget=None, data=None):
		"""Copy selection from terminal"""
		result = False

		if self._terminal_type == TerminalType.VTE and self._terminal.get_has_selection():
			self._terminal.copy_clipboard()
			result = True

		return result

	def _paste_selection(self, widget=None, data=None):
		"""Paste selection from terminal"""
		result = False

		if self._terminal_type == TerminalType.VTE:
			self._terminal.paste_clipboard()
			result = True

		return result

	def _drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
		"""Handle dropping files on file list"""
		text = selection_data.data

		# ask user what to do with data
		dialog = Gtk.MessageDialog(
								self._parent,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.QUESTION,
								Gtk.ButtonsType.YES_NO,
								_(
									'You are about to feed child process with '
									'following data. Are you sure?\n\n{0}'
								).format(text)
							)
		dialog.set_default_response(Gtk.ResponseType.YES)
		result = dialog.run()
		dialog.destroy()
		
		if result == Gtk.ResponseType.YES:
			self.feed_terminal(text)

		# notify source application about operation outcome
		drag_context.finish(result, False, timestamp)

	def _get_supported_drag_types(self):
		"""Return list of supported data for drag'n'drop events"""
		return [
				('text/plain', 0, 0),
			]

	def _get_supported_drag_actions(self):
		"""Return integer representing supported drag'n'drop actions"""
		return None

	def feed_terminal(self, text):
		"""Feed terminal process with specified text"""
		self._terminal.feed_child(text)

	def apply_settings(self):
		"""Apply terminal settings"""
		# let parent class do its work
		PluginBase.apply_settings(self)
		options = self._parent.options
		section = options.section('terminal')

		if self._terminal_type == TerminalType.VTE:
			# apply terminal scroll bar policy
			show_scrollbars = section.get('show_scrollbars')
			scrollbar_vertical = self._container.get_vscrollbar()
			scrollbar_vertical.set_child_visible(show_scrollbars)

			# apply cursor shape
			shape = section.get('cursor_shape')

			# Since Vte 0.38 Vte.TerminalCursorShape has been renamed Vte.CursorShape
			if hasattr(Vte, 'TerminalCursorShape'):
				cursorshape = Vte.TerminalCursorShape
			else:
				cursorshape = Vte.CursorShape

			shape_type = {
				CursorShape.BLOCK: cursorshape.BLOCK,
				CursorShape.IBEAM: cursorshape.IBEAM,
				CursorShape.UNDERLINE: cursorshape.UNDERLINE
			}
			self._terminal.set_cursor_shape(shape_type[shape])

			# apply allow bold
			self._terminal.set_allow_bold(section.get('allow_bold'))

			# apply mouse autohiding
			self._terminal.set_mouse_autohide(section.get('mouse_autohide'))

			# apply font
			if section.get('use_system_font'):
				self.__set_system_font()

			else:
				self._terminal.set_font_from_string(section.get('font'))

	def focus_main_object(self):
		"""Give focus to main object"""
		result = False

		if self._terminal_type == TerminalType.VTE:
			result = PluginBase.focus_main_object(self)

		elif self._terminal_type == TerminalType.EXTERNAL:
			self._main_object.child_focus(Gtk.DirectionType.TAB_FORWARD)
			result = True

		return result
