import gtk

from widgets.settings_page import SettingsPage


class AssociationsOptions(SettingsPage):
	"""Mime-type associations options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'accelerators', _('Associations'))

		# create interface
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._associations = gtk.TreeStore(str, int, str)
		self._list = gtk.TreeView(model=self._associations)
		
		# create add menu
		self._add_menu = gtk.Menu()
		
		item_add_mime_type = gtk.MenuItem(label=_('Add mime type'))
		item_add_application = gtk.MenuItem(label=_('Add application to mime type'))
		
		self._add_menu.append(item_add_mime_type)
		self._add_menu.append(item_add_application)
		
		self._add_menu.show_all()
		
		# create controls
		hbox_controls = gtk.HBox(homogeneous=False, spacing=5)
		
		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self.__button_add_clicked)
		
		# pack interface
		container.add(self._list)
		
		hbox_controls.pack_start(button_add, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_end(hbox_controls, False, False, 0)

	def __button_add_clicked(self, widget, data=None):
		"""Handle clicking on add button"""
		self._add_menu.popup(
						None, None,
						self.__get_menu_position,
						1, 0, widget
					)
					
	def __get_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)
