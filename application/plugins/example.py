import gtk

main_window = None

def menu_item_click(widget, data=None):
	""" Shows message when user clicks on menu item """
	dialog = gtk.MessageDialog(
							main_window,
							gtk.DIALOG_DESTROY_WITH_PARENT,
							gtk.MESSAGE_INFO,
							gtk.BUTTONS_OK,
							'Hi there, this is an example message!'
						)
	dialog.run()
	dialog.destroy()

def register_plugin(application):
	"""Method that Sunflower calls once plugin is loaded"""
	global main_window

	# store application main window to a local variable
	main_window = application

	# create menu item and connect signals
	menu_item = gtk.MenuItem('Show example plugin message')
	menu_item.connect('activate', menu_item_click)

	# add to tools menu and show it
	main_window.menu_tools.append(menu_item)
	menu_item.show()
