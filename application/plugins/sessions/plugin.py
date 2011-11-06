import gtk
import os

from widgets.settings_page import SettingsPage

main_window = None
item_sessions = None
config = None

class SessionsOptions(SettingsPage):
	"""Sessions options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'sessions', _('Sessions'))
		self._tab_options = application.tab_options

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
		sessions = _get_sessions_list(self._tab_options)
		for session in sessions:
			self._session_store.append((_get_session_name(self._tab_options, session), session))

	def _save_options(self):
		"""Method called when save button is clicked"""
		# prepere data in convince format
		identifiers = list()
		names = list()		
		for session in self._session_store:
			names.append(session[0])
			identifiers.append(session[1])
		actual_sessions = _get_sessions_list(self._tab_options)

		# save names
		for name, identifier in zip(names, identifiers):
			self._tab_options.set('names', 'session_{0}'.format(identifier), name)

		# delete old sesions
		for identifier in actual_sessions:
			if identifier not in identifiers:
				self._tab_options.remove_section('left_{0}'.format(identifier))
				self._tab_options.remove_section('right_{0}'.format(identifier))
				self._tab_options.remove_option('options', 'left_{0}_selected'.format(identifier))
				self._tab_options.remove_option('options', 'right_{0}_selected'.format(identifier))
				self._tab_options.remove_option('names', 'session_{0}'.format(identifier))
				
		# add new sessions
		for identifier in identifiers:
			if identifier not in actual_sessions:
				try:
					self._tab_options.add_section('left_{0}'.format(identifier))
					self._tab_options.add_section('right_{0}'.format(identifier))
				except:
					pass
				self._tab_options.set('options', 'left_{0}_selected'.format(identifier), '0')
				self._tab_options.set('options', 'right_{0}_selected'.format(identifier), '0')
				home_tab = 'FileList:{0}:0:1'.format(os.path.expanduser('~'))
				self._tab_options.set('left_{0}'.format(identifier), 'tab_0', home_tab)
				self._tab_options.set('right_{0}'.format(identifier), 'tab_0', home_tab)
				
		# save new order
		self._tab_options.set('sessions', 'session_order', ':'.join(identifiers))
		
		# recreate menu
		item_sessions.remove_submenu()
		_create_menu()

	def _handle_edited_name(self, cell, path, text, column):
		"""Filter new names"""
		# check if name already exists
		for session in self._session_store:
			if text == session[0]:
				return
		
		# change name
		iter_ = self._session_store.get_iter(path)
		self._session_store.set_value(iter_, column, text)

		# enable save button
		self._parent.enable_save()
	
	def _handle_add_session(self, widget, data=None):
		"""Add new session to the store"""
		# generate unique identifier
		identifier = 0
		for session in self._session_store:
			if int(session[1]) > identifier:
				identifier = int(session[1])
		identifier += 1
			
		# add session
		self._session_store.append((_('New session') + str(identifier), identifier))

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
	page = notebook.get_current_page()
	for i in range(num):
		main_window.close_tab(notebook, notebook.get_nth_page(0))
	main_window.set_active_tab(notebook, page)

def _first_start_specific_actions():
	"""Adds required options to configuration if they are not present"""
	if not main_window.tab_options.has_section('names'):
		main_window.tab_options.add_section('names')
		main_window.tab_options.set('names', 'session_0', 'Default')
	if not main_window.tab_options.has_section('sessions'):
		main_window.tab_options.add_section('sessions')
		main_window.tab_options.set('sessions', 'session_order', '0')
		main_window.tab_options.set('sessions', 'current', '0')

def _create_menu():
	"""Creates menu"""
	menu_sessions = gtk.Menu()
	item_manage = gtk.MenuItem(_('Manage sessions'))
	item_separator = gtk.MenuItem()
	current_session = main_window.tab_options.get('sessions', 'current')
		
	# pack menus and connect signals
	group = None
	menu_sessions.append(item_manage)
	menu_sessions.append(item_separator)	
	for session in _get_sessions_list(main_window.tab_options):
		item = gtk.RadioMenuItem(group, _get_session_name(main_window.tab_options, session))
		menu_sessions.append(item)
		item.connect('activate', change_session, session)
		if session == current_session:
			item.set_active(True)
		group = item
	item_sessions.set_submenu(menu_sessions)
	item_manage.connect('activate', show_sessions_manager)

	# add to file menu and show it
	item_sessions.show_all()

def _get_session_name(tab_options, identifier):
	"""Returns sesions name basing on its identifier"""
	return tab_options.get('names', 'session_{0}'.format(identifier))

def _get_sessions_list(tab_options):
	"""Returns ordered list of sessions"""
	return tab_options.get('sessions', 'session_order').split(':')

def register_plugin(application):
	"""Method that Sunflower calls once plugin is loaded"""
	global main_window
	main_window = application
	_first_start_specific_actions()
	save_current_session()
	
	# create menu
	global item_sessions
	item_sessions = gtk.MenuItem(_('Sessions'))
	_create_menu()
	main_window.menu_manager.get_item_by_name('file').get_submenu().insert(item_sessions, 1)
	
	# add configuration
	global config
	config = SessionsOptions(main_window.preferences_window, main_window)

