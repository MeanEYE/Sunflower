#!/usr/bin/env python

import gtk

class Menus:
	"""Menu handling class

	This class also supports local cache for menus used in 'Open With'
	menu.

	"""
	_cache = {}

	def __init__(self, application):
		self._application = application

	def _item_normal(self, item):
		"""Create normal menu item"""
		return gtk.MenuItem(label = item['label'], use_underline = True)

	def _item_checkbox(self, item):
		"""Create checkbox menu item"""
		active = item['active'] if 'active' in item else False
		result = gtk.CheckMenuItem(label = item['label'], use_underline = True)
		result.set_active(active)
		
		return result

	def _item_radio(self, item):
		"""Create radio menu item"""
		if item.has_key('group'):
			group = item['group']
		else:
			group = None

		return gtk.RadioMenuItem(group, item['label'], use_underline = True)

	def _item_separator(self, item):
		"""Create separator"""
		return gtk.SeparatorMenuItem()

	def _item_image(self, item):
		"""Create normal menu item with image"""

		result = gtk.ImageMenuItem()
		image = gtk.Image()
		icon_manager = self._application.icon_manager

		if item.has_key('image'):
			image.set_from_pixbuf(icon_manager.get_icon_from_type(item['image']))

		elif item.has_key('stock'):
			image.set_from_stock(item['stock'], gtk.ICON_SIZE_MENU)

		try:
			result.set_label(item['label'])
			result.set_use_underline(True)
		except:
			# walk-around for problems with GTK+ on windows systems
			item = gtk.Label(item['label'])
			item.set_use_underline(True)
			item.set_alignment(0, 0.5)

			result.add(item)

		result.set_image(image)

		return result

	def _open_with_callback(self, widget, data=None):
		"""Callback event for menu items from 'open with' menu"""

		if data is not None:
			self._application.associations_manager.open_file_with_config(data['callback'], data['config'])

	def get_menu_item_from_config(self, config_file, callback):
		"""Retrieves menu item for selected config file

		This method is used to populate "open with" menu. All
		menu items are cached by the config name. Universal callback
		method defined in main application window is used.

		"""
		result = None

		if config_file in self._cache:
			# cached menu item, return
			result = self._cache[config_file]

		else:
			# get config
			config = self._application.associations_manager.get_association_config(config_file)

			# parse the config
			if config is not None:
				# get icon name
				if config.has_key('icon'):
					icon_name = config['icon']
				else:
					icon_name = None

				# get label
				label = 'Open with {0}'.format(config['name'])

				# create menu item
				if icon_name is not None:
					result = self._item_image({
											'image': icon_name,
											'label': label,
										})
				else:
					result = self._item_normal({
											'label': label,
										})

				data = {
					'config': config_file,
					'callback': callback
					}

				result.connect('activate', self._open_with_callback, data)
				result.show()

				self._cache[config_file] = result


		return result

	def create_menu_item(self, item):
		"""Create new menu item from definition"""

		# ensure we dont get confused with item type
		if item.has_key('type'):
			item_type = item['type']
		else:
			item_type = 'item'

		# item type creator calls
		create_item_call = {
			'item': self._item_normal,
			'checkbox': self._item_checkbox,
			'radio': self._item_radio,
			'separator': self._item_separator,
			'image': self._item_image
		}

		# create item
		new_item = create_item_call[item_type](item)

		# if item has children then make submenu
		if item_type is not 'separator' and item.has_key('submenu'):
			submenu = gtk.Menu()
			for sub_item in item['submenu']:
				submenu.append(self.create_menu_item(sub_item))
			new_item.set_submenu(submenu)

		# connect signals
		if item.has_key('callback'):
			data = None
			if item.has_key('data'): data = item['data']

			if item_type is 'checkbox':
				# connect checkbox event
				new_item.connect('toggled', item['callback'], data)

			elif item_type is 'radio':
				# connect group changed event
				new_item.connect('group-changed', item['callback'], data)

			else:
				# connect on click event
				new_item.connect('activate', item['callback'], data)
				
		elif not item.has_key('callback') and not item.has_key('submenu'):  
			# item doesn't have a callback, so we disable it
			new_item.set_sensitive(False)

		# if menu should be right aligned
		if item.has_key('right') and item['right']:
			new_item.set_right_justified(item['right'])

		new_item.show_all()
		return new_item
