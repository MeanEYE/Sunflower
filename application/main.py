import os
import gi
import sys

try:
	# try to from import gtk
	gi.require_version('Gtk', '3.0')
	from gi.repository import Gdk

except:
	# print error and die
	print "Error starting Sunflower, missing GTK 3.0+"
	sys.exit(1)

# add search path
application_path = os.path.abspath(os.path.dirname(sys.argv[0]))
if application_path not in sys.path:
	sys.path.insert(1, application_path)

# initialize threads
Gdk.threads_init()

# construct main application object
from gui.main_window import MainWindow

application = MainWindow()
application.run()
