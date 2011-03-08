#!/usr/bin/env python

import gtk
import dbus
import os.path

from dbus.mainloop.glib import DBusGMainLoop

COL_DEVICE		= 0
COL_MOUNT_POINT = 1
COL_FILESYSTEM	= 2

class MountsManager:
	"""Class used for monitoring and managing mounts menu"""

	def __init__(self, application, menu_item):
		self._application = application
		self._menu_item = menu_item
		self._filesystems = []

		self._menu = gtk.Menu()
		self._menu_item.set_submenu(self._menu)

		# create dbus based monitor
		dbus_loop = DBusGMainLoop()
		self._session_bus = dbus.SessionBus(mainloop = dbus_loop)

		# connect dbus signals
		self._session_bus.add_signal_receiver(
										self._mount_added,
										'MountAdded',
										'org.gtk.Private.RemoteVolumeMonitor'
									)
		self._session_bus.add_signal_receiver(
										self._mount_removed,
										'MountRemoved',
										'org.gtk.Private.RemoteVolumeMonitor'
									)

		# load list of file systems recognized by the system
		self._load_valid_filesystems()

		# load list of currently mounted file systems
		self._load_mtab()

	def _load_valid_filesystems(self):
		"""Load filesystems recognized by the host OS"""
		with open('/proc/filesystems', 'r') as file:
			data = file.read().splitlines(False)

		for item in data:
			dev, name = item.split('\t')
			if dev != 'nodev': self._filesystems.append(name)

	def _load_mtab(self):
		"""Load list of mounted filesystems"""
		with open('/etc/mtab', 'r') as file:
			raw = file.read().splitlines(False)

		for item in raw:
			data = item.split()

			device = data[COL_DEVICE]
			mount_point = data[COL_MOUNT_POINT]
			filesystem = data[COL_FILESYSTEM]
			icon = self._application.icon_manager.get_mount_icon_name('')

			if mount_point != '/':
				label = os.path.basename(data[COL_MOUNT_POINT]).capitalize()
			else:
				label = mount_point

			if filesystem in self._filesystems:
				self._add_item(label, mount_point, device, icon)

	def _mount_added(self, sender, mount_id, data):
		"""Handle adding of new device"""
		label = data[1]
		icon = self._application.icon_manager.get_mount_icon_name(data[2])
		mount_point = data[4].split('://')[1]

		self._add_item(label, mount_point, mount_id, icon)

	def _mount_removed(self, sender, mount_id, data):
		"""Handle removal of device"""
		mount_point = data[4].split('://')[1]
		self._remove_item(mount_point)

	def _add_item(self, text, path, device, icon):
		"""Add new menu item to the list"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_data('path', path)
		menu_item.connect('activate', self._application._handle_bookmarks_click)
		menu_item.show()

		self._menu.append(menu_item)

	def _remove_item(self, mount_point):
		"""Remove item based on device name"""
		for item in self._menu.get_children():
			if item.get_data('path') == mount_point: self._menu.remove(item)
