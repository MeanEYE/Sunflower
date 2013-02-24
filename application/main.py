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
path_application = os.path.abspath(os.path.dirname(sys.argv[0]))
# sys.path.insert(1, path_application)

# initialize threads
gtk.gdk.threads_init()

# change working directory
os.chdir(os.path.dirname(path_application))

# construct main application object
from gui.main_window import MainWindow

app = MainWindow()
app.run()
