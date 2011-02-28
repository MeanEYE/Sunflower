#!/usr/bin/env python
#
#		Sunflower.py
#
#		Copyright (c) 2010. by MeanEYE[rcf]
#		RCF Group, http://rcf-group.com
#
#		This program is free software; you can redistribute it and/or modify
#		it under the terms of the GNU General Public License as published by
#		the Free Software Foundation; either version 3 of the License, or
#		(at your option) any later version.
#
#		This program is distributed in the hope that it will be useful,
#		but WITHOUT ANY WARRANTY; without even the implied warranty of
#		MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#		GNU General Public License for more details.
#
#		You should have received a copy of the GNU General Public License
#		along with this program; if not, write to the Free Software
#		Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#		MA 02110-1301, USA.

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

if __name__ == '__main__':
	# add search path
	path_application = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "application"))
	sys.path.insert(1, path_application)

	gtk.gdk.threads_init()

	# construct main application object
	from gui.main_window import MainWindow

	app = MainWindow()
	app.run()
