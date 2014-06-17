import os
import sys
import gtk


class Indicator(object):
	"""This class provides access to application indicators in Gnome envirnoments"""

	def __init__(self, parent):
		self._parent = parent
		self._menu = gtk.Menu()
		self._create_menu_items()

		base_path = os.path.dirname(os.path.dirname(sys.argv[0]))

		self._icon = 'sunflower_64.png'
		self._icon_path = os.path.abspath(os.path.join(base_path, 'images'))
		self._indicator = None

		if self._parent.window_options.section('main').get('hide_on_close'):
			self._indicator = gtk.StatusIcon()

			self._indicator.set_from_file(os.path.join(self._icon_path, self._icon))
			self._indicator.connect('activate', self._status_icon_activate)
			self._indicator.connect('popup-menu', self._status_icon_popup_menu)

	def _create_menu_items(self):
		"""Create commonly used menu items in indicator"""
		# show window
		self._menu_show = self._parent.menu_manager.create_menu_item({
														'label': _('Sh_ow main window'),
														'callback': self._change_visibility,
														'data': True,
													})
		self._menu_show.hide()
		self._menu.append(self._menu_show)

		# hide window
		self._menu_hide = self._parent.menu_manager.create_menu_item({
														'label': _('_Hide main window'),
														'callback': self._change_visibility,
														'data': False,
													})
		self._menu.append(self._menu_hide)

		# close window option
		self._menu.append(self._parent.menu_manager.create_menu_item({'type': 'separator'}))
		self._menu.append(self._parent.menu_manager.create_menu_item({
														'label': _('_Quit'),
														'type': 'image',
														'callback': self._parent._destroy,
														'stock': gtk.STOCK_QUIT,
													}))

		# separator
		self._separator = self._parent.menu_manager.create_menu_item({'type': 'separator'})
		self._menu.append(self._separator)
		self._separator.hide()

	def _status_icon_activate(self, widget, data=None):
		"""Toggle visibility on status icon activate"""
		visible = not self._parent.get_visible()
		self._change_visibility(widget, visible)

	def _status_icon_popup_menu(self, widget, button, activate_time):
		"""Show popup menu on right click"""
		self._menu.popup(None, None, None, button, activate_time)

	def _change_visibility(self, widget, visible):
		"""Change main window visibility"""
		self._parent.set_visible(visible)
		self.adjust_visibility_items(visible)

	def adjust_visibility_items(self, visible):
		"""Adjust show/hide menu items"""
		self._menu_show.set_visible(not visible)
		self._menu_hide.set_visible(visible)

	def add_operation(self, widget, callback, data):
		"""Add operation to operations menu"""
		menu_item = gtk.MenuItem()
		menu_item.add(widget)

		if callback is not None:
			menu_item.connect('activate', callback, data)

		menu_item.show()
		self._separator.show()
		self._menu.append(menu_item)

		if hasattr(self._indicator, 'set_menu'):
			self._indicator.set_menu(self._menu)

		return menu_item
