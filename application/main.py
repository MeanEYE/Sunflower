import os
import sys


try:
	# check if gtk is available
	import gi
	gi.require_version('Gtk', '3.0')

except:
	# print error and die
	print "Error starting Sunflower, missing GTK 3.0+"
	sys.exit(1)

else:
	# import required modules
	from gi.repository import Gtk, Gdk

try:
	# set process title
	from setproctitle import setproctitle
	setproctitle('sunflower')

except ImportError:
	pass

# add search path
application_path = os.path.abspath(os.path.dirname(sys.argv[0]))
if application_path not in sys.path:
	sys.path.insert(1, application_path)


class Sunflower(Gtk.Application):
	"""Main application instance."""

	def __init__(self):
		Gtk.Application.__init__(self, application_id='org.sunflower')

	def do_activate(self):
		"""Handle application activation."""
		# import main window
		from gui.main_window import MainWindow

		# create main window and show it
		main_window = MainWindow(self)
		main_window.run()

	def do_startup(self):
		"""Handle application startup"""
		# perform parent startup
		Gtk.Application.do_startup(self)

		# add search path
		application_path = os.path.abspath(os.path.dirname(sys.argv[0]))
		if application_path not in sys.path:
			sys.path.insert(1, application_path)

# create application
application = Sunflower()
exit_status = application.run(sys.argv)
sys.exit(exit_status)
