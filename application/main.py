import os
import sys

try:
	# try to import GTK
	import pygtk
	pygtk.require20()
	import gtk

except:
	# print error and die
	print "Error starting Sunflower, missing GTK 2.0+"
	sys.exit(1)

# add search path
application_path = os.path.abspath(os.path.dirname(sys.argv[0]))
if application_path not in sys.path:
	sys.path.insert(1, application_path)

# initialize threads
gtk.gdk.threads_init()

# construct main application object
from gui.main_window import MainWindow

app = MainWindow()
app.run()
