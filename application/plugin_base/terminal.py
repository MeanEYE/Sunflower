import gtk

try:
	import vte
except:
	vte = None

from plugin import PluginBase

# button text constants
BUTTON_TEXT_MENU 	= u'\u2699'
BUTTON_TEXT_RECYCLE = u'\u267B'


class Terminal(PluginBase):
	"""Base class for terminal based plugins

	This class will provide basic VTE GTK+ component wrapped in VBox.

	You are strongly encouraged to use predefined methods rather than
	defining your own.

	"""

	_vte_present = False

	def __init__(self, parent, notebook, path=None):
		PluginBase.__init__(self, parent, notebook, path)

		self._menu = None

		# global key event handlers with modifier switches (control, alt, shift)
		self._key_handlers = {
			'Tab': {
					'001': self._parent.focus_oposite_list,
					'100': self._notebook_next_tab,
					'101': self._notebook_previous_tab,
				},
			'ISO_Left_Tab': {  # CTRL+SHIFT+Tab produces ISO_Left_Tab
					'101': self._notebook_previous_tab,
				},
			'w': {
					'100': self._close_tab,
				},
			't': {
					'100': self._duplicate_tab,
				},
			'z': {
					'100': self._create_terminal,
				},
			'c': {
					'101': self._copy_selection,
				},
			'v': {
					'101': self._paste_selection,
				},
			'F11': {
					'000': self._parent.toggle_fullscreen
				},
		}

		# change list icon
		self._title_bar.set_icon_from_name('terminal')

		# recycle button
		self._recycle_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			# set icon
			image_recycle = gtk.Image()
			image_recycle.set_from_icon_name('reload', gtk.ICON_SIZE_MENU)
			self._recycle_button.set_image(image_recycle)
		else:
			# set text
			self._recycle_button = gtk.Button(BUTTON_TEXT_RECYCLE)

		self._recycle_button.set_focus_on_click(False)
		self._recycle_button.set_tooltip_text(_('Recycle terminal'))
		self._recycle_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._recycle_button.connect('clicked', self._recycle_terminal)

		# terminal menu button
		self._menu_button = gtk.Button()

		if self._parent.options.getboolean('main', 'tab_button_icons'):
			# set icon
			image_menu = gtk.Image()
			image_menu.set_from_icon_name(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU)
			self._menu_button.set_image(image_menu)
		else:
			# set text
			self._menu_button = gtk.Button(BUTTON_TEXT_MENU)

		self._menu_button.set_focus_on_click(False)
		self._menu_button.set_tooltip_text(_('Terminal menu'))
		self._menu_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._menu_button.connect('clicked', self._show_terminal_menu)

		# pack buttons
		self._title_bar.add_control(self._recycle_button)
		self._title_bar.add_control(self._menu_button)

		if vte is not None:
			self._vte_present = True
			self._terminal = vte.Terminal()
			self._terminal.connect('window-title-changed', self._update_title)
		else:
			self._terminal = gtk.Label(_('Python VTE module is not installed on this system!'))

		# terminal container
		self._container = gtk.ScrolledWindow()
		self._container.set_shadow_type(gtk.SHADOW_IN)

		policy = (
				gtk.POLICY_NEVER,
				gtk.POLICY_AUTOMATIC
			)[self._parent.options.getboolean('main', 'terminal_scrollbars')]
		self._container.set_policy(policy, policy)

		# pack terminal
		self._container.add(self._terminal)
		self.pack_start(self._container, True, True, 0)

		# connect events to main object
		self._connect_main_object(self._terminal)

		# create menu
		self._create_menu()

	def _update_title(self, widget, data=None):
		"""Update title with terminal window text"""
		self._change_title_text(self._terminal.get_window_title())
		return True

	def _update_terminal_status(self, widget, data=None):
		"""Update status bar text with terminal data"""
		self.update_status(self._terminal.get_status_line())

	def _recycle_terminal(self, widget, data=None):
		"""Recycle terminal"""
		pass

	def _create_terminal(self, widget, data=None):
		"""Create terminal tab in parent notebook"""
		self._parent.create_terminal_tab(self._notebook, self.path)
		return True

	def _create_menu(self):
		"""Create terminal menu"""
		self._menu = gtk.Menu()

		# copy
		self._menu_item_copy = gtk.ImageMenuItem(stock_id=gtk.STOCK_COPY)
		self._menu_item_copy.connect('activate', self._copy_selection)
		self._menu.append(self._menu_item_copy)

		# paste
		self._menu_item_paste = gtk.ImageMenuItem(stock_id=gtk.STOCK_PASTE)
		self._menu_item_paste.connect('activate', self._paste_selection)
		self._menu.append(self._menu_item_paste)

		# show all items
		self._menu.show_all()
		self._menu.connect('hide', self._handle_menu_hide)

	def _prepare_menu(self):
		"""Prepare terminal menu before showing"""
		self._menu_item_copy.set_sensitive(self._terminal.get_has_selection())
		self._menu_item_paste.set_sensitive(self._parent.is_clipboard_text())

	def _handle_menu_hide(self, widget, data=None):
		"""Handle hide event for terminal menu"""
		self._disable_object_block()
		oposite_list = self._parent.get_oposite_list(self)
		oposite_list._disable_object_block()

	def _duplicate_tab(self, widget, data=None):
		"""Creates new tab with same path"""
		PluginBase._duplicate_tab(self, None, self.path)
		return True

	def _get_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def _show_terminal_menu(self, widget, data=None):
		"""History button click event"""
		# prepare menu for drawing
		self._prepare_menu()

		# show the menu on calculated location
		self._enable_object_block()
		oposite_list = self._parent.get_oposite_list(self)
		oposite_list._enable_object_block()

		self._menu.popup(
						None, None,
						self._get_menu_position,
						1, 0, widget
					)

	def _copy_selection(self, widget=None, data=None):
		"""Copy selection from terminal"""
		if self._terminal.get_has_selection():
			self._terminal.copy_clipboard()

		return True

	def _paste_selection(self, widget=None, data=None):
		"""Paste selection from terminal"""
		self._terminal.paste_clipboard()
		return True

	def feed_terminal(self, text):
		"""Feed terminal process with specified text"""
		self._terminal.feed_child(text)

	def apply_settings(self):
		"""Apply terminal settings"""
		# let parent class do its work
		PluginBase.apply_settings(self)

		# button relief
		self._recycle_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		self._menu_button.set_relief((
									gtk.RELIEF_NONE,
									gtk.RELIEF_NORMAL
									)[self._parent.options.getint('main', 'button_relief')])

		# apply terminal scrollbar policy
		policy = (
				gtk.POLICY_NEVER,
				gtk.POLICY_AUTOMATIC
			)[self._parent.options.getboolean('main', 'terminal_scrollbars')]
		self._container.set_policy(policy, policy)

