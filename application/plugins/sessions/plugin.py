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
	main_window.tab_options.set('sessions', 'current', new_session)

	# close old tabs
	_close_tabs(main_window.left_notebook, left_pages)
	_close_tabs(main_window.right_notebook, right_pages)
	
def _close_tabs(notebook, num):
	"""Closes first 'num' pages in 'notebook'"""
	for i in range(num):
		main_window.close_tab(notebook, notebook.get_nth_page(0))

def _first_start_specific_actions():
	"""Adds required options to configuration"""
	if not main_window.tab_options.has_section('names'):
		main_window.tab_options.add_section('names')
		main_window.tab_options.set('names', 'session_0', 'Default')
	if not main_window.tab_options.has_section('sessions'):
		main_window.tab_options.add_section('sessions')
		main_window.tab_options.set('sessions', 'session_order', '0')
		main_window.tab_options.set('sessions', 'current', '0')

def _save_current_session():
	"""Just saves current session"""
	current_session = main_window.tab_options.get('sessions', 'current')
	main_window.save_tabs(main_window.left_notebook, 'left_{0}'.format(current_session))
	main_window.save_tabs(main_window.right_notebook, 'right_{0}'.format(current_session))
	
def _edited_name():
	pass
	
def _add_session():
	pass
	
def _delete_session():
	pass
	
def _move_session():
	pass

def register_plugin(application):
	"""Method that Sunflower calls once plugin is loaded"""
	global main_window
	main_window = application
	_first_start_specific_actions()
	_save_current_session()
	sessions = main_window.tab_options.get('sessions', 'session_order').split(':')
	
	# create menu
	menu_sessions = gtk.Menu()
	item_sessions = gtk.MenuItem('Sessions')
	item_manage = gtk.MenuItem('Manage sessions')
	item_separator = gtk.MenuItem()
		
	# pack menus and connect signals
	menu_sessions.append(item_manage)
	menu_sessions.append(item_separator)	
	for session in sessions:
		item = gtk.MenuItem(main_window.tab_options.get('names', 'session_{0}'.format(session)))
		menu_sessions.append(item)
		item.connect('activate', _change_session, session)
	item_sessions.set_submenu(menu_sessions)
	item_manage.connect('activate', _show_sessions_manager)

	# add to file menu and show it
	main_window.menu_manager.get_item_by_name('file').get_submenu().insert(item_sessions, 1)
	item_sessions.show_all()
	
	# create configuration
	page = gtk.VBox(False, 0)
	
	# create list box
	container = gtk.ScrolledWindow()
	container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
	container.set_shadow_type(gtk.SHADOW_IN)

	session_store = gtk.ListStore(str, str)

	treeview = gtk.TreeView()
	treeview.set_model(session_store)
	treeview.set_rules_hint(True)

	cell_name = gtk.CellRendererText()
	cell_name.set_property('editable', True)
	cell_name.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
	cell_name.connect('edited', _edited_name, 0)

	col_name = gtk.TreeViewColumn(_('Name'), cell_name, text=0)
	col_name.set_min_width(200)
	col_name.set_resizable(True)

	treeview.append_column(col_name)
	container.add(treeview)

	# create controls
	button_box = gtk.HBox(False, 5)

	button_add = gtk.Button(stock=gtk.STOCK_ADD)
	button_add.connect('clicked', _add_session)

	button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
	button_delete.connect('clicked', _delete_session)

	image_up = gtk.Image()
	image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

	button_move_up = gtk.Button(label=None)
	button_move_up.add(image_up)
	button_move_up.set_tooltip_text(_('Move Up'))
	button_move_up.connect('clicked', _move_session, -1)

	image_down = gtk.Image()
	image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

	button_move_down = gtk.Button(label=None)
	button_move_down.add(image_down)
	button_move_down.set_tooltip_text(_('Move Down'))
	button_move_down.connect('clicked', _move_session, 1)

	# pack ui
	button_box.pack_start(button_add, False, False, 0)
	button_box.pack_start(button_delete, False, False, 0)
	button_box.pack_end(button_move_down, False, False, 0)
	button_box.pack_end(button_move_up, False, False, 0)

	page.pack_start(container, True, True, 0)
	page.pack_start(button_box, False, False, 0)
	
	main_window.preferences_window.add_tab('sessions', 'Sessions', page)

