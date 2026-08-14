from gi.repository import Gtk, Pango, Gdk, Gio


class TabLabel:
	"""Tab label wrapper class"""

	MAX_CHARS=20

	def __init__(self, application, parent):
		self._application = application
		self._parent = parent
		self._menu_popover = None

		# create interface
		self._hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

		if Gtk.get_major_version() == 3:
			self._container = Gtk.EventBox.new()

			# initialize tab events
			self._container.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
			self._container.connect('button-release-event', self._button_release_event)
			self._container.set_visible_window(False)

			self._container.add(self._hbox)

		else:
			# GTK 4 removed event boxes, clicks arrive through a gesture instead
			self._container = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

			gesture = Gtk.GestureClick.new()
			gesture.set_button(0)
			gesture.connect('released', self._button_released)
			self._container.add_controller(gesture)

			self._container.append(self._hbox)

		self._label = Gtk.Label.new()
		self._label.set_single_line_mode(True)

		self._lock_image = Gtk.Image()

		if Gtk.get_major_version() == 3:
			self._lock_image.set_property('no-show-all', True)
			self._lock_image.set_from_icon_name('changes-prevent-symbolic', Gtk.IconSize.MENU)

			self._button = Gtk.Button.new_from_icon_name('window-close-symbolic', Gtk.IconSize.MENU)

		else:
			# GTK 4 icon helpers take no size, widgets are hidden directly
			self._lock_image.hide()
			self._lock_image.set_from_icon_name('changes-prevent-symbolic')

			self._button = Gtk.Button.new_from_icon_name('window-close-symbolic')

		self._button.set_focus_on_click(False)
		self._button.connect('clicked', self._close_tab)

		if Gtk.get_major_version() == 3:
			self._button.set_property('no-show-all', True)

		else:
			self._button.hide()

		self._button.get_style_context().add_class('sunflower-close-tab')
		self._button.get_style_context().add_class('flat')

		# pack interface
		if Gtk.get_major_version() == 3:
			self._hbox.pack_start(self._lock_image, False, False, 0)
			self._hbox.pack_start(self._label, True, True, 0)
			self._hbox.pack_start(self._button, False, False, 0)

		else:
			self._hbox.append(self._lock_image)
			self._label.set_hexpand(True)
			self._hbox.append(self._label)
			self._hbox.append(self._button)

			# label fills the tab but must not make the tab itself expand
			self._hbox.set_hexpand(False)
			self._container.set_hexpand(False)

		# show controls
		if self._application.options.get('tab_close_button'):
			self._button.show()
			self._hbox.set_spacing(3)

		if Gtk.get_major_version() == 3:
			self._container.show_all()

	def _button_released(self, gesture, count, x, y):
		"""Handle mouse button release on tab label (GTK 4)"""
		return self._handle_button_release(gesture.get_current_button())

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
		close_item = {
					'label': _('Close Tab'),
					'callback': self._close_tab,
				}

		# stock items exist only in GTK 3
		if Gtk.get_major_version() == 3:
			close_item['type'] = 'image'
			close_item['stock'] = Gtk.STOCK_CLOSE

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
					close_item,
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

		if Gtk.get_major_version() == 3:
			# create menu
			menu_manager = self._application.menu_manager
			menu = Gtk.Menu()

			for item in menu_items:
				item = menu_manager.create_menu_item(item)
				menu.append(item)

			menu.popup_at_pointer()
			menu.show_all()
			return

		# GTK 4 menus are built from a model with actions
		actions = Gio.SimpleActionGroup.new()
		model = Gio.Menu.new()
		section = Gio.Menu.new()

		for index, item in enumerate(menu_items):
			if item.get('type') == 'separator':
				model.append_section(None, section)
				section = Gio.Menu.new()
				continue

			action_name = 'item-{0}'.format(index)
			action = Gio.SimpleAction.new(action_name, None)
			action.connect('activate', self._handle_menu_action, item)
			actions.add_action(action)
			section.append(item['label'], 'tab-menu.{0}'.format(action_name))

		model.append_section(None, section)

		# popover is created on first use and reused with fresh model
		if self._menu_popover is None:
			self._menu_popover = Gtk.PopoverMenu.new_from_model(model)
			self._menu_popover.set_parent(self._container)

		else:
			self._menu_popover.set_menu_model(model)

		self._menu_popover.insert_action_group('tab-menu', actions)
		self._menu_popover.popup()

	def _handle_menu_action(self, action, parameter, item):
		"""Forward menu action to item callback. (GTK 4)"""
		item['callback'](None, item.get('data'))

	def _button_release_event(self, widget, event, data=None):
		"""
		Handle clicking on the tab itself, when middle button is pressed
		the tab is closed.
		"""
		return self._handle_button_release(event.button)

	def _handle_button_release(self, button):
		"""Handle released mouse button regardless of the toolkit version"""
		result = False

		if button == 2:
			self._close_tab()
			result = True

		elif button == 3:
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
