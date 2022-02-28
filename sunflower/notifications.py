from __future__ import absolute_import

import os
import sys

try:
	import gi
	gi.require_version('Notify', '0.7')
	from gi.repository import Notify
except:
	Notify = None

from sunflower import common


class NotificationManager:
	"""Notification manager provides OS specific notification
	methods to plugins and operations.
	"""

	available = Notify is not None

	def __init__(self, application):
		# initialize OS notification system
		if not self.available:
			return

		self._application = application

		Notify.init('sunflower')

		# decide which icon to use
		if self._application.icon_manager.has_icon('sunflower'):
			# use global icon
			self._default_icon = 'sunflower'

		else:
			# use local icon
			icon_file = os.path.join(os.path.dirname(common.get_static_assets_directory()), 'images', 'sunflower_64.png')
			self._default_icon = 'file://{0}'.format(icon_file)

	def notify(self, title, text, icon=None):
		"""Make system notification"""
		if not self.available \
		or not self._application.options.get('show_notifications'):
			return  # if notifications are disabled or unavailable

		if icon is None:  # make sure we show notification with icon
			icon = self._default_icon

		try:
			# create notification object
			notification = Notify.Notification.new(title, text, icon)

			# show notification
			notification.show()

		except:
			# we don't need to handle errors from notification daemon
			pass
