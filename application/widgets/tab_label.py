import gtk
import pango


class TabLabel:
	"""Tab label wrapper class"""

	def __init__(self, application, parent):
		self._container = gtk.EventBox()

		self._application = application
		self._parent = parent
		
		# initialize tab events
		self._container.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
		self._container.connect('button-release-event', self._button_release_event)
		self._container.set_visible_window(False)

		# create interface
		self._hbox = gtk.HBox(False, 0)
		self._container.add(self._hbox)
		
		self._label = gtk.Label()
		self._label.set_max_width_chars(20)
		self._label.set_ellipsize(pango.ELLIPSIZE_END)

		self._lock_image = gtk.Image()
		self._lock_image.set_property('no-show-all', True)
		self._lock_image.set_from_icon_name('changes-prevent-symbolic', gtk.ICON_SIZE_MENU)

		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
		image_width, image_height = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
		image.show()

		style = gtk.RcStyle()
		style.xthickness = 0
		style.ythickness = 0

		self._button = gtk.Button()
		self._button.set_focus_on_click(False)
		self._button.add(image)
		self._button.set_relief(gtk.RELIEF_NONE)
		self._button.modify_style(style)
		self._button.connect('clicked', self._close_tab)
		self._button.set_property('no-show-all', True)
		self._button.set_size_request(image_width + 2, image_height + 2)

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
						'stock': gtk.STOCK_CLOSE,
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
		menu = gtk.Menu()

		for item in menu_items:
			item = menu_manager.create_menu_item(item)
			menu.append(item)

		menu.popup(None, None, None, 3, 0)
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
