import os
import sys


try:
	# check if gtk is available
	import gi
	gi.require_version('Gtk', '3.0')
	gi.require_version('Notify', '0.7')

except:
	# print error and die
	print "Error starting Sunflower, missing GTK 3.0+"
	sys.exit(1)

else:
	# import required modules
	from gi.repository import Gtk, Gdk, GObject

try:
	# set process title
	from setproctitle import setproctitle
	setproctitle('sunflower')

except ImportError:
	pass

# Sunflower has to handle UTF-8 encoded strings while interacting with GTK
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class Sunflower(Gtk.Application):
	"""Main application instance."""

	def __init__(self):
		Gtk.Application.__init__(self)
		self.connect('startup', self.on_startup)
		self.connect('activate', self.on_activate)

	def on_activate(self, data=None):
		"""Handle application activation."""
		# import main window
		from gui.main_window import MainWindow

		# create main window and show it
		main_window = MainWindow(self)
		main_window.run()

	def on_startup(self, data=None):
		"""Handle application startup"""
		# add search path
		application_path = os.path.abspath(os.path.dirname(sys.argv[0]))
		if application_path not in sys.path:
			sys.path.insert(1, application_path)

# create application
application = Sunflower()
exit_status = application.run(sys.argv)
sys.exit(exit_status)
