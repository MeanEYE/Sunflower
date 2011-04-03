import os
import sys
import gtk
import pango
import webbrowser
import locale
import user
import fnmatch
import gettext

from menus import MenuManager
from mounts import MountsManager
from icons import IconManager
from associations import AssociationManager
from indicator import Indicator
from notifications import NotificationManager
from toolbar import ToolbarManager

from ConfigParser import RawConfigParser

# gui imports
from about_window import AboutWindow
from preferences_window import PreferencesWindow
from changelog_dialog import ChangeLogDialog
from input_dialog import InputDialog, AddBookmarkDialog

class MainWindow(gtk.Window):
	"""Main application class"""

	# in order to ease version comparing build number will
	# continue increasing and will never be reset.
	version = {
			'major': 0,
			'minor': 1,
			'build': 21,
			'stage': 'a'
		}

	def __init__(self):
		# create main window and other widgets
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.realize()

		# load translations
		self._load_translation()

		# containers
		self.plugin_classes = {}
		self.provider_classes = {}

		# list of protected plugins
		self.protected_plugins = ('file_list', 'system_terminal')

		# create managers early
		self.icon_manager = IconManager(self)
		self.menu_manager = MenuManager(self)
		self.mount_manager = None  # we'll create manager later
		self.associations_manager = AssociationManager()
		self.notification_manager = NotificationManager(self)
		self.toolbar_manager = ToolbarManager(self)

		# set window title
		self.set_title(_('Sunflower'))

		# set window icon
		self.icon_manager.set_application_icon(self)

		# set locale for international number formatting
		locale.setlocale(locale.LC_ALL)

		# config parsers
		self.options = None
		self.tab_options = None
		self.bookmark_options = None
		self.toolbar_options = None
		self.tool_options = None

		# location of all configuration files
		self.config_path = None

		# create a clipboard manager
		self.clipboard = gtk.Clipboard()

		# load config
		self.load_config()

		# call version specific actions
		self._version_specific_actions()

		# connect delete event to main window
		if self.options.getboolean('main', 'hide_on_close'):
			self.connect("delete-event", self._delete_event)
		else:
			self.connect("delete-event", self._destroy)

		# create other interfaces
		self.indicator = Indicator(self)
		self.about_window = AboutWindow(self)
		self.preferences_window = PreferencesWindow(self)

		# define local variables
		self._in_fullscreen = False

		# create menu items
		menu_bar = gtk.MenuBar()

		menu_items = (
			{
				'label': _('File'),
				'submenu': (
					{
						'label': _('New tab'),
						'name': 'new_tab',
						'type': 'image',
						'image': 'tab-new',
						'data': 'file',
						'path': '<Sunflower>/File/NewTab',
						'submenu': ()
					},
					{
						'type': 'separator',
					},
					{
						'label': _('Create file'),
						'type': 'image',
						'stock': gtk.STOCK_NEW,
						'callback': self._command_create,
						'data': 'file',
						'path': '<Sunflower>/File/CreateFile',
					},
					{
						'label': _('Create directory'),
						'type': 'image',
						'image': 'folder-new',
						'callback': self._command_create,
						'data': 'directory',
						'path': '<Sunflower>/File/CreateDirectory',
					},
					{
						'type': 'separator',
					},
					{
						'label': _('_Quit'),
						'type': 'image',
						'stock': gtk.STOCK_QUIT,
						'callback' : self._destroy,
						'path': '<Sunflower>/File/Quit',
					},
				)
			},
			{
				'label': _('Mark'),
				'submenu': (
					{
						'label': _('_Select all'),
						'type': 'image',
						'stock': gtk.STOCK_SELECT_ALL,
						'callback': self.select_all,
						'path': '<Sunflower>/Mark/SelectAll',
					},
					{
						'label': _('_Unselect all'),
						'callback': self.unselect_all,
						'path': '<Sunflower>/Mark/UnselectAll',
					},
					{
						'label': _('Invert select_ion'),
						'callback': self.invert_selection,
						'path': '<Sunflower>/Mark/InvertSelection',
					},
					{'type': 'separator'},
					{
						'label': _('S_elect with pattern'),
						'callback': self.select_with_pattern,
						'path': '<Sunflower>/Mark/SelectPattern',
					},
					{
						'label': _('Unselect with pa_ttern'),
						'callback': self.unselect_with_pattern,
						'path': '<Sunflower>/Mark/UnselectPattern',
					},
					{'type': 'separator'},
					{
						'label': _('Select with same e_xtension'),
						'callback': self.select_with_same_extension,
						'path': '<Sunflower>/Mark/SelectWithSameExtension',
					},
					{'type': 'separator'},
					{
						'label': _('Compare _directories'),
						'callback': self.compare_directories,
						'path': '<Sunflower>/Mark/Compare',
					}
				)
			},
		    {
		        'label': _('Commands'),
		        'name': 'commands_menu',
		        'submenu': (
		            {
		                'label': _('Find files'),
		                'type': 'image',
		                'image': 'system-search',
		                'path': '<Sunflower>/Commands/FindFiles'
		            },
		            {
		                'label': _('Synchronize directories'),
		                'path': '<Sunflower>/Commands/SynchronizeDirectories'
		            },
		            {'type': 'separator'},
		            {
		                'label': _('Advanced rename'),
		                'path': '<Sunflower>/Commands/AdvancedRename'
		            },
		        )
		    },
			{
				'label': _('View'),
				'submenu': (
					{
						'label': _('Ful_lscreen'),
						'type': 'image',
						'stock': gtk.STOCK_FULLSCREEN,
						'callback': self.toggle_fullscreen,
						'path': '<Sunflower>/View/Fullscreen',
						'name': 'fullscreen_toggle',
					},
					{
						'label': _('Rel_oad item list'),
						'type': 'image',
						'image': 'reload',
						'callback': self._command_reload,
						'path': '<Sunflower>/View/Reload'
					},
					{
						'type': 'separator',
					},
					{
						'label': _('Show _hidden files'),
						'type': 'checkbox',
						'active': self.options.getboolean('main', 'show_hidden'),
						'callback': self._toggle_show_hidden_files,
						'name': 'show_hidden_files',
						'path': '<Sunflower>/View/ShowHidden',
					},
					{
						'label': _('Show _toolbar'),
						'type': 'checkbox',
						'active': self.options.getboolean('main', 'show_toolbar'),
						'callback': self._toggle_show_toolbar,
						'name': 'show_toolbar',
						'path': '<Sunflower>/View/ShowToolbar',
					},
					{
						'label': _('Show _command bar'),
						'type': 'checkbox',
						'active': self.options.getboolean('main', 'show_command_bar'),
						'callback': self._toggle_show_command_bar,
						'name': 'show_command_bar',
						'path': '<Sunflower>/View/ShowCommandBar',
					},
					{
						'label': _('Show co_mmand entry'),
						'type': 'checkbox',
						'active': self.options.getboolean('main', 'show_command_entry'),
						'callback': self._toggle_show_command_entry,
						'name': 'show_command_entry',
						'path': '<Sunflower>/View/ShowCommandEntry',
					},
					{'type': 'separator'},
					{
						'label': _('_Preferences'),
						'type': 'image',
						'stock': gtk.STOCK_PREFERENCES,
						'callback': self.preferences_window._show,
						'path': '<Sunflower>/View/Preferences',
					},
				)
			},
			{
				'label': _('Tools'),
				'name': 'tools',
			},
			{
				'label': _('Operations'),
				'name': 'operations',
		        'submenu': (
		            {
		                'label': _('There are no minimized operations'),
		                'name': 'no_operations',
		            },
		        )
			},
			{
				'label': _('Help'),
				'submenu': (
					{
						'label': _('_Home page'),
						'type': 'image',
						'stock': gtk.STOCK_HOME,
						'callback': self.goto_web,
						'data': 'rcf-group.com',
						'path': '<Sunflower>/Help/HomePage',
					},
					{'type': 'separator'},
					{
						'label': _('File a _bug report'),
						'type': 'image',
						'image': 'lpi-bug',
						'callback': self.goto_web,
						'data': 'code.google.com/p/sunflower-fm/issues/entry',
						'path': '<Sunflower>/Help/BugReport',
					},
					{
						'label': _('Check for _updates'),
						'path': '<Sunflower>/Help/CheckForUpdates',
					},
					{'type': 'separator'},
					{
						'label': _('_About'),
						'type': 'image',
						'stock': gtk.STOCK_ABOUT,
						'callback': self.about_window._show,
						'path': '<Sunflower>/Help/About',
					}
				)
			},
		)

		# add items to main menu
		for item in menu_items:
			menu_bar.append(self.menu_manager.create_menu_item(item))

		# tools menu
		self.menu_tools = gtk.Menu()

		self._menu_item_tools = self.menu_manager.get_item_by_name('tools')
		self._menu_item_tools.set_sensitive(False)
		self._menu_item_tools.set_submenu(self.menu_tools)

		# operations menu
		self._menu_item_operations = self.menu_manager.get_item_by_name('operations')
		self._menu_item_no_operations = self.menu_manager.get_item_by_name('no_operations')

		self.menu_operations = self._menu_item_operations.get_submenu()

		# load accelerator map
		self.load_accel_map(os.path.join(self.config_path, 'accel_map'))

		# create toolbar
		self.toolbar_manager.load_config(self.toolbar_options)

		toolbar = self.toolbar_manager.get_toolbar()
		toolbar.set_property(
						'no-show-all',
						not self.options.getboolean('main', 'show_toolbar')
					)

		# bookmarks menu
		self.menu_bookmarks = gtk.Menu()
		self.menu_bookmarks.connect('hide', self._handle_bookmarks_hide)

		# mounts menu
		mounts_image = gtk.Image()
		mounts_image.set_from_icon_name('computer', gtk.ICON_SIZE_MENU)

		self._menu_item_mounts = gtk.ImageMenuItem()
		self._menu_item_mounts.set_label(_('Mounts'))
		self._menu_item_mounts.set_image(mounts_image)
		self._menu_item_mounts.show()
		self.mount_manager = MountsManager(self, self._menu_item_mounts)

		# commands menu
		menu_item_commands = self.menu_manager.get_item_by_name('commands_menu')
		self.menu_commands = menu_item_commands.get_submenu()

		# create notebooks
		hbox = gtk.HBox(True, 3)

		self.left_notebook = gtk.Notebook()
		self.left_notebook.set_scrollable(True)
		self.left_notebook.connect('focus-in-event', self._transfer_focus)
		self.left_notebook.connect('page-added', self._tab_moved)
		self.left_notebook.set_group_id(0)

		self.right_notebook = gtk.Notebook()
		self.right_notebook.set_scrollable(True)
		self.right_notebook.connect('focus-in-event', self._transfer_focus)
		self.right_notebook.connect('page-added', self._tab_moved)
		self.right_notebook.set_group_id(0)

		hbox.pack_start(self.left_notebook, True, True, 0)
		hbox.pack_start(self.right_notebook, True, True, 0)

		# command line prompt
		self.command_entry_bar = gtk.HBox(False, 0)

		self.path_label = gtk.Label()
		self.path_label.set_alignment(1, 0.5)
		self.path_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
		self.path_label.show()

		# create history list
		self.command_list = gtk.ListStore(str)

		# create auto-complete entry
		self.command_completion = gtk.EntryCompletion()
		self.command_completion.set_model(self.command_list)
		self.command_completion.set_minimum_key_length(2)
		self.command_completion.set_text_column(0)

		# create editor
		self.command_edit = gtk.Entry()
		self.command_edit.set_completion(self.command_completion)
		self.command_edit.connect('activate', self.execute_command)
		self.command_edit.connect('key-press-event', self._command_edit_key_press)
		self.command_edit.show()

		# load history file
		self._load_history()

		self.command_entry_bar.pack_start(self.path_label, True, True, 3)
		self.command_entry_bar.pack_start(self.command_edit, True, True, 0)

		self.command_entry_bar.set_property(
						'no-show-all',
						not self.options.getboolean('main', 'show_command_entry')
					)
		# command buttons bar
		self.command_bar = gtk.HBox(True, 0)

		buttons = (
				(_('Refresh'), _('Reload active item list (CTRL+R)'), self._command_reload),
				(_('View'), _('View selected file (F3)'), None),
				(_('Edit'), _('Edit selected file (F4)'), self._command_edit),
				(_('Copy'), _('Copy selected items from active to opposite list (F5)'), self._command_copy),
				(_('Move'), _('Move selected items from active to opposite list (F6)'), self._command_move),
				(_('Create'), _('Create new directory (F7)\nCreate new file (CTRL+F7)'), self._command_create),
				(_('Delete'), _('Delete selected items (F8 or Delete)'), self._command_delete)
			)

		# create buttons and pack them
		for text, tooltip, callback in buttons:
			button = gtk.Button(label=text)

			if callback is not None:
				button.connect('clicked', callback)

			button.set_tooltip_text(tooltip)
			button.set_focus_on_click(False)

			button.show()  # we need to explicitly show in cases where toolbar is not visible

			self.command_bar.pack_start(button, True, True, 0)

		self.command_bar.set_property(
						'no-show-all',
						not self.options.getboolean('main', 'show_command_bar')
					)

		# pack gui
		vbox = gtk.VBox(False, 0)
		vbox.pack_start(menu_bar, expand=False, fill=False, padding=0)
		vbox.pack_start(self.toolbar_manager.get_toolbar(), expand=False, fill=False, padding=0)

		vbox2 = gtk.VBox(False, 3)
		vbox2.set_border_width(3)
		vbox2.pack_start(hbox, expand=True, fill=True, padding=0)
		vbox2.pack_start(self.command_entry_bar, expand=False, fill=False, padding=0)
		vbox2.pack_start(self.command_bar, expand=False, fill=False, padding=0)

		vbox.pack_start(vbox2, True, True, 0)
		self.add(vbox)

		# create bookmarks menu
		self._create_bookmarks_menu()

		# create tools menu
		self._create_tools_menu()

		# restore window size and position
		self._restore_window_position()

		# load plugins
		self._load_plugins()

		# create toolbar widgets
		self.toolbar_manager.create_widgets()

		# show widgets
		self.show_all()

	def _destroy(self, widget, data=None):
		"""Application desctructor"""
		self.save_tabs(self.left_notebook, 'left_notebook')
		self.save_tabs(self.right_notebook, 'right_notebook')

		self._save_window_position()

		self.save_config()

		gtk.main_quit()

	def _delete_event(self, widget, data=None):
		"""Handle delete event"""
		self.hide()
		self.indicator.adjust_visibility_items(False)

		return True  # prevent default handler

	def _create_bookmarks_menu(self):
		"""Create bookmarks menu as defined in options"""
		for item in self.menu_bookmarks.get_children():  # remove existing items
			self.menu_bookmarks.remove(item)

		# create mounts if specified
		if self.options.getboolean('main', 'show_mounts'):
			self.menu_bookmarks.append(self._menu_item_mounts)
			separator = self.menu_manager.create_menu_item({'type': 'separator'})
			self.menu_bookmarks.append(separator)

		# add home if specified
		if self.options.getboolean('main', 'add_home'):
			bookmark = gtk.ImageMenuItem()
			image = gtk.Image()
			image.set_from_icon_name('user-home', gtk.ICON_SIZE_MENU)

			bookmark.set_image(image)
			bookmark.set_label(label=_('Home directory'))
			bookmark.set_data('path', os.path.expanduser('~/'))
			bookmark.connect('activate', self._handle_bookmarks_click)

			self.menu_bookmarks.append(bookmark)

		# create bookmark menu items
		raw_bookmarks = self.bookmark_options.options('bookmarks')

		for index in range(1, len(raw_bookmarks) + 1):
			data = self.bookmark_options.get('bookmarks', 'b_{0}'.format(index)).split(';', 1)

			bookmark = gtk.ImageMenuItem()
			image = gtk.Image()
			image.set_from_icon_name('folder', gtk.ICON_SIZE_MENU)

			bookmark.set_image(image)
			bookmark.set_label(label=data[0])
			bookmark.set_data('path', os.path.expanduser(data[1]))
			bookmark.connect('activate', self._handle_bookmarks_click)

			self.menu_bookmarks.append(bookmark)

		# add separator
		separator = self.menu_manager.create_menu_item({'type': 'separator'})
		self.menu_bookmarks.append(separator)

		# create additional options
		menu_item = self.menu_manager.create_menu_item({
										'label': _('Options'),
										'submenu': (
												{
													'label': _('_Add bookmark'),
													'type': 'image',
													'image': 'bookmark-new',
													'callback': self._add_bookmark,
												},
												{
													'label': _('_Edit bookmarks'),
													'type': 'image',
													'stock': gtk.STOCK_PREFERENCES,
													'callback': self.preferences_window._show,
													'data': 5
												},
											)
									})

		self.menu_bookmarks.append(menu_item)
		self.menu_bookmarks.show_all()

	def _handle_bookmarks_hide(self, widget=None, data=None):
		"""Handle hiding of bookmarks menu

		This method will disable blocking of signals on specified list.

		"""
		list_ = self.menu_bookmarks.get_data('list')
		oposite_list = self.get_oposite_list(list_)

		list_._disable_object_block()
		oposite_list._disable_object_block()

	def _create_tools_menu(self):
		"""Create tools main menu"""
		for item in self.menu_tools.get_children():  # remove existing items
			self.menu_tools.remove(item)

		# get total tool items count
		tool_count = (len(self.tool_options.options('tools')) / 2) + 1

		# create each item from the list
		for index in range(1, tool_count):
			# get data from config
			tool_title = self.tool_options.get('tools', 'title_{0}'.format(index))
			tool_command = self.tool_options.get('tools', 'command_{0}'.format(index))

			# create menu item
			if tool_title != '-':
				# normal menu item
				tool = gtk.MenuItem(label=tool_title)
				tool.connect('activate', self._handle_tool_click)
				tool.set_data('command', tool_command)

			else:
				# separator
				tool = gtk.SeparatorMenuItem()

			# add item to the tools menu
			self.menu_tools.append(tool)

		# create separator
		if tool_count > 1:
			separator = gtk.SeparatorMenuItem()
			self.menu_tools.append(separator)

		# create option for editing tools
		edit_tools = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
		edit_tools.set_label(_('_Edit tools'))
		edit_tools.connect('activate', self.preferences_window._show, 6)
		self.menu_tools.append(edit_tools)

		self._menu_item_tools.set_sensitive(tool_count > 0)
		self.menu_tools.show_all()

	def _get_bookmarks_menu_position(self, menu, button):
		"""Get bookmarks position"""
		window_x, window_y = self.window.get_position()
		button_x, button_y = button.translate_coordinates(self, 0, 0)
		button_h = button.get_allocation().height

		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def _add_bookmark(self, widget, item_list=None):
		"""Show dialog for adding a new bookmark"""
		if item_list is None:
			# no list was specified
			item_list = self.menu_bookmarks.get_data('list')

		path = item_list.path
		dialog = AddBookmarkDialog(self, path)

		response = dialog.get_response()

		if response[0] == gtk.RESPONSE_OK:
			bookmarks = self.bookmark_options.options('bookmarks')

			name = 'b_{0}'.format(len(bookmarks) + 1)
			value = '{0};{1}'.format(response[1], response[2])

			self.bookmark_options.set('bookmarks', name, value)
			self._create_bookmarks_menu()

	def _handle_bookmarks_click(self, widget, data=None):
		"""Handle clicks on bookmark menu"""
		item_list = self.menu_bookmarks.get_data('list')

		if item_list is not None and hasattr(item_list, 'change_path'):
			path = widget.get_data('path')

			if os.path.isdir(path):
				# path is valid
				item_list.change_path(path)

			else:
				# invalid path, notify user
				dialog = gtk.MessageDialog(
										self,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										_(
				                            "Specified path does not exist or is not "
				                            "valid. If path is not local check if volume "
				                            "is mounted."
				                        ) + "\n\n{0}".format(path)
				                    )
				dialog.run()
				dialog.destroy()

	def _handle_tool_click(self, widget, data=None):
		"""Handle click on tool menu item"""
		command = widget.get_data('command')

		# grab active objects
		left_object = self.left_notebook.get_nth_page(self.left_notebook.get_current_page())
		right_object = self.right_notebook.get_nth_page(self.right_notebook.get_current_page())

		if hasattr(left_object, '_get_selection'):
			# get selected item from the left list
			left_selection_short = left_object._get_selection(True)
			left_selection_long = left_object._get_selection(False)

		if hasattr(right_object, '_get_selection'):
			# get selected item from the left list
			right_selection_short = right_object._get_selection(True)
			right_selection_long = right_object._get_selection(False)

		# get universal 'selected item' values
		if self._get_active_object() is left_object:
			selection_short = left_selection_short
			selection_long = left_selection_long
		else:
			selection_short = right_selection_short
			selection_long = right_selection_long

		# replace command
		command = command.replace('%l', str(left_selection_short))
		command = command.replace('%L', str(left_selection_long))
		command = command.replace('%r', str(right_selection_short))
		command = command.replace('%R', str(right_selection_long))
		command = command.replace('%s', str(selection_short))
		command = command.replace('%S', str(selection_long))

		os.system(command)

	def _handle_new_tab_click(self, widget, data=None):
		"""Handle clicking on item from 'New tab' menu"""
		notebook = self._get_active_object()._notebook
		plugin_class = widget.get_data('class')

		self.create_tab(notebook, plugin_class)

	def _tab_moved(self, notebook, child, page_num):
		"""Handle adding/moving tab accross notebooks"""
		if hasattr(child, 'update_notebook'):
			child.update_notebook(notebook)

	def _transfer_focus(self, notebook, data=None):
		"""Transfer focus from notebook to child widget in active tab"""
		selected_page = notebook.get_nth_page(notebook.get_current_page())
		selected_page._main_object.grab_focus()

	def _toggle_show_hidden_files(self, widget, data=None):
		"""Transfer option event to all the lists"""
		show_hidden = widget.get_active()
		self.options.set('main', 'show_hidden', ('False', 'True')[show_hidden])

		# update left notebook
		for index in range(0, self.left_notebook.get_n_pages()):
			page = self.left_notebook.get_nth_page(index)

			if hasattr(page, 'refresh_file_list'):
				page.refresh_file_list(widget, data)

		# update right notebook
		for index in range(0, self.right_notebook.get_n_pages()):
			page = self.right_notebook.get_nth_page(index)

			if hasattr(page, 'refresh_file_list'):
				page.refresh_file_list(widget, data)

	def _toggle_show_command_bar(self, widget, data=None):
		"""Show/hide command bar"""
		show_command_bar = widget.get_active()

		self.options.set('main', 'show_command_bar', ('False', 'True')[show_command_bar])
		self.command_bar.set_visible(show_command_bar)

	def _toggle_show_command_entry(self, widget, data=None):
		"""Show/hide command entry"""
		show_command_entry = widget.get_active()

		self.options.set('main', 'show_command_entry', ('False', 'True')[show_command_entry])
		self.command_entry_bar.set_visible(show_command_entry)

	def _toggle_show_toolbar(self, widget, data=None):
		"""Show/hide toolbar"""
		show_toolbar = widget.get_active()

		self.options.set('main', 'show_toolbar', ('False', 'True')[show_toolbar])
		self.toolbar_manager.get_toolbar().set_visible(show_toolbar)

	def _get_active_object(self):
		"""Return active notebook object"""
		return self._active_object

	def _set_active_object(self, object):
		"""Set active object"""
		if object is not None:
			self._active_object = object

	def _load_history(self):
		"""Load history file and populate the command list"""
		self.command_list.clear()

		try:
			# try to load our history file
			for line in file(os.path.join(user.home, self.options.get('main', 'history_file'))):
				self.command_list.append((line.strip(),))
		except:
			pass

	def _get_plugin_list(self):
		"""Get list of plugins"""
		# get plugin list
		path = os.path.join(
						os.path.dirname(sys.argv[0]),
						'application',
						'plugins'
					)

		# get matching files
		list_ = fnmatch.filter(os.listdir(path), '*.py')

		# remove extension
		list_ = [os.path.splitext(file_)[0] for file_ in list_]

		# remove package initialized
		list_.remove('__init__')

		return list_

	def _load_plugins(self):
		"""Dynamically load plugins"""
		# get plugin list
		list_ = self._get_plugin_list()

		# list of enabled plugins
		plugins_to_load = self.options.get('main', 'plugins').split(',')

		# filter list for loading
		list_ = filter(lambda file_: file_ in plugins_to_load, list_)

		for file_ in list_:
			# import module
			__import__('plugins.{0}'.format(file_))
			plugin = sys.modules['plugins.{0}'.format(file_)]

			# call module register_plugin method
			if hasattr(plugin, 'register_plugin'):
				plugin.register_plugin(self)

	def _load_translation(self):
		"""Load translation and install global functions"""
		# get directory for translations
		directory = os.path.join(
				os.path.dirname(sys.argv[0]),
				'translations'
			)

		# function params
		params = {
				'domain': 'sunflower',
				'fallback': True
			}

		# install translations from local directory if needed
		if os.path.isdir(directory):
			params.update({'localedir': directory})

		# get translation
		translation = gettext.translation(**params)

		# install global functions for translating
		__builtins__.update({
						'_': translation.gettext,
						'ngettext': translation.ngettext
					})

	def _command_reload(self, widget, data=None):
		"""Handle command button click"""
		active_object = self._get_active_object()

		if hasattr(active_object, 'refresh_file_list'):
			active_object.refresh_file_list()

	def _command_edit(self, widget, data=None):
		"""Handle command button click"""
		active_object = self._get_active_object()

		if hasattr(active_object, '_edit_selected'):
			active_object._edit_selected()

	def _command_copy(self, widget, data=None):
		"""Handle command button click"""
		active_object = self._get_active_object()

		if hasattr(active_object, '_copy_files'):
			active_object._copy_files()

	def _command_move(self, widget, data=None):
		"""Handle command button click"""
		active_object = self._get_active_object()

		if hasattr(active_object, '_move_files'):
			active_object._move_files()

	def _command_create(self, widget, data=None):
		"""Handle command button click"""
		active_object = self._get_active_object()

		if data is None or (data is not None and data == 'directory'):
			# create directory
			if hasattr(active_object, '_create_directory'):
				active_object._create_directory()

		else:
			# create file
			if hasattr(active_object, '_create_file'):
				active_object._create_file()

	def _command_delete(self, widget, data=None):
		"""Handle command button click"""
		active_object = self._get_active_object()

		if hasattr(active_object, '_delete_files'):
			active_object._delete_files()

	def _command_edit_key_press(self, widget, event):
		"""Handle key press in command edit"""

		result = False

		# generate state sting based on modifier state (control, alt, shift)
		state = "%d%d%d" % (
					bool(event.state & gtk.gdk.CONTROL_MASK),
					bool(event.state & gtk.gdk.MOD1_MASK),
					bool(event.state & gtk.gdk.SHIFT_MASK)
				)

		# retrieve human readable key representation
		key_name = gtk.gdk.keyval_name(event.keyval)

		if (key_name == 'Up' or key_name == 'Escape') and state == '000':
			self._get_active_object()._main_object.grab_focus()
			result = True

		return result

	def _save_window_position(self):
		"""Save window position to config"""
		self.unfullscreen()
		self.unmaximize()
		size = self.get_size()
		position = self.get_position()
		geometry = '{0}x{1}+{2}+{3}'.format(size[0], size[1], position[0], position[1])

		self.options.set('main', 'window', geometry)

	def _restore_window_position(self):
		"""Restore window position from config string"""
		self.parse_geometry(self.options.get('main', 'window'))

	def _version_specific_actions(self):
		"""This method will provide user with some feedback and
		backwards compatibility. Also it will show latest changelog"""
		config_version = self.options.getint('main', 'last_version')
		current_version = self.version['build']

		# check if we need to show change log and optionally modify system
		if config_version is None or current_version > config_version:
			mod_count = 0
			vbox = gtk.VBox(False, 10)
			vbox.set_border_width(5)

			# reset aceelerator map
			if config_version < 21:
				vbox_accel_map = gtk.VBox(False, 0)

				label_accel_map = gtk.Label('<b>Version 0.1a-21:</b>')
				label_accel_map.set_alignment(0, 0.5)
				label_accel_map.set_use_markup(True)

				checkbox_reset_accel_map = gtk.CheckButton('Reset accelerator map')
				checkbox_reset_accel_map.set_active(True)

				vbox_accel_map.pack_start(label_accel_map, False, False, 0)
				vbox_accel_map.pack_start(checkbox_reset_accel_map, False, False, 0)

				vbox.pack_start(vbox_accel_map, False, False, 0)
				mod_count += 1

			# clear tabs
			if config_version < 15:
				vbox_15 = gtk.VBox(False, 0)

				label_15 = gtk.Label('<b>Version 0.1a-15:</b>')
				label_15.set_alignment(0, 0.5)
				label_15.set_use_markup(True)

				checkbox_reset_tabs = gtk.CheckButton('Clear open tabs')
				checkbox_reset_tabs.set_active(True)

				vbox_15.pack_start(label_15, False, False, 0)
				vbox_15.pack_start(checkbox_reset_tabs, False, False, 0)

				vbox.pack_start(vbox_15, False, False, 0)
				mod_count += 1

			# show dialog
			change_log = ChangeLogDialog(self, vbox, not mod_count == 0)
			change_log.run()

			## apply selected changes in reverse order

			# clear saved tabs
			if config_version < 15:
				if checkbox_reset_tabs.get_active():
					self.tab_options = RawConfigParser()

			# reset accelerator map
			if config_version < 21:
				if checkbox_reset_accel_map.get_active()\
				and os.path.isfile(os.path.join(self.config_path, 'accel_map')):
					os.remove(os.path.join(self.config_path, 'accel_map'))

			# set config version to current
			self.options.set('main', 'last_version', current_version)

			# kill dialog
			change_log.destroy()

	def show_bookmarks_menu(self, widget=None, notebook=None):
		"""Position bookmarks menu properly and show it"""
		button = None

		if notebook is not None:
			# show request was triggered by global shortcut
			page = notebook.get_nth_page(notebook.get_current_page())
			if hasattr(page, '_bookmarks_button'):
				button = page._bookmarks_button

			self.menu_bookmarks.set_data('list', page)

		else:
			# button called for menu
			button = widget

		if button is not None:
			list_ = self.menu_bookmarks.get_data('list')
			oposite_list = self.get_oposite_list(list_)

			list_._enable_object_block()
			oposite_list._enable_object_block()

			self.menu_bookmarks.popup(
									None, None,
									self._get_bookmarks_menu_position,
									1, 0, button
								)

	def select_all(self, widget, data=None):
		"""Select all items in active list"""
		list_ = self._get_active_object()

		# ensure we don't make exception on terminal tabs
		if hasattr(list_, 'select_all'):
			list_.select_all()

	def unselect_all(self, widget, data=None):
		"""Unselect all items in active list"""
		list_ = self._get_active_object()

		# ensure we don't make exception on terminal tabs
		if hasattr(list_, 'unselect_all'):
			list_.unselect_all()

	def invert_selection(self, widget, data=None):
		"""Invert selection in active list"""
		list_ = self._get_active_object()

		if hasattr(list_, 'invert_selection'):
			list_.invert_selection()

	def select_with_pattern(self, widget, data=None):
		"""Ask user for selection pattern and
		select matching items"""
		list_ = self._get_active_object()

		if hasattr(list_, 'select_all'):
			# create dialog
			dialog = InputDialog(self)

			dialog.set_title(_('Select items'))
			dialog.set_label(_('Selection pattern (eg.: *.jpg):'))
			dialog.set_text('*')

			# get response
			response = dialog.get_response()

			# release dialog
			dialog.destroy()

			# commit selection
			if response[0] == gtk.RESPONSE_OK:
				list_.select_all(response[1])

	def select_with_same_extension(self, widget, data=None):
		"""Select all items with same extension in active list"""
		list_ = self._get_active_object()

		if hasattr(list_, '_get_selection') and hasattr(list_, 'select_all'):
			selection = list_._get_selection()

			if selection is not None:
				extension = os.path.splitext(selection)[1]
				list_.select_all('*{0}'.format(extension))

	def unselect_with_pattern(self, widget, data=None):
		"""Ask user for selection pattern and
		select matching items"""
		list_ = self._get_active_object()

		if hasattr(list_, 'unselect_all'):
			# create dialog
			dialog = InputDialog(self)

			dialog.set_title(_('Unselect items'))
			dialog.set_label(_('Selection pattern (eg.: *.jpg):'))
			dialog.set_text('*')

			# get response
			response = dialog.get_response()

			# release dialog
			dialog.destroy()

			# commit selection
			if response[0] == gtk.RESPONSE_OK:
				list_.unselect_all(response[1])

	def compare_directories(self, widget=None, data=None):
		"""Compare directories from left and right notebook"""
		left_object = None
		right_object = None

		# get left object
		if self.left_notebook.get_n_pages() > 0:
			left_object = self.left_notebook.get_nth_page(self.left_notebook.get_current_page())

		# get right object
		if self.right_notebook.get_n_pages() > 0:
			right_object = self.right_notebook.get_nth_page(self.right_notebook.get_current_page())

		# if both objects have selection methods and exist
		if None not in (left_object, right_object) \
		and hasattr(left_object, 'select_all') \
		and hasattr(right_object, 'select_all'):
			# get file lists
			left_list = left_object.get_provider().list_dir(left_object.path)
			right_list = right_object.get_provider().list_dir(right_object.path)

			# mark missing files
			left_object.select_all(exclude_list=right_list)
			right_object.select_all(exclude_list=left_list)

	def run(self):
		"""Main application loop"""
		# load tabs in the left notebook
		if not self.load_tabs(self.left_notebook, 'left_notebook'):
			self.create_tab(self.left_notebook, FileList)

		# load tabs in the right notebook
		if not self.load_tabs(self.right_notebook, 'right_notebook'):
			self.create_tab(self.right_notebook, FileList)

		gtk.main()

	def create_tab(self, notebook, plugin_class=None, path=None, sort_column=None, sort_ascending=None):
		"""Safe create tab"""
		if sort_column is not None and sort_column != '':
			# create plugin object with sort parameters
			new_tab = plugin_class(self, notebook, path, int(sort_column), bool(int(sort_ascending)))

		else:
			# create plugin object without sorting information
			new_tab = plugin_class(self, notebook, path)

		# add page to notebook
		index = notebook.append_page(new_tab, new_tab._tab_label)
		notebook.set_tab_reorderable(new_tab, True)
		notebook.set_tab_detachable(new_tab, True)

		# show tabs if needed
		if not self.options.getboolean('main', 'always_show_tabs'):
			notebook.set_show_tabs(notebook.get_n_pages() > 1)

		# focus tab if needed
		if self.options.getboolean('main', 'focus_new_tab'):
			notebook.set_current_page(index)
			new_tab._main_object.grab_focus()

	def create_terminal_tab(self, notebook, path=None):
		"""Create terminal tab on selected notebook"""
		self.create_tab(notebook, SystemTerminal, path)

	def close_tab(self, notebook, child):
		"""Safely remove tab and it's children"""
		if notebook.get_n_pages() > 1:
			# remove page from notebook
			notebook.remove_page(notebook.page_num(child))

			# hide tabs if needed
			if not self.options.getboolean('main', 'always_show_tabs'):
				notebook.set_show_tabs(notebook.get_n_pages() > 1)

			# kill the component
			del child

	def next_tab(self, notebook):
		"""Select next tab on given notebook"""
		first_page = 0
		last_page = notebook.get_n_pages() - 1

		if notebook.get_current_page() == last_page:
			self.set_active_tab(notebook, first_page)
		else:
			notebook.next_page()

		page = notebook.get_nth_page(notebook.get_current_page())
		page._main_object.grab_focus()

	def previous_tab(self, notebook):
		"""Select previous tab on given notebook"""
		first_page = 0
		last_page = notebook.get_n_pages() - 1

		if notebook.get_current_page() == first_page:
			self.set_active_tab(notebook, last_page)
		else:
			notebook.prev_page()

		page = notebook.get_nth_page(notebook.get_current_page())
		page._main_object.grab_focus()

	def set_active_tab(self, notebook, tab):
		"""Set active tab number"""
		notebook.set_current_page(tab)

	def goto_web(self, widget, data=None):
		"""Open URL stored in data"""
		if data is not None:
			webbrowser.open_new_tab("http://%s" % data)

	def execute_command(self, widget, data=None):
		"""Executes system command"""
		if data is not None:
			# process custom data
			raw_command = data

		else:
			# no data is specified so we try to process command entry
			raw_command = self.command_edit.get_text()
			self.command_edit.insert_text(raw_command)
			self.command_edit.set_text('')

		handled = False
		active_object = self._get_active_object()
		command = raw_command.split(' ', 1)

		# return if we don't have anything to parse
		if len(command) < 2: return

		if command[0] == 'cd' and hasattr(active_object, 'change_path'):
			# handle CD command
			if os.path.isdir(os.path.join(active_object.path, command[1])):
				active_object.change_path(os.path.join(active_object.path, command[1]))
				active_object._main_object.grab_focus()

			handled = True

		if not handled:
			print 'Unhandled command: {0}'.format(command[0])

	def save_tabs(self, notebook, section):
		"""Save opened tabs"""

		self.tab_options.remove_section(section)
		self.tab_options.add_section(section)

		for index in range(0, notebook.get_n_pages()):
			page = notebook.get_nth_page(index)

			tab_class = page.__class__.__name__
			tab_path = page.path

			if hasattr(page, '_sort_column'):
				# file lists have sort column
				tab_sort_column = page._sort_column
				tab_sort_ascending = (0, 1)[page._sort_ascending]

			else:
				# other plugins might not have sort column
				tab_sort_column = ''
				tab_sort_ascending = ''

			self.tab_options.set(
							section,
							'tab_{0}'.format(index),
							'{0}:{1}:{2}:{3}'.format(
												tab_class,
												tab_path,
												tab_sort_column,
												tab_sort_ascending
											)
						)

		if not self.tab_options.has_section('options'):
			self.tab_options.add_section('options')

		self.tab_options.set(
					'options',
					'{0}_selected'.format(section),
					notebook.get_current_page()
				)

	def load_tabs(self, notebook, section):
		"""Load saved tabs"""
		result = False

		if self.tab_options.has_section(section):
			# if section exists, load it
			tab_list = self.tab_options.options(section)
			tab_list.sort()

			for tab in tab_list:
				data = self.tab_options.get(section, tab).split(':', 3)

				tab_class = data[0]
				tab_path = data[1]
				tab_sort_column = data[2]
				tab_sort_ascending = data[3]

				self.create_tab(
							notebook,
							globals()[tab_class],
							tab_path,
							tab_sort_column,
							tab_sort_ascending
						)

			result = True

			# set active tab
			active_tab = self.tab_options.getint(
										'options',
										'{0}_selected'.format(section)
									)
			self.set_active_tab(notebook, active_tab)

		return result

	def save_accel_map(self, path):
		"""Save menu accelerator map"""
		gtk.accel_map_save(path)

	def load_accel_map(self, path):
		"""Load menu accelerator map"""
		if os.path.isfile(path):
			# load accelerator map
			gtk.accel_map_load(path)

		else:
			# no existing configuration, set default
			accel_map = (
						('<Sunflower>/File/CreateFile', 'F7', gtk.gdk.CONTROL_MASK),
						('<Sunflower>/File/CreateDirectory', 'F7', 0),
			            ('<Sunflower>/File/Quit', 'Q', gtk.gdk.CONTROL_MASK),
						('<Sunflower>/Mark/SelectAll', 'A', gtk.gdk.CONTROL_MASK),
						('<Sunflower>/Mark/SelectPattern', 'KP_Add', 0),
						('<Sunflower>/Mark/UnselectPattern', 'KP_Subtract', 0),
						('<Sunflower>/Mark/InvertSelection', 'KP_Multiply', 0),
						('<Sunflower>/Mark/SelectWithSameExtension', 'KP_Add', gtk.gdk.MOD1_MASK),
						('<Sunflower>/Mark/Compare', 'F12', 0),
			            ('<Sunflower>/Commands/FindFiles', 'F7', gtk.gdk.MOD1_MASK),
			            ('<Sunflower>/Commands/SynchronizeDirectories', 'F8', gtk.gdk.MOD1_MASK),
			            ('<Sunflower>/Commands/AdvancedRename', 'M', gtk.gdk.CONTROL_MASK),
						('<Sunflower>/View/Fullscreen', 'F11', 0),
						('<Sunflower>/View/Reload', 'R', gtk.gdk.CONTROL_MASK),
						('<Sunflower>/View/ShowHidden', 'H', gtk.gdk.CONTROL_MASK),
						('<Sunflower>/View/Preferences', 'P', gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK),
						)

			for path, key, mask in accel_map:
				gtk.accel_map_change_entry(path, gtk.gdk.keyval_from_name(key), mask, True)

	def save_config(self):
		"""Save configuration to file"""
		try:
			if not os.path.isdir(self.config_path):
				os.makedirs(self.config_path)

			self.options.write(open(os.path.join(self.config_path, 'config'), 'w'))
			self.tab_options.write(open(os.path.join(self.config_path, 'tabs'), 'w'))
			self.bookmark_options.write(open(os.path.join(self.config_path, 'bookmarks'), 'w'))
			self.toolbar_options.write(open(os.path.join(self.config_path, 'toolbar'), 'w'))
			self.tool_options.write(open(os.path.join(self.config_path, 'tools'), 'w'))
			self.save_accel_map(os.path.join(self.config_path, 'accel_map'))

		except IOError as error:
			# notify user about failure
			dialog = gtk.MessageDialog(
									self,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_OK,
									_(
										"Error saving configuration to files "
										"in your home directory. Make sure you have "
										"enough permissions."
									) +	"\n\n{0}".format(error)
								)
			dialog.run()
			dialog.destroy()

	def load_config(self):
		"""Load configuration from file located in users home directory"""
		self.options = RawConfigParser()
		self.tab_options = RawConfigParser()
		self.bookmark_options = RawConfigParser()
		self.toolbar_options = RawConfigParser()
		self.tool_options = RawConfigParser()

		# load configuration from right folder on systems that support it
		if os.path.isdir(os.path.join(user.home, '.config')):
			self.config_path = os.path.join(user.home, '.config', 'sunflower')
		else:
			self.config_path = os.path.join(user.home, '.sunflower')

		self.options.read(os.path.join(self.config_path, 'config'))
		self.tab_options.read(os.path.join(self.config_path, 'tabs'))
		self.bookmark_options.read(os.path.join(self.config_path, 'bookmarks'))
		self.toolbar_options.read(os.path.join(self.config_path, 'toolbar'))
		self.tool_options.read(os.path.join(self.config_path, 'tools'))

		# set default values
		if not self.options.has_section('main'):
			self.options.add_section('main')

		if not self.bookmark_options.has_section('bookmarks'):
			self.bookmark_options.add_section('bookmarks')

		if not self.tool_options.has_section('tools'):
			self.tool_options.add_section('tools')

		# define default options
		default_options = {
				'default_editor': 'gedit "{0}"',
				'wait_for_editor': 'False',
				'status_text': _('Directories:') + ' %dir_sel/%dir_count   ' +
							_('Files:') + ' %file_sel/%file_count   ' +
							_('Size:') + ' %size_sel/%size_total',
				'show_hidden': 'False',
				'show_mounts': 'True',
				'show_toolbar': 'False',
				'show_command_bar': 'False',
				'show_command_entry': 'True',
				'add_home': 'True',
				'search_modifier': '010',
				'time_format': '%H:%M %d-%m-%y',
				'focus_new_tab': 'True',
				'row_hinting': 'False',
				'grid_lines': 0,
				'selection_color': 'red',
				'history_file': '.bash_history',
				'window': '950x450',
				'hide_on_close': 'False',
				'last_version': 0,
				'button_relief': 1,
				'terminal_scrollbars': 'True',
				'case_sensitive_sort': 'True',
				'plugins': 'file_list,system_terminal,default_toolbar',
				'reserve_size': 'False',
				'tab_button_icons': 'True',
				'always_show_tabs': 'True',
				'right_click_select': 'False',
				'vim_movement': 'False',
				'headers_visible': 'True',
				'hide_operation_on_minimize': 'False',
				'ubuntu_coloring': 'False',
			}

		# set default options
		for option, value in default_options.items():
			if not self.options.has_option('main', option):
				self.options.set('main', option, value)

	def focus_oposite_list(self, widget, data=None):
		"""Sets focus on oposite item list"""
		oposite_object = self.get_oposite_list(self._get_active_object())
		oposite_object._main_object.grab_focus()

		return True

	def get_oposite_list(self, list_):
		"""Return oposite object"""
		left_object = self.left_notebook.get_nth_page(self.left_notebook.get_current_page())
		right_object = self.right_notebook.get_nth_page(self.right_notebook.get_current_page())

		if list_ is left_object:
			result = right_object

		else:
			result = left_object

		return result

	def update_column_sizes(self, column, sender=None):
		"""Update column size on all tabs of specified class"""
		# update left notebook
		for index in range(0, self.left_notebook.get_n_pages()):
			page = self.left_notebook.get_nth_page(index)

			if isinstance(page, sender.__class__) and page is not sender:
				page.update_column_size(column.size_id)

		# update right notebook
		for index in range(0, self.right_notebook.get_n_pages()):
			page = self.right_notebook.get_nth_page(index)

			if isinstance(page, sender.__class__) and page is not sender:
				page.update_column_size(column.size_id)

	def toggle_fullscreen(self, widget, data=None):
		"""Toggle application fullscreen"""
		if self._in_fullscreen:
			self.unfullscreen()
			self._in_fullscreen = False

		else:
			self.fullscreen()
			self._in_fullscreen = True

		# adjust menu item image
		stock = (gtk.STOCK_FULLSCREEN, gtk.STOCK_LEAVE_FULLSCREEN)[self._in_fullscreen]
		menu_item = self.menu_manager.get_item_by_name('fullscreen_toggle')

		image = menu_item.get_image()
		image.set_from_stock(stock, gtk.ICON_SIZE_MENU)

	def add_operation(self, widget, callback, data=None):
		"""Add operation to menu"""
		item = gtk.ImageMenuItem()
		item.add(widget)
		item.connect('activate', callback, data)

		item.show_all()
		item.hide()

		self.menu_operations.append(item)

		return item

	def remove_operation(self, widget):
		"""Remove operation item from menu"""
		self.menu_operations.remove(widget)
		self.operation_menu_changed()

	def operation_menu_changed(self):
		"""Increase count of visible operation menu items"""
		has_operations = False

		# check if there are minimized operations
		for operation_item in self.menu_operations.get_children():
			if operation_item is not self._menu_item_no_operations \
			and operation_item.get_visible():
				has_operations = True
				break;

		# set "no operations" menu item visibility
		self._menu_item_no_operations.set_visible(not has_operations)

	def apply_settings(self):
		"""Apply settings to all the pluggins and main window"""
		# show or hide command bar depending on settings
		show_command_bar = self.menu_manager.get_item_by_name('show_command_bar')
		show_command_bar.set_active(self.options.getboolean('main', 'show_command_bar'))

		# show or hide command bar depending on settings
		show_command_entry = self.menu_manager.get_item_by_name('show_command_entry')
		show_command_entry.set_active(self.options.getboolean('main', 'show_command_entry'))

		# show or hide toolbar depending on settings
		show_toolbar = self.menu_manager.get_item_by_name('show_toolbar')
		show_toolbar.set_active(self.options.getboolean('main', 'show_toolbar'))

		# show or hide hidden files
		show_hidden = self.menu_manager.get_item_by_name('show_hidden_files')
		show_hidden.set_active(self.options.getboolean('main', 'show_hidden'))

		# recreate bookmarks menu
		self._create_bookmarks_menu()

		# recreate tools menu
		self._create_tools_menu()

		# recreate toolbar widgets
		self.toolbar_manager.create_widgets()

		# show tabs if needed
		self.left_notebook.set_show_tabs(
								self.options.getboolean('main', 'always_show_tabs') or
								self.left_notebook.get_n_pages() > 1
							)
		self.right_notebook.set_show_tabs(
								self.options.getboolean('main', 'always_show_tabs') or
								self.right_notebook.get_n_pages() > 1
							)

		# apply settings for each tab in left notebook
		for index in range(0, self.left_notebook.get_n_pages()):
			page = self.left_notebook.get_nth_page(index)

			if hasattr(page, 'apply_settings'):
				page.apply_settings()

		# apply settings for each tab in right notebook
		for index in range(0, self.right_notebook.get_n_pages()):
			page = self.right_notebook.get_nth_page(index)

			if hasattr(page, 'apply_settings'):
				page.apply_settings()

	def register_class(self, name, plugin_class):
		"""Register plugin class

		Classes registered using this method will be displayed in 'New tab' menu.
		Only plugins that provide tab components should be registered using this method!

		"""
		# add to plugin list
		self.plugin_classes[name] = plugin_class

		# create menu item and add it
		menu_item = gtk.MenuItem(name)
		menu_item.set_data('class', plugin_class)
		menu_item.connect('activate', self._handle_new_tab_click)

		menu_item.show()

		# add menu item
		menu = self.menu_manager.get_item_by_name('new_tab').get_submenu()
		menu.append(menu_item)

		# import class to globals
		globals()[plugin_class.__name__] = plugin_class

	def register_provider(self, protocol, ProviderClass):
		"""Register file provider class for specified protocol

		These classes will be used when handling all sorts of URI based operations
		like drag and drop and system bookmark handling.

		"""
		self.provider_classes[protocol] = ProviderClass

	def register_toolbar_factory(self, FactoryClass):
		"""Register and create toolbar widget factory"""
		self.toolbar_manager.register_factory(FactoryClass)

	def get_provider_by_protocol(self, protocol):
		"""Return provider class specified by protocol"""
		result = None

		if protocol in self.provider_classes.keys():
			result = self.provider_classes[protocol]

		return result
