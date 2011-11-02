import gtk

from widgets.settings_page import SettingsPage

main_window = None
item_sessions = None
menu_sessions = None
config = None

class SessionsOptions(SettingsPage):
	"""Sessions options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'sessions', _('Sessions'))

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._session_store = gtk.ListStore(str, str)

		self._treeview = gtk.TreeView()
		self._treeview.set_model(self._session_store)
		self._treeview.set_rules_hint(True)

		cell_name = gtk.CellRendererText()
		cell_name.set_property('editable', True)
		cell_name.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_name.connect('edited', self._handle_edited_name, 0)

		col_name = gtk.TreeViewColumn(_('Name'), cell_name, text=0)
		col_name.set_min_width(200)
		col_name.set_resizable(True)

		self._treeview.append_column(col_name)
		container.add(self._treeview)

		# create controls
		button_box = gtk.HBox(False, 5)

		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._handle_add_session)

		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		button_delete.connect('clicked', self._handle_delete_session)

		image_up = gtk.Image()
		image_up.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)

		button_move_up = gtk.Button(label=None)
		button_move_up.add(image_up)
		button_move_up.set_tooltip_text(_('Move Up'))
		button_move_up.connect('clicked', self._handle_move_session, -1)

		image_down = gtk.Image()
		image_down.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)

		button_move_down = gtk.Button(label=None)
		button_move_down.add(image_down)
		button_move_down.set_tooltip_text(_('Move Down'))
		button_move_down.connect('clicked', self._handle_move_session, 1)

		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_end(button_move_down, False, False, 0)
		button_box.pack_end(button_move_up, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _load_options(self):
		"""Load options and update interface"""
		self._session_store.clear()
		sessions = _get_sessions_list(self._application)
		for session in sessions:
			self.add_session(_get_session_name(self._application, session), session)

	def _save_options(self):
		"""Method called when save button is clicked"""
		pass

	def add_session(self, name, identifier):
		"""Adds session to the store"""
		self._session_store.append((name, identifier))

	def _handle_edited_name(self, cell, path, text, column):
		"""Filter new names"""
		if not text in _get_sessions_name_list(self._application):
			iter_ = self._session_store.get_iter(path)
			self._session_store.set_value(iter_, column, text)

			# enable save button
			self._parent.enable_save()
	
	def _handle_add_session(self, widget, data=None):
		"""Add new session to the store"""
		# generate new identifier
		identifier = 100
		self.add_session(_('New session'), identifier)

		# enable save button
		self._parent.enable_save()
	
	def _handle_delete_session(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._treeview.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# remove item from the store
			list_.remove(iter_)

			# enable save button if item was removed
			self._parent.enable_save()
	
	def _handle_move_session(self, widget, direction):
		"""Move selected bookmark up or down"""
		selection = self._treeview.get_selection()
		list_, iter_ = selection.get_selected()

		if iter_ is not None:
			# get iter index
			index = list_.get_path(iter_)[0]

			# depending on direction, swap iters
			if (direction == -1 and index > 0) \
			or (direction == 1 and index < len(list_) - 1):
				list_.swap(iter_, list_[index + direction].iter)

			# enable save button if iters were swapped
			self._parent.enable_save()


def show_sessions_manager(widget, data=None):
	"""Shows preferences window"""
	main_window.preferences_window._show(None, 'sessions')
	
def change_session(item, new_session):
	"""Changes session"""
	left_pages = main_window.left_notebook.get_n_pages()
	right_pages = main_window.right_notebook.get_n_pages()
	
	# save current session
	save_current_session()
	
	# load new session
	main_window.load_tabs(main_window.left_notebook, 'left_{0}'.format(new_session))
	main_window.load_tabs(main_window.right_notebook, 'right_{0}'.format(new_session))
	main_window.tab_options.set('sessions', 'current', new_session)

	# close old tabs
	_close_tabs(main_window.left_notebook, left_pages)
	_close_tabs(main_window.right_notebook, right_pages)
	
def save_current_session():
	"""Just saves current session"""
	current_session = main_window.tab_options.get('sessions', 'current')
	main_window.save_tabs(main_window.left_notebook, 'left_{0}'.format(current_session))
	main_window.save_tabs(main_window.right_notebook, 'right_{0}'.format(current_session))

def _close_tabs(notebook, num):
	"""Closes first 'num' pages in 'notebook'"""
	for i in range(num):
		main_window.close_tab(notebook, notebook.get_nth_page(0))

def _first_start_specific_actions():
	"""Adds required options to configuration if they are not present"""
	if not main_window.tab_options.has_section('names'):
		main_window.tab_options.add_section('names')
		main_window.tab_options.set('names', 'session_0', 'Default')
	if not main_window.tab_options.has_section('sessions'):
		main_window.tab_options.add_section('sessions')
		main_window.tab_options.set('sessions', 'session_order', '0')
		main_window.tab_options.set('sessions', 'current', '0')

def _get_session_name(application, identifier):
	"""Returns sesions name basing on its identifier"""
	return application.tab_options.get('names', 'session_{0}'.format(identifier))

def _get_sessions_list(application):
	"""Returns ordered list of sessions"""
	return application.tab_options.get('sessions', 'session_order').split(':')
	
def _get_sessions_name_list(application):
	"""Return ordered list of sessions names"""
	result = []
	ids = _get_sessions_list(application)
	for session in ids:
		result.append(_get_session_name(application, session))
	return result

def register_plugin(application):
	"""Method that Sunflower calls once plugin is loaded"""
	global main_window
	main_window = application
	_first_start_specific_actions()
	save_current_session()
	sessions = _get_sessions_list(main_window)
	
	# create menu
	menu_sessions = gtk.Menu()
	item_sessions = gtk.MenuItem(_('Sessions'))
	item_manage = gtk.MenuItem(_('Manage sessions'))
	item_separator = gtk.MenuItem()
		
	# pack menus and connect signals
	menu_sessions.append(item_manage)
	menu_sessions.append(item_separator)	
	for session in sessions:
		item = gtk.MenuItem(_get_session_name(main_window, session))
		menu_sessions.append(item)
		item.connect('activate', change_session, session)
	item_sessions.set_submenu(menu_sessions)
	item_manage.connect('activate', show_sessions_manager)

	# add to file menu and show it
	main_window.menu_manager.get_item_by_name('file').get_submenu().insert(item_sessions, 1)
	item_sessions.show_all()
	
	# add configuration
	global config
	config = SessionsOptions(main_window.preferences_window, main_window)

