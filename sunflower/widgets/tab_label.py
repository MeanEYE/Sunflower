from gi.repository import Gtk, Pango, Gdk


class TabLabel:
	"""Tab label wrapper class"""

	MAX_CHARS=20

	def __init__(self, application, parent):
		self._container = Gtk.EventBox.new()

		self._application = application
		self._parent = parent

		# initialize tab events
		self._container.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
		self._container.connect('button-release-event', self._button_release_event)
		self._container.set_visible_window(False)

		# create interface
		self._hbox = Gtk.HBox(homogeneous=False, spacing=0)
		self._container.add(self._hbox)

		self._label = Gtk.Label.new()
		self._label.set_single_line_mode(True)

		self._lock_image = Gtk.Image()
		self._lock_image.set_property('no-show-all', True)
		self._lock_image.set_from_icon_name('changes-prevent-symbolic', Gtk.IconSize.MENU)

		self._button = Gtk.Button.new_from_icon_name('window-close-symbolic', Gtk.IconSize.MENU)
		self._button.set_focus_on_click(False)
		self._button.connect('clicked', self._close_tab)
		self._button.set_property('no-show-all', True)
		self._button.get_style_context().add_class('sunflower-close-tab')
		self._button.get_style_context().add_class('flat')

		# pack interface
		self._hbox.pack_start(self._lock_image, False, False, 0)
		self._hbox.pack_start(self._label, True, True, 0)
		self._hbox.pack_start(self._button, False, False, 0)

		# show controls
		if self._application.options.get('tab_close_button'):
			self._button.show()
			self._hbox.set_spacing(3)

		self._container.show_all()

	def _close_tab(self, widget=None, mode=None):
		"""Handle clicking on close button"""
		if mode == 'all':
			self._application.close_all_tabs(self._parent._notebook)

		elif mode == 'other':
			self._application.close_all_tabs(self._parent._notebook, self._parent)

		else:
			self._parent._close_tab()

	def _toggle_lock_tab(self, widget=None, data=None):
		"""Toggle tab lock state."""
		if self._parent.is_tab_locked():
			self._parent.unlock_tab()

		else:
			self._parent.lock_tab()

	def _show_menu(self):
		"""Show tab menu."""
		menu_manager = self._application.menu_manager
		menu_items = (
					{
						'label': _('Unlock') if self._parent.is_tab_locked() else _('Lock'),
						'callback': self._toggle_lock_tab,
					},
					{
						'label': _('Duplicate tab'),
						'callback': self._parent._duplicate_tab,
					},
					{
						'label': _('Move to opposite panel'),
						'callback': self._parent._move_tab,
					},
					{
						'type': 'separator'
					},
					{
						'label': _('Close Tab'),
						'type': 'image',
						'stock': Gtk.STOCK_CLOSE,
						'callback': self._close_tab,
					},
					{
						'label': _('Close All'),
						'data': 'all',
						'callback': self._close_tab,
					},
					{
						'label': _('Close Other Tabs'),
						'data': 'other',
						'callback': self._close_tab,
					},
				)

		# create menu
		menu = Gtk.Menu()

		for item in menu_items:
			item = menu_manager.create_menu_item(item)
			menu.append(item)

		menu.popup(None, None, None, None, 3, 0)
		menu.show_all()

	def _button_release_event(self, widget, event, data=None):
		"""
		Handle clicking on the tab itself, when middle button is pressed
		the tab is closed.
		"""
		result = False

		if event.button == 2:
			self._close_tab()
			result = True

		elif event.button == 3:
			self._show_menu()
			result = False

		return result

	def set_text(self, text):
		"""Set label text"""
		if len(text)>self.MAX_CHARS:
			self._label.set_width_chars(self.MAX_CHARS)
			self._label.set_ellipsize(Pango.EllipsizeMode.END)
		else:
			self._label.set_width_chars(-1)
			self._label.set_ellipsize(Pango.EllipsizeMode.NONE)
		self._label.set_text(text)

	def lock_tab(self):
		"""Set label state to locked"""
		self._lock_image.show()

	def unlock_tab(self):
		"""Delete * from label"""
		self._lock_image.hide()

	def get_container(self):
		"""Return container to be added to notebook"""
		return self._container

	def apply_settings(self):
		"""Apply global settings to tab label"""
		if self._application.options.get('tab_close_button'):
			self._button.show()
			self._hbox.set_spacing(3)

		else:
			self._button.hide()
			self._hbox.set_spacing(0)
