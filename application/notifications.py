import os
import sys
import pynotify

class NotificationManager:
	"""Notification manager provides OS specific notification
	methods to plugins and operations.
	"""

	def __init__(self, application):
		self._application = application

		# initialize os notification system
		pynotify.init('sunflower')

		# decide which icon to use
		if self._application.icon_manager.has_icon('sunflower'):
			# use global icon
			self._default_icon = 'sunflower'

		else:
			# use local icon
			icon_file = os.path.abspath(os.path.join(
			                    os.path.dirname(sys.argv[0]),
			                    'images',
			                    'sunflower_hi-def_64x64.png'
			                ))
			self._default_icon = 'file://{0}'.format(icon_file)

	def notify(self, title, text, icon=None):
		"""Make system notification"""
		if icon is None:  # make sure we show notification with icon
			icon = self._default_icon

		# create notification object
		notification = pynotify.Notification(title, text, icon)

		# show notification
		notification.show()