import gtk

main_window = None
item_sessions = None
menu_sessions = None

def _show_sessions_manager(widget, data=None):
	"""Shows configuration"""
	main_window.preferences_window._show(None, 'sessions')
	
def _change_session(item, new_session):
	"""Changes session"""
	left_pages = main_window.left_notebook.get_n_pages()
	right_pages = main_window.right_notebook.get_n_pages()
	
	# save current session
	_save_current_session()
	
	# load new session
	main_window.load_tabs(main_window.left_notebook, 'left_{0}'.format(new_session))
	main_window.load_tabs(main_window.right_notebook, 'right_{0}'.format(new_session))
	main_window.tab_options.set('options', 'current', new_session)

	# close old tabs
	_close_tabs(main_window.left_notebook, left_pages)
	_close_tabs(main_window.right_notebook, right_pages)
	
def _close_tabs(notebook, num):
	"""Closes first 'num' pages in 'notebook'"""
	for i in range(num):
		main_window.close_tab(notebook, notebook.get_nth_page(0))

def _first_start_specific_actions():
	"""Adds required options to configuration"""
	if not main_window.tab_options.has_option('options', 'sessions'):
		main_window.tab_options.set('options', 'sessions', 'Default')
	if not main_window.tab_options.has_option('options', 'current'):
		main_window.tab_options.set('options', 'current', 'Default')

def _save_current_session():
	"""Just saves current session"""
	current_session = main_window.tab_options.get('options', 'current')
	main_window.save_tabs(main_window.left_notebook, 'left_{0}'.format(current_session))
	main_window.save_tabs(main_window.right_notebook, 'right_{0}'.format(current_session))

def register_plugin(application):
	"""Method that Sunflower calls once plugin is loaded"""
	global main_window
	main_window = application
	_first_start_specific_actions()
	_save_current_session()
	session_names = main_window.tab_options.get('options', 'sessions').split(':')
	
	# create menu
	menu_sessions = gtk.Menu()
	item_sessions = gtk.MenuItem('Sessions')
	item_manage = gtk.MenuItem('Manage sessions')
	item_separator = gtk.MenuItem()
		
	# pack menus and connect signals
	menu_sessions.append(item_manage)
	menu_sessions.append(item_separator)	
	for name in session_names:
		item = gtk.MenuItem(name)
		menu_sessions.append(item)
		item.connect('activate', _change_session, name)
	item_sessions.set_submenu(menu_sessions)
	item_manage.connect('activate', _show_sessions_manager)

	# add to file menu and show it
	main_window.menu_manager.get_item_by_name('file').get_submenu().insert(item_sessions, 1)
	item_sessions.show_all()
	
	# create configuration
	page = gtk.Label('No configuration avaible yet')
	main_window.preferences_window.add_tab('sessions', 'Sessions', page)

