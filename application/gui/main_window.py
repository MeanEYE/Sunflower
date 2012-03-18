import os
import sys
import gtk
import pango
import webbrowser
import locale
import user
import gettext
import common
import shlex

from menus import MenuManager
from mounts import MountsManager
from icons import IconManager
from associations import AssociationManager
from indicator import Indicator
from notifications import NotificationManager
from toolbar import ToolbarManager
from accelerator_manager import AcceleratorManager

from plugin_base.item_list import ItemList
from plugin_base.rename_extension import RenameExtension
from plugin_base.find_extension import FindExtension
from tools.advanced_rename import AdvancedRename
from tools.find_files import FindFiles

from ConfigParser import RawConfigParser

try:
	# try to import argument parser
	from argparse import ArgumentParser
	USE_ARGPARSE = True

except:
	USE_ARGPARSE = False

# GUI imports
from gui.about_window import AboutWindow
from gui.preferences_window import PreferencesWindow
from gui.preferences.display import TabExpand
from gui.changelog_dialog import ChangeLogDialog
from gui.input_dialog import InputDialog, AddBookmarkDialog


class MainWindow(gtk.Window):
	"""Main application class"""

	# in order to ease version comparing build number will
	# continue increasing and will never be reset.
	version = {
			'major': 0,
			'minor': 1,
			'build': 41,
			'stage': 'a'
		}

	NAUTILUS_SEND_TO_INSTALLED = common.executable_exists('nautilus-sendto')
		
	def __init__(self):
		# create main window and other widgets
		gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)

		self._geometry = None

		# load translations
		self._load_translation()

		# parse arguments
		self.arguments = None
		self._parse_arguments()

		# containers
		self.plugin_classes = {}
		self.provider_classes = {}
		self.archive_provider_classes = {}
		self.rename_extension_classes = {}
		self.find_extension_classes = {}
		self.mount_manager_extensions = []

		# list of protected plugins
		self.protected_plugins = ('file_list', 'system_terminal')

		# create managers early
		self.icon_manager = IconManager(self)
		self.menu_manager = MenuManager(self)
		self.mount_manager = MountsManager(self)
		self.associations_manager = AssociationManager()
		self.notification_manager = NotificationManager(self)
		self.toolbar_manager = ToolbarManager(self)
		self.accelerator_manager = AcceleratorManager(self)

		# set window title
		self.set_title(_('Sunflower'))
		self.set_wmclass('Sunflower', 'Sunflower')

		# set window icon
		self.icon_manager.set_window_icon(self)

		# config parsers
		self.options = None
		self.tab_options = None
		self.bookmark_options = None
		self.toolbar_options = None
		self.command_options = None
		self.accel_options = None
		self.association_options = None

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
			self.connect('delete-event', self._delete_event)
		else:
			self.connect('delete-event', self._destroy)

		self.connect('configure-event', self._handle_configure_event)
		self.connect('window-state-event', self._handle_window_state_event)

		# create other interfaces
		self.indicator = Indicator(self)
		self.preferences_window = PreferencesWindow(self)

		# define local variables
		self._in_fullscreen = False

		# create menu items
		self.menu_bar = gtk.MenuBar()

		menu_items = (
			{
				'label': _('File'),
				'name': 'file',
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
						'label': _('_Open'),
						'type': 'image',
						'stock': gtk.STOCK_OPEN,
						'callback': self._command_open,
						'path': '<Sunflower>/File/Open',
					},
					{
						'label': _('Open in new ta_b'),
						'type': 'image',
						'image': 'tab-new',
						'callback': self._command_open_in_new_tab,
						'path': '<Sunflower>/File/OpenInNewTab',
					},
					{
						'type': 'separator',
					},
					{
						'label': _('_Properties'),
						'type': 'image',
						'stock': gtk.STOCK_PROPERTIES,
						'callback': self._command_properties,
						'path': '<Sunflower>/File/Properties',
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
				'label': _('Edit'),
				'submenu': (
					{
						'label': _('Cu_t'),
						'type': 'image',
						'stock': gtk.STOCK_CUT,
						'callback': self._command_cut_to_clipboard,
						'path': '<Sunflower>/Edit/Cut',
					},
					{
						'label': _('_Copy'),
						'type': 'image',
						'stock': gtk.STOCK_COPY,
						'callback': self._command_copy_to_clipboard,
						'path': '<Sunflower>/Edit/Copy',
					},
					{
						'label': _('_Paste'),
						'type': 'image',
						'stock': gtk.STOCK_PASTE,
						'callback': self._command_paste_from_clipboard,
						'path': '<Sunflower>/Edit/Paste',
					},
					{
						'type': 'separator',
					},
					{
						'label': _('_Delete'),
						'type': 'image',
						'stock': gtk.STOCK_DELETE,
						'callback': self._command_delete,
						'path': '<Sunflower>/Edit/Delete',
					},
					{
						'type': 'separator',
					},
					{
						'label': _('Send to...'),
						'type': 'image',
						'image': 'document-send',
						'callback': self._command_send_to,
						'path': '<Sunflower>/Edit/SendTo',
						'visible': self.NAUTILUS_SEND_TO_INSTALLED,
					},
					{
						'label': _('Ma_ke link'),
						'path': '<Sunflower>/Edit/MakeLink',
					},
					{
						'label': _('_Rename...'),
						'callback': self._command_rename,
						'path': '<Sunflower>/Edit/Rename',
					},
					{
						'type': 'separator',
					},
					{
						'label': _('_Unmount'),
						'name': 'unmount_menu',
						'submenu': (
							{
								'label': _('Mount list is empty'),
								'name': 'mount_list_empty',
							},
						),
					},
					{
						'type': 'separator',
					},
					{
						'label': _('_Preferences'),
						'type': 'image',
						'stock': gtk.STOCK_PREFERENCES,
						'callback': self.preferences_window._show,
						'path': '<Sunflower>/Edit/Preferences',
					},
				),
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
					{
						'label': _('Unselect with same exte_nsion'),
						'callback': self.unselect_with_same_extension,
						'path': '<Sunflower>/Mark/UnselectWithSameExtension',
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
				'label': _('Tools'),
				'name': 'tools',
				'submenu': (
					{
						'label': _('Find files'),
						'type': 'image',
						'image': 'system-search',
						'path': '<Sunflower>/Tools/FindFiles',
						'callback': self.show_find_files
					},
					{
						'label': _('Find duplicate files'),
						'path': '<Sunflower>/Tools/FindDuplicateFiles'
					},
					{
						'label': _('Synchronize directories'),
						'path': '<Sunflower>/Tools/SynchronizeDirectories'
					},
					{'type': 'separator'},
					{
						'label': _('Advanced rename'),
						'path': '<Sunflower>/Tools/AdvancedRename',
						'callback': self.show_advanced_rename,
					},
					{'type': 'separator'},
					{
						'label': _('Mount manager'),
						'path': '<Sunflower>/Tools/MountManager',
						'callback': self.mount_manager.show,
					}
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
						'label': _('Fast m_edia preview'),
						'type': 'checkbox',
						'active': self.options.getboolean('main', 'media_preview'),
						'callback': self._toggle_media_preview,
						'name': 'fast_media_preview',
						'path': '<Sunflower>/View/FastMediaPreview',
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
				)
			},
			{
				'label': _('Commands'),
				'name': 'commands',
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
					{'type': 'separator'},
					{
						'label': _('_About'),
						'type': 'image',
						'stock': gtk.STOCK_ABOUT,
						'callback': self.show_about_window,
						'path': '<Sunflower>/Help/About',
					}
				)
			},
		)

		# add items to main menu
		for item in menu_items:
			self.menu_bar.append(self.menu_manager.create_menu_item(item))

		# commands menu
		self.menu_commands = gtk.Menu()

		self._menu_item_commands = self.menu_manager.get_item_by_name('commands')
		self._menu_item_commands.set_submenu(self.menu_commands)

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
		self.menu_bookmarks.set_accel_group(self.menu_manager.get_accel_group())

		# mounts menu
		mounts_image = gtk.Image()
		mounts_image.set_from_icon_name('computer', gtk.ICON_SIZE_MENU)

		self._menu_item_mounts = gtk.ImageMenuItem()
		self._menu_item_mounts.set_label(_('Mounts'))
		self._menu_item_mounts.set_image(mounts_image)
		self._menu_item_mounts.show()

		# tell mounts manager to attache menu items
		self.mount_manager._attach_menus()

		# tools menu
		menu_item_tools = self.menu_manager.get_item_by_name('tools')
		self.menu_tools = menu_item_tools.get_submenu()

		# create notebooks
		hbox = gtk.HBox(True, 4)

		self.left_notebook = gtk.Notebook()
		self.left_notebook.set_scrollable(True)
		self.left_notebook.connect('focus-in-event', self._transfer_focus)
		self.left_notebook.connect('page-added', self._page_added)
		self.left_notebook.connect('switch-page', self._page_switched)
		self.left_notebook.set_group_id(0)

		self.right_notebook = gtk.Notebook()
		self.right_notebook.set_scrollable(True)
		self.right_notebook.connect('focus-in-event', self._transfer_focus)
		self.right_notebook.connect('page-added', self._page_added)
		self.right_notebook.connect('switch-page', self._page_switched)
		self.right_notebook.set_group_id(0)

		hbox.pack_start(self.left_notebook, True, True, 0)
		hbox.pack_start(self.right_notebook, True, True, 0)

		# command line prompt
		self.command_entry_bar = gtk.HBox(False, 0)

		self.path_label = gtk.Label()
		self.path_label.set_alignment(1, 0.5)
		self.path_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
		self.path_label.show()

		label_pound = gtk.Label('$');
		label_pound.set_alignment(0, 0.5)
		label_pound.show()

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
		self.command_edit.connect('focus-in-event', self._command_edit_focused)
		self.command_edit.show()

		# load history file
		self._load_history()

		self.command_entry_bar.pack_start(self.path_label, True, True, 5)
		self.command_entry_bar.pack_start(label_pound, False, False, 0)
		self.command_entry_bar.pack_start(self.command_edit, True, True, 0)

		self.command_entry_bar.set_property(
						'no-show-all',
						not self.options.getboolean('main', 'show_command_entry')
					)
		# command buttons bar
		self.command_bar = gtk.HBox(True, 0)

		buttons = (
				(_('Refresh'), _('Reload active item list'), self._command_reload),
				(_('Rename'), _('Rename selected file'), self._command_rename),
				(_('View'), _('View selected file'), self._command_view),
				(_('Edit'), _('Edit selected file'), self._command_edit),
				(_('Copy'), _('Copy selected items from active to opposite list'), self._command_copy),
				(_('Move'), _('Move selected items from active to opposite list'), self._command_move),
				(_('Create'), _('Create new directory'), self._command_create),
				(_('Delete'), _('Delete selected items'), self._command_delete)
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
		vbox.pack_start(self.menu_bar, expand=False, fill=False, padding=0)
		vbox.pack_start(self.toolbar_manager.get_toolbar(), expand=False, fill=False, padding=0)

		vbox2 = gtk.VBox(False, 4)
		vbox2.set_border_width(3)
		vbox2.pack_start(hbox, expand=True, fill=True, padding=0)
		vbox2.pack_start(self.command_entry_bar, expand=False, fill=False, padding=0)
		vbox2.pack_start(self.command_bar, expand=False, fill=False, padding=0)

		vbox.pack_start(vbox2, True, True, 0)
		self.add(vbox)

		# create bookmarks menu
		self._create_bookmarks_menu()

		# create commands menu
		self._create_commands_menu()

		# restore window size and position
		self._restore_window_position()

		# load plugins
		self._load_plugins()

		# create toolbar widgets
		self.toolbar_manager.create_widgets()

		# show widgets
		self.show_all()

	def _destroy(self, widget, data=None):
		"""Application destructor"""
		# save tabs
		self.save_tabs(self.left_notebook, 'left_notebook')
		self.save_tabs(self.right_notebook, 'right_notebook')

		# save window properties
		self._save_window_position()
		self._save_active_notebook()

		# save config changes
		self.save_config()

		# exit main loop
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
			separator = self.menu_manager.create_menu_item({'type': 'separator'})
			self.menu_bookmarks.append(self._menu_item_mounts)
			self.menu_bookmarks.append(separator)

		# add home if specified
		if self.options.getboolean('main', 'add_home'):
			bookmark = gtk.ImageMenuItem()
			image = gtk.Image()
			image.set_from_icon_name('user-home', gtk.ICON_SIZE_MENU)

			bookmark.set_image(image)
			bookmark.set_always_show_image(True)
			bookmark.set_label(_('Home directory'))
			bookmark.set_data('path', user.home)
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
			bookmark.set_always_show_image(True)
			bookmark.set_label(data[0])
			bookmark.set_data('path', os.path.expanduser(data[1]))
			bookmark.connect('activate', self._handle_bookmarks_click)

			self.menu_bookmarks.append(bookmark)

		# add system bookmarks if needed
		if self.options.getboolean('main', 'system_bookmarks')\
		and os.path.exists(os.path.join(user.home, '.gtk-bookmarks')):
			with open(os.path.join(user.home, '.gtk-bookmarks'), 'r') as raw_file:
				lines = raw_file.readlines(False)

			# add separator
			separator = self.menu_manager.create_menu_item({'type': 'separator'})
			self.menu_bookmarks.append(separator)

			# add bookmarks
			for line in lines:
				line = line.strip()
				label = os.path.basename(line)

				bookmark = gtk.ImageMenuItem()
				image = gtk.Image()
				image.set_from_icon_name('folder', gtk.ICON_SIZE_MENU)

				bookmark.set_image(image)
				bookmark.set_always_show_image(True)
				bookmark.set_label(label)
				bookmark.set_data('path', line)
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
													'data': 'bookmarks'
												},
											)
									})

		self.menu_bookmarks.append(menu_item)
		self.menu_bookmarks.show_all()

	def _handle_bookmarks_hide(self, widget=None, data=None):
		"""Handle hiding of bookmarks menu

		This method will disable blocking of signals on specified list.

		"""
		item_list = self.menu_bookmarks.get_data('list')
		oposite_object = self.get_oposite_object(item_list)

		item_list._disable_object_block()
		oposite_object._disable_object_block()

	def _create_commands_menu(self):
		"""Create commands main menu"""
		for item in self.menu_commands.get_children():  # remove existing items
			self.menu_commands.remove(item)

		# get total tool items count
		if self.command_options.has_section('commands'):
			tool_count = (len(self.command_options.options('commands')) / 2) + 1

		else:
			tool_count = 0

		# create each item from the list
		for index in range(1, tool_count):
			# get data from config
			tool_title = self.command_options.get('commands', 'title_{0}'.format(index))
			tool_command = self.command_options.get('commands', 'command_{0}'.format(index))

			# create menu item
			if tool_title != '-':
				# normal menu item
				tool = gtk.MenuItem(label=tool_title)
				tool.connect('activate', self._handle_command_click)
				tool.set_data('command', tool_command)

			else:
				# separator
				tool = gtk.SeparatorMenuItem()

			# add item to the tools menu
			self.menu_commands.append(tool)

		# create separator
		if tool_count > 1:
			separator = gtk.SeparatorMenuItem()
			self.menu_commands.append(separator)

		# create option for editing tools
		edit_commands = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
		edit_commands.set_label(_('_Edit commands'))
		edit_commands.connect('activate', self.preferences_window._show, 'commands')
		self.menu_commands.append(edit_commands)

		self._menu_item_commands.set_sensitive(True)
		self.menu_commands.show_all()

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

	def _handle_command_click(self, widget, data=None):
		"""Handle click on command menu item"""
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
		if self.get_active_object() is left_object:
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

		# execute command using programs default handler
		self.execute_command(widget, command)

	def _handle_new_tab_click(self, widget, data=None):
		"""Handle clicking on item from 'New tab' menu"""
		notebook = self.get_active_object()._notebook
		plugin_class = widget.get_data('class')

		self.create_tab(notebook, plugin_class)

	def _handle_configure_event(self, widget, event):
		"""Handle window resizing"""
		if self.window.get_state() == 0:
			self._geometry = self.get_size() + self.get_position()

	def _handle_window_state_event(self, widget, event):
		"""Handle window state change"""
		in_fullscreen = event.new_window_state is gtk.gdk.WINDOW_STATE_FULLSCREEN
		stock = (gtk.STOCK_FULLSCREEN, gtk.STOCK_LEAVE_FULLSCREEN)[in_fullscreen]

		# update main menu item
		menu_item = self.menu_manager.get_item_by_name('fullscreen_toggle')

		image = menu_item.get_image()
		image.set_from_stock(stock, gtk.ICON_SIZE_MENU)

	def _page_added(self, notebook, child, page_num):
		"""Handle adding/moving tab accross notebooks"""
		if hasattr(child, 'update_notebook'):
			child.update_notebook(notebook)

		if self.options.getint('main', 'expand_tabs') == TabExpand.ALL:
			notebook.child_set_property(child, 'tab-expand', True)

	def _page_switched(self, notebook, page, page_num, data=None):
		"""Handle switching pages"""
		current_page = notebook.get_nth_page(notebook.get_current_page())
		new_page = notebook.get_nth_page(page_num)

		if self.options.getint('main', 'expand_tabs') == TabExpand.ACTIVE:
			notebook.child_set_property(current_page, 'tab-expand', False)
			notebook.child_set_property(new_page, 'tab-expand', True)

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

	def _toggle_media_preview(self, widget, data=None):
		"""Enable/disable fast image preview"""
		self.options.set('main', 'media_preview', ('False', 'True')[widget.get_active()])

		# update left notebook
		for index in range(0, self.left_notebook.get_n_pages()):
			page = self.left_notebook.get_nth_page(index)

			if hasattr(page, 'apply_media_preview_settings'):
				page.apply_media_preview_settings()

		# update right notebook
		for index in range(0, self.right_notebook.get_n_pages()):
			page = self.right_notebook.get_nth_page(index)

			if hasattr(page, 'apply_media_preview_settings'):
				page.apply_media_preview_settings()

	def _set_active_object(self, new_object):
		"""Set active object"""
		if new_object is not None:
			self._active_object = new_object

			# set bookmarks target so accels could work
			self.menu_bookmarks.set_data('list', new_object)

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
		path = os.path.abspath(os.path.join('application', 'plugins'))

		# get matching directories
		plugin_list = filter(lambda item: os.path.isdir(os.path.join(path, item)), os.listdir(path))
		plugin_list = filter(lambda item: os.path.exists(os.path.join(path, item, 'plugin.py')), plugin_list)

		return plugin_list

	def _load_plugins(self):
		"""Dynamically load plugins"""
		# get plugin list
		plugin_files = self._get_plugin_list()

		# list of enabled plugins
		plugins_to_load = self.options.get('main', 'plugins').split(',')

		# filter list for loading
		plugin_files = filter(lambda file_name: file_name in plugins_to_load, plugin_files)

		for file_name in plugin_files:
			try:
				# import module
				__import__('plugins.{0}.plugin'.format(file_name))
				plugin = sys.modules['plugins.{0}.plugin'.format(file_name)]

				# call module register_plugin method
				if hasattr(plugin, 'register_plugin'):
					plugin.register_plugin(self)

			except Exception as error:
				print 'Error: Unable to load plugin "{0}": {1}'.format(file_name, error)

				# in case plugin is protected, complain and exit
				if file_name in self.protected_plugins:
					print '\nFatal error! Failed to load required plugin, exiting!'
					sys.exit(3)

	def _load_translation(self):
		"""Load translation and install global functions"""
		# get directory for translations
		directory = os.path.abspath('translations')

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

	def _command_reload(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, 'refresh_file_list'):
			active_object.refresh_file_list()

	def _command_rename(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_rename_file'):
			active_object._rename_file()

	def _command_view(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_view_selected'):
			active_object._view_selected()

	def _command_edit(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_edit_selected'):
			active_object._edit_selected()

	def _command_copy(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_copy_files'):
			active_object._copy_files()

	def _command_move(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_move_files'):
			active_object._move_files()

	def _command_create(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if data is None or (data is not None and data == 'directory'):
			# create directory
			if hasattr(active_object, '_create_directory'):
				active_object._create_directory()

		else:
			# create file
			if hasattr(active_object, '_create_file'):
				active_object._create_file()

	def _command_delete(self, widget=None, data=None):
		"""Handle command button click"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_delete_files'):
			active_object._delete_files()

	def _command_open(self, widget=None, data=None):
		"""Execute selected item in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_execute_selected_item'):
			active_object._execute_selected_item()

	def _command_open_in_new_tab(self, widget=None, data=None):
		"""Open selected directory from active list in new tab"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_open_in_new_tab'):
			active_object._open_in_new_tab()

	def _command_cut_to_clipboard(self, widget=None, data=None):
		"""Copy selected items from active list to clipboard"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_cut_files_to_clipboard'):
			active_object._cut_files_to_clipboard()

	def _command_copy_to_clipboard(self, widget=None, data=None):
		"""Copy selected items from active list to clipboard"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_copy_files_to_clipboard'):
			# ItemList object
			active_object._copy_files_to_clipboard()

		elif hasattr(active_object, '_copy_selection'):
			# Terminal object
			active_object._copy_selection()

	def _command_paste_from_clipboard(self, widget=None, data=None):
		"""Copy selected items from active list to clipboard"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_paste_files_from_clipboard'):
			# ItemList object
			active_object._paste_files_from_clipboard()

		elif hasattr(active_object, '_paste_selection'):
			# Terminal object
			active_object._paste_selection()

	def _command_properties(self, widget=None, data=None):
		"""Show properties for selected item in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_item_properties'):
			active_object._item_properties()

	def _command_send_to(self, widget=None, data=None):
		"""Show 'send to' dialog for selected items in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_send_to'):
			active_object._send_to()

	def _command_rename(self, widget=None, data=None):
		"""Rename selected item in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_rename_file'):
			active_object._rename_file()

	def _command_edit_key_press(self, widget, event):
		"""Handle key press in command edit"""
		result = False

		if event.keyval in (gtk.keysyms.Up, gtk.keysyms.Escape)\
		and event.state & gtk.accelerator_get_default_mod_mask() == 0:
			self.get_active_object()._main_object.grab_focus()
			result = True

		return result

	def _command_edit_focused(self, widget, event):
		"""Handle focusing command entry"""
		self.accelerator_manager.deactivate_scheduled_groups(widget)

	def _save_window_position(self):
		"""Save window position to config"""
		state = self.window.get_state()
		window_state = 0

		if state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			# window is in fullscreen
			window_state = 2

		elif state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
			# window is maximized
			window_state = 1

		self.options.set('main', 'window_state', window_state)

		# save window size and position
		geometry = '{0}x{1}+{2}+{3}'.format(*self._geometry)

		self.options.set('main', 'window', geometry)

	def _save_active_notebook(self):
		"""Save active notebook to config"""
		active_object = self.get_active_object()
		is_left = active_object._notebook is self.left_notebook

		self.options.set('main', 'active_notebook', (1, 0)[is_left])

	def _restore_window_position(self):
		"""Restore window position from config string"""
		self.parse_geometry(self.options.get('main', 'window'))
		self._geometry = self.get_size() + self.get_position()

		# restore window state
		window_state = self.options.getint('main', 'window_state')

		if window_state == 1:
			self.maximize()

		elif window_state == 2:
			self.fullscreen()

	def _version_specific_actions(self):
		"""This method will provide user with some feedback and
		backwards compatibility. Also it will show latest change log"""
		config_version = self.options.getint('main', 'last_version')
		current_version = self.version['build']

		# check if we need to show change log and optionally modify system
		if config_version is None or current_version > config_version and config_version > 0:
			mod_count = 0
			vbox = gtk.VBox(False, 10)
			vbox.set_border_width(5)

			# clear tabs
			if config_version < 40:
				vbox_version_40 = gtk.VBox(False, 0)

				label_version_40 = gtk.Label('<b>Version 0.1a-40:</b>')
				label_version_40.set_alignment(0, 0.5)
				label_version_40.set_use_markup(True)

				checkbox_reset_tabs = gtk.CheckButton('Clear open tabs')
				checkbox_reset_tabs.set_active(True)

				vbox_version_40.pack_start(label_version_40, False, False, 0)
				vbox_version_40.pack_start(checkbox_reset_tabs, False, False, 0)

				vbox.pack_start(vbox_version_40, False, False, 0)
				mod_count += 1

			if config_version < 37:
				vbox_version_37 = gtk.VBox(False, 0)

				label_version_37 = gtk.Label('<b>Version 0.1a-37:</b>')
				label_version_37.set_alignment(0, 0.5)
				label_version_37.set_use_markup(True)

				# reset accelerator map
				checkbox_reset_accel_map = gtk.CheckButton('Reset accelerator map')
				checkbox_reset_accel_map.set_active(True)

				# pack controls
				vbox_version_37.pack_start(label_version_37, False, False, 0)
				vbox_version_37.pack_start(checkbox_reset_accel_map, False, False, 0)

				vbox.pack_start(vbox_version_37, False, False, 0)
				mod_count += 1

			if config_version < 34:
				vbox_version_34 = gtk.VBox(False, 0)

				label_version_34 = gtk.Label('<b>Version 0.1a-34:</b>')
				label_version_34.set_alignment(0, 0.5)
				label_version_34.set_use_markup(True)

				# convert tools menu
				checkbox_convert_tools_menu = gtk.CheckButton('Convert saved tools menu')
				checkbox_convert_tools_menu.set_active(True)

				# convert saved column sizes
				checkbox_convert_column_sizes = gtk.CheckButton('Convert column sizes to new format')
				checkbox_convert_column_sizes.set_active(True)

				vbox_version_34.pack_start(label_version_34, False, False, 0)
				vbox_version_34.pack_start(checkbox_convert_tools_menu, False, False, 0)
				vbox_version_34.pack_start(checkbox_convert_column_sizes, False, False, 0)

				vbox.pack_start(vbox_version_34, False, False, 0)
				mod_count += 2

			# show dialog
			change_log = ChangeLogDialog(self, vbox, not mod_count == 0)
			change_log.run()

			## apply selected changes in reverse order

			if config_version < 34:
				# convert tools menu
				if checkbox_convert_tools_menu.get_active():
					# open old configuration file
					old_menu = RawConfigParser()
					old_menu.read(os.path.join(self.config_path, 'tools'))

					if not self.command_options.has_section('tools'):
						return

					# create section in new configuration file if it doesn't exist
					if not self.command_options.has_section('commands'):
						self.command_options.add_section('commands')

					# transfer items
					for key in old_menu.options('tools'):
						value = old_menu.get('tools', key)
						self.command_options.set('commands', key, value)

					# remove old configuration file
					os.unlink(os.path.join(self.config_path, 'tools'))

				# convert column sizes
				if checkbox_convert_column_sizes.get_active():
					columns = {
							0: 'name',
							1: 'extension',
							2: 'size',
							3: 'mode',
							4: 'date'
						}

					for index, name in columns.items():
						# save size to a new option
						size = self.options.getint('FileList', 'size_{0}'.format(index))
						self.options.set('FileList', 'size_{0}'.format(name), size)

						# remove old option
						self.options.remove_option('FileList', 'size_{0}'.format(index))

			if config_version < 37:
				# reset accelerator map
				if checkbox_reset_accel_map.get_active() \
				and os.path.isfile(os.path.join(self.config_path, 'accel_map')):
					os.remove(os.path.join(self.config_path, 'accel_map'))

			if config_version < 40:
				# clear saved tabs
				if checkbox_reset_tabs.get_active():
					self.tab_options = RawConfigParser()

			# kill dialog
			change_log.destroy()

		# set config version to current
		if config_version is None or current_version > config_version:
			self.options.set('main', 'last_version', current_version)

	def _parse_arguments(self):
		"""Parse command-line arguments passed to the application"""
		if not USE_ARGPARSE: return

		parser = ArgumentParser(
							description=_('Sunflower file manager'),
							prog='Sunflower.py'
						)

		# add parameters to parser
		parser.add_argument(
						'-v', '--version',
						action='version',
						version=(
								'{0} {1[major]}.{1[minor]}'
								'{1[stage]} ({1[build]})'
							).format(
								_('Sunflower'),
								self.version
							),
						help=_('print version and exit')
					)
		parser.add_argument(
						'-t', '--no-load-tabs',
						action='store_true',
						help=_('skip loading saved tabs'),
						dest='dont_load_tabs'
					)
		parser.add_argument(
						'-l', '--left-tab',
						action='append',
						help=_('open new tab on the left notebook'),
						metavar='PATH',
						dest='left_tabs'
					)
		parser.add_argument(
						'-r', '--right-tab',
						action='append',
						help=_('open new tab on the right notebook'),
						metavar='PATH',
						dest='right_tabs'
					)

		self.arguments = parser.parse_args()

	def activate_bookmark(self, widget=None, index=1):
		"""Activate bookmark by index"""
		result = False
		active_object = self.get_active_object()

		# get path list
		items = []

		# add home if needed
		if self.options.getboolean('main', 'add_home'):
			items.append(user.home)

		# read all bookmarks
		bookmark_count = len(self.bookmark_options.options('bookmarks'))
		for number in range(1, bookmark_count+1):
			path = self.bookmark_options.get('bookmarks', 'b_{0}'.format(number)).split(';', 1)[1]
			items.append(path)

		# check if bookmark index and active object are valid
		if index-1 < len(items) \
		and hasattr(active_object, 'change_path'):
			active_object.change_path(items[index-1])
			result = True

		return result

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
			# disable color changing on tab title bar
			item_list = self.menu_bookmarks.get_data('list')
			oposite_object = self.get_oposite_object(item_list)

			item_list._enable_object_block()
			oposite_object._enable_object_block()

			# show bookmarks menu
			self.menu_bookmarks.popup(
									None, None,
									self._get_bookmarks_menu_position,
									1, 0, button
								)

	def select_all(self, widget, data=None):
		"""Select all items in active list"""
		active_object = self.get_active_object()

		# ensure we don't make exception on terminal tabs
		if hasattr(active_object, 'select_all'):
			active_object.select_all()

	def unselect_all(self, widget, data=None):
		"""Unselect all items in active list"""
		active_object = self.get_active_object()

		# ensure we don't make exception on terminal tabs
		if hasattr(active_object, 'unselect_all'):
			active_object.unselect_all()

	def invert_selection(self, widget, data=None):
		"""Invert selection in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, 'invert_selection'):
			active_object.invert_selection()

	def select_with_pattern(self, widget, data=None):
		"""Ask user for selection pattern and select matching items"""
		active_object = self.get_active_object()

		if hasattr(active_object, 'select_all'):
			# create dialog
			dialog = InputDialog(self)

			dialog.set_title(_('Select items'))
			dialog.set_label(_('Selection pattern (eg.: *.jpg):'))
			dialog.set_text('*')

			# get response
			response = dialog.get_response()

			# commit selection
			if response[0] == gtk.RESPONSE_OK:
				active_object.select_all(response[1])

	def select_with_same_extension(self, widget, data=None):
		"""Select all items with same extension in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_get_selection') and hasattr(active_object, 'select_all'):
			selection = active_object._get_selection()

			if selection is not None\
			and os.path.splitext(selection)[1] != '':
				active_object.select_all('*{0}'.format(os.path.splitext(selection)[1]))

	def unselect_with_same_extension(self, widget, data=None):
		"""Select all items with same extension in active list"""
		active_object = self.get_active_object()

		if hasattr(active_object, '_get_selection') and hasattr(active_object, 'select_all'):
			selection = active_object._get_selection()

			if selection is not None\
			and os.path.splitext(selection)[1] != '':
				active_object.unselect_all('*{0}'.format(os.path.splitext(selection)[1]))

	def unselect_with_pattern(self, widget, data=None):
		"""Ask user for selection pattern and select matching items"""
		active_object = self.get_active_object()

		if hasattr(active_object, 'unselect_all'):
			# create dialog
			dialog = InputDialog(self)

			dialog.set_title(_('Unselect items'))
			dialog.set_label(_('Selection pattern (eg.: *.jpg):'))
			dialog.set_text('*')

			# get response
			response = dialog.get_response()

			# commit selection
			if response[0] == gtk.RESPONSE_OK:
				active_object.unselect_all(response[1])

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
			result_left = left_object.select_all(exclude_list=right_list)
			result_right = right_object.select_all(exclude_list=left_list)

			if result_left == result_right == 0:
				dialog = gtk.MessageDialog(
										self,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_INFO,
										gtk.BUTTONS_OK,
										_("First level of compared directories is identical.") 
									)
				dialog.run()
				dialog.destroy()

	def run(self):
		"""Start application"""
		DefaultList = self.plugin_classes['file_list']

		if self.arguments is not None and self.arguments.dont_load_tabs:
			# if specified tab list is empty, create default
			if self.arguments.left_tabs is None:
				self.create_tab(self.left_notebook, DefaultList)

			if self.arguments.right_tabs is None:
				self.create_tab(self.right_notebook, DefaultList)

		else:
			# load tabs in the left notebook
			if not self.load_tabs(self.left_notebook, 'left_notebook'):
				self.create_tab(self.left_notebook, DefaultList)

			# load tabs in the right notebook
			if not self.load_tabs(self.right_notebook, 'right_notebook'):
				self.create_tab(self.right_notebook, DefaultList)

		# create additional tabs
		if self.arguments is not None:
			if self.arguments.left_tabs is not None:
				for path in self.arguments.left_tabs:
					self.create_tab(self.left_notebook, DefaultList, path)

			if self.arguments.right_tabs is not None:
				for path in self.arguments.right_tabs:
					self.create_tab(self.right_notebook, DefaultList, path)

		# focus active notebook
		active_notebook_index = self.options.getint('main', 'active_notebook')
		notebook = (self.left_notebook, self.right_notebook)[active_notebook_index]

		notebook.grab_focus()

		# enter main loop
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
		index = notebook.append_page(new_tab, new_tab.get_tab_label())
		notebook.set_tab_reorderable(new_tab, True)
		notebook.set_tab_detachable(new_tab, True)

		# show tabs if needed
		if not self.options.getboolean('main', 'always_show_tabs'):
			notebook.set_show_tabs(notebook.get_n_pages() > 1)

		# focus tab if needed
		if self.options.getboolean('main', 'focus_new_tab'):
			notebook.set_current_page(index)
			new_tab._main_object.grab_focus()

		return new_tab

	def create_terminal_tab(self, notebook, path=None):
		"""Create terminal tab on selected notebook"""
		result = None

		if self.plugin_classes.has_key('system_terminal'):
			# only create tab if specified plugin is activated
			SystemTerminal = self.plugin_classes['system_terminal']
			result = self.create_tab(notebook, SystemTerminal, path)

		return result

	def close_tab(self, notebook, child):
		"""Safely remove tab and its children"""
		if notebook.get_n_pages() > 1:
			# call tab close handle method
			if hasattr(child, '_handle_tab_close'):
				child._handle_tab_close()

			# remove page from notebook
			notebook.remove_page(notebook.page_num(child))

			# hide tabs if needed
			if not self.options.getboolean('main', 'always_show_tabs'):
				notebook.set_show_tabs(notebook.get_n_pages() > 1)

			# block signal when destroying plugin with columns
			if hasattr(child, '_column_changed'):
				child._item_list.handler_block_by_func(child._column_changed)

			# kill the component
			child.destroy()

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

	def set_location_label(self, path):
		"""Set location label"""
		self.path_label.set_text(path)

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
		active_object = self.get_active_object()
		command = shlex.split(raw_command)

		if command[0] == 'cd' and hasattr(active_object, 'change_path'):
			# handle CD command
			if len(command) < 2:
				command.append(os.path.expanduser('~'))

			if os.path.isdir(os.path.join(active_object.path, command[1])):
				active_object.change_path(os.path.join(active_object.path, command[1]))
				active_object._main_object.grab_focus()

			handled = True

		if not handled:
			# try executing command
			try:
				if common.is_x_app(command[0]):
					# command is X based, just execute it
					os.system('{0} &'.format(raw_command))

				else:
					# command is console based, create terminal tab and fork it
					tab = self.create_terminal_tab(active_object._notebook)

					tab._close_on_child_exit = False
					tab._terminal.fork_command(
									command=command[0],
									argv=command,
									directory=active_object.path
								)

				handled = True

			except OSError:
				handled = False

		if not handled:
			print 'Unhandled command: {0}'.format(command[0])

	def save_tabs(self, notebook, section):
		"""Save opened tabs"""
		self.tab_options.remove_section(section)
		self.tab_options.add_section(section)

		for index in range(0, notebook.get_n_pages()):
			page = notebook.get_nth_page(index)

			# give plugin a chance to clean up
			if hasattr(page, '_handle_tab_close'):
				page._handle_tab_close()

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
												tab_sort_column,
												tab_sort_ascending,
												tab_path
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
		count = 0

		if self.tab_options.has_section(section):
			# if section exists, load it
			tab_list = self.tab_options.options(section)
			tab_list.sort()

			for tab in tab_list:
				data = self.tab_options.get(section, tab).split(':', 3)

				# extract data
				tab_class = data[0]
				tab_sort_column = data[1]
				tab_sort_ascending = data[2]
				tab_path = data[3]

				if self.plugin_class_exists(tab_class):
					# create new tab with specified data
					self.create_tab(
								notebook,
								globals()[tab_class],
								tab_path,
								tab_sort_column,
								tab_sort_ascending
							)

					count += 1

				else:
					# print error to console
					print 'Error: Unknown plugin class "{0}". Tab skipped!'.format(tab_class)

			result = count > 0

			# set active tab
			if result:
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
					('<Sunflower>/Edit/Preferences', 'P', gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK),
					('<Sunflower>/Mark/SelectAll', 'A', gtk.gdk.CONTROL_MASK),
					('<Sunflower>/Mark/SelectPattern', 'KP_Add', 0),
					('<Sunflower>/Mark/UnselectPattern', 'KP_Subtract', 0),
					('<Sunflower>/Mark/InvertSelection', 'KP_Multiply', 0),
					('<Sunflower>/Mark/SelectWithSameExtension', 'KP_Add', gtk.gdk.MOD1_MASK),
					('<Sunflower>/Mark/UnselectWithSameExtension', 'KP_Subtract', gtk.gdk.MOD1_MASK),
					('<Sunflower>/Mark/Compare', 'F12', 0),
					('<Sunflower>/Tools/FindFiles', 'F7', gtk.gdk.MOD1_MASK),
					('<Sunflower>/Tools/SynchronizeDirectories', 'F8', gtk.gdk.MOD1_MASK),
					('<Sunflower>/Tools/AdvancedRename', 'M', gtk.gdk.CONTROL_MASK),
					('<Sunflower>/Tools/MountManager', 'O', gtk.gdk.CONTROL_MASK),
					('<Sunflower>/View/Fullscreen', 'F11', 0),
					('<Sunflower>/View/Reload', 'R', gtk.gdk.CONTROL_MASK),
					('<Sunflower>/View/FastMediaPreview', 'F3', gtk.gdk.MOD1_MASK),
					('<Sunflower>/View/ShowHidden', 'H', gtk.gdk.CONTROL_MASK),
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
			self.command_options.write(open(os.path.join(self.config_path, 'commands'), 'w'))
			self.accel_options.write(open(os.path.join(self.config_path, 'accelerators'), 'w'))
			self.association_options.write(open(os.path.join(self.config_path, 'associations'), 'w'))

			# save accelerators
			self.accelerator_manager.save()
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
		self.command_options = RawConfigParser()
		self.accel_options = RawConfigParser()
		self.association_options = RawConfigParser()

		# load configuration from right folder on systems that support it
		if os.path.isdir(os.path.join(user.home, '.config')):
			self.config_path = os.path.join(user.home, '.config', 'sunflower')
		else:
			self.config_path = os.path.join(user.home, '.sunflower')

		self.options.read(os.path.join(self.config_path, 'config'))
		self.tab_options.read(os.path.join(self.config_path, 'tabs'))
		self.bookmark_options.read(os.path.join(self.config_path, 'bookmarks'))
		self.toolbar_options.read(os.path.join(self.config_path, 'toolbar'))
		self.command_options.read(os.path.join(self.config_path, 'commands'))
		self.accel_options.read(os.path.join(self.config_path, 'accelerators'))
		self.association_options.read(os.path.join(self.config_path, 'associations'))

		# load accelerators
		self.accelerator_manager.load(self.accel_options)

		# set default values
		if not self.options.has_section('main'):
			self.options.add_section('main')

		if not self.bookmark_options.has_section('bookmarks'):
			self.bookmark_options.add_section('bookmarks')

		if not self.command_options.has_section('tools'):
			self.command_options.add_section('tools')

		# define default options
		default_options = {
				'default_editor': 'gedit "{0}"',
				'wait_for_editor': 'False',
				'show_hidden': 'False',
				'show_mounts': 'True',
				'show_toolbar': 'False',
				'show_command_bar': 'False',
				'show_command_entry': 'True',
				'add_home': 'True',
				'system_bookmarks': 'False',
				'search_modifier': '000',
				'time_format': '%H:%M %d-%m-%y',
				'focus_new_tab': 'True',
				'row_hinting': 'False',
				'grid_lines': 0,
				'selection_color': '#ffff5e5e0000',
				'history_file': '.bash_history',
				'window': '960x550',
				'window_state': 0,
				'hide_on_close': 'False',
				'last_version': 0,
				'button_relief': 0,
				'terminal_scrollbars': 'True',
				'terminal_command': 'urxvt -embed {0}',
				'terminal_type': 0,
				'terminal_cursor_shape': 0,
				'terminal_use_system_font': 'True',
				'terminal_font': 'Monospace 12',
				'terminal_allow_bold': 'True',
				'terminal_mouse_autohide': 'False',
				'case_sensitive_sort': 'True',
				'plugins': 'file_list,system_terminal,default_toolbar',
				'reserve_size': 'False',
				'tab_button_icons': 'True',
				'always_show_tabs': 'True',
				'right_click_select': 'False',
				'headers_visible': 'True',
				'hide_operation_on_minimize': 'False',
				'ubuntu_coloring': 'False',
				'media_preview': 'False',
				'active_notebook': 0,
				'tab_close_button': 'True',
				'show_status_bar': 0,
				'human_readable_size': 'True',
				'expand_tabs': 0,
				'show_notifications': 'True',
				'operation_set_owner': 'False',
				'operation_set_mode': 'True',
				'operation_set_timestamp': 'True',
				'operation_silent': 'False',
				'operation_merge_in_silent': 'True',
				'operation_overwrite_in_silent': 'True'
			}

		# set default options
		for option, value in default_options.items():
			if not self.options.has_option('main', option):
				self.options.set('main', option, value)

	def focus_oposite_object(self, widget, data=None):
		"""Sets focus on oposite item list"""
		oposite_object = self.get_oposite_object(self.get_active_object())
		oposite_object._main_object.grab_focus()

		return True

	def focus_command_entry(self, widget=None, data=None):
		"""Focus main command entry widget"""
		self.command_edit.grab_focus()

	def focus_left_object(self, widget=None, data=None):
		"""Focus object in the left notebook"""
		left_object = self.left_notebook.get_nth_page(self.left_notebook.get_current_page())

		if left_object is not None:
			left_object._main_object.grab_focus()

	def focus_right_object(self, widget=None, data=None):
		"""Focus object in the right notebook"""
		right_object = self.right_notebook.get_nth_page(self.right_notebook.get_current_page())

		if right_object is not None:
			right_object._main_object.grab_focus()

	def get_active_object(self):
		"""Return active object"""
		return self._active_object

	def get_oposite_object(self, active_object):
		"""Return oposite object"""
		left_object = self.left_notebook.get_nth_page(self.left_notebook.get_current_page())
		right_object = self.right_notebook.get_nth_page(self.right_notebook.get_current_page())

		if active_object is left_object:
			result = right_object

		else:
			result = left_object

		return result

	def delegate_to_objects(self, caller, method_name, *args):
		"""Call specified method_name on all active objects of same class as caller

		Params:
		caller - object
		method_name - string
		args - arguments to be passed to specified methods

		"""
		# get all objects
		objects = self.left_notebook.get_children()
		objects.extend(self.right_notebook.get_children())

		# get only objects of specified class that are not caller
		filter_objects = lambda item: item.__class__ is caller.__class__ and item is not caller
		objects = filter(filter_objects, objects)

		# call specified method_name
		for item in objects:
			method = getattr(item, method_name)

			if callable(method):
				method(*args)

	def toggle_fullscreen(self, widget, data=None):
		"""Toggle application fullscreen"""
		if self.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self.unfullscreen()

		else:
			self.fullscreen()

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
				break

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

		# apply media preview settings
		media_preview = self.menu_manager.get_item_by_name('fast_media_preview')
		media_preview.set_active(self.options.getboolean('main', 'media_preview'))

		# recreate bookmarks menu
		self._create_bookmarks_menu()

		# recreate tools menu
		self._create_commands_menu()

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

		# apply settings for all tabs
		expand_tabs = self.options.getint('main', 'expand_tabs')

		for index in range(0, self.left_notebook.get_n_pages()):
			page = self.left_notebook.get_nth_page(index)

			# apply tab-expand
			if expand_tabs == TabExpand.NONE:
				self.left_notebook.child_set_property(page, 'tab-expand', False)

			elif expand_tabs == TabExpand.ACTIVE:
				self.left_notebook.child_set_property(page, 'tab-expand', page is self.get_active_object())

			else:
				self.left_notebook.child_set_property(page, 'tab-expand', True)

			# call plugin apply_settings
			if hasattr(page, 'apply_settings'):
				page.apply_settings()

		for index in range(0, self.right_notebook.get_n_pages()):
			page = self.right_notebook.get_nth_page(index)

			# apply tab-expand
			if expand_tabs == TabExpand.NONE:
				self.right_notebook.child_set_property(page, 'tab-expand', False)

			elif expand_tabs == TabExpand.ACTIVE:
				self.right_notebook.child_set_property(page, 'tab-expand', page is self.get_active_object())

			else:
				self.right_notebook.child_set_property(page, 'tab-expand', True)

			# call plugin apply_settings
			if hasattr(page, 'apply_settings'):
				page.apply_settings()

	def register_class(self, name, title, PluginClass):
		"""Register plugin class

		Classes registered using this method will be displayed in 'New tab' menu.
		Only plugins that provide tab components should be registered using this method!

		"""
		# add to plugin list
		self.plugin_classes[name] = PluginClass

		# create menu item and add it
		menu_item = gtk.MenuItem(title)
		menu_item.set_data('class', PluginClass)
		menu_item.connect('activate', self._handle_new_tab_click)

		menu_item.show()

		# add menu item
		menu = self.menu_manager.get_item_by_name('new_tab').get_submenu()
		menu.append(menu_item)

		# import class to globals
		globals()[PluginClass.__name__] = PluginClass

	def register_provider(self, ProviderClass):
		"""Register file provider class for specified protocol

		These classes will be used when handling all sorts of URI based operations
		like drag and drop and system bookmark handling.

		"""
		for protocol in ProviderClass.protocols:
			self.provider_classes[protocol] = ProviderClass

		for archive_type in ProviderClass.archives:
			self.archive_provider_classes[archive_type] = ProviderClass

	def register_toolbar_factory(self, FactoryClass):
		"""Register and create toolbar widget factory"""
		self.toolbar_manager.register_factory(FactoryClass)

	def register_rename_extension(self, name, ExtensionClass):
		"""Register class to be used in advanced rename tool"""
		if issubclass(ExtensionClass, RenameExtension) \
		and not self.rename_extension_classes.has_key(name):
			# register class
			self.rename_extension_classes[name] = ExtensionClass

		else:
			# report error to console
			if self.rename_extension_classes.has_key(name):
				print 'Error: Extension with name "{0}" is already registered!'

			if not issubclass(ExtensionClass, RenameExtension):
				print 'Error: Invalid object class!'

	def register_find_extension(self, name, ExtensionClass):
		"""Register class to be used in find files tool"""
		if issubclass(ExtensionClass, FindExtension) \
		and not self.find_extension_classes.has_key(name):
			# register extension
			self.find_extension_classes[name] = ExtensionClass

		else:
			# report error to console
			if self.find_extension_classes.has_key(name):
				print 'Error: Extension with name "{0}" is already registered!'

			if not issubclass(ExtensionClass, FindExtension):
				print 'Error: Invalid object class!'
	
	def register_mount_manager_extension(self, extension):
		"""Register mount manager extension"""
		self.mount_manager_extensions.append(extension)

	def plugin_class_exists(self, class_name):
		"""Check if specified class name exists in active plugins"""
		result = False

		for PluginClass in self.plugin_classes.values():
			if PluginClass.__name__ == class_name:
				result = True
				break

		return result

	def get_provider_by_protocol(self, protocol):
		"""Return provider class specified by protocol"""
		result = None

		if protocol in self.provider_classes.keys():
			result = self.provider_classes[protocol]

		return result

	def set_clipboard_text(self, text):
		"""Set text data to clipboard"""
		self.clipboard.set_text(text)

	def set_clipboard_item_list(self, operation, uri_list):
		"""Set clipboard to contain list of items

		operation - 'copy' or 'cut' string representing operation
		uri_list - list of URIs
		"""
		targets = [
				('x-special/gnome-copied-files', 0, 0),
				("text/uri-list", 0, 0)
			]
		raw_data = '{0}\n'.format(operation) + '\n'.join(uri_list)

		def get_func(clipboard, selection, info, data):
			"""Handle request from application"""
			target = selection.get_target()
			selection.set(target, 8, raw_data)

		def clear_func(clipboard, data):
			"""Clear function"""
			pass

		# set clipboard and return result
		return self.clipboard.set_with_data(targets, get_func, clear_func)

	def get_clipboard_text(self):
		"""Get text from clipboard"""
		return self.clipboard.wait_for_text()

	def get_clipboard_item_list(self):
		"""Get item list from clipboard"""
		result = None
		selection = self.clipboard.wait_for_contents('x-special/gnome-copied-files')

		# in case there is something to paste
		if selection is not None:
			data = selection.data.splitlines(False)

			operation = data[0]
			uri_list = data[1:]

			result = (operation, uri_list)

		return result

	def is_clipboard_text(self):
		"""Check if clipboard data is text"""
		return self.clipboard.wait_is_text_available()

	def is_clipboard_item_list(self):
		"""Check if clipboard data is URI list"""
		return self.clipboard.wait_is_uris_available()

	def show_about_window(self, widget=None, data=None):
		"""Show about window"""
		window = AboutWindow(self)
		window._show()

	def show_advanced_rename(self, widget, data=None):
		"""Show advanced rename tool for active list"""
		if len(self.rename_extension_classes) > 0 \
		and issubclass(self._active_object.__class__, ItemList):
			active_object = self.get_active_object()

			if issubclass(active_object.__class__, ItemList):
				AdvancedRename(active_object, self)

		elif not issubclass(self._active_object.__class__, ItemList):
			# active object is not item list
			dialog = gtk.MessageDialog(
								self,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_INFO,
								gtk.BUTTONS_OK,
								_(
									'Active object is not item list. Advanced '
									'rename tool needs files and directories.'
								)
							)
			dialog.run()
			dialog.destroy()

		elif len(self.rename_extension_classes) == 0:
			# no extensions found, report error to user
			dialog = gtk.MessageDialog(
								self,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_INFO,
								gtk.BUTTONS_OK,
								_(
									'No rename extensions were found. Please '
									'enable basic rename options plugin and try '
									'again.'
								)
							)
			dialog.run()
			dialog.destroy()

			# show preferences window
			self.preferences_window._show(None, tab_name='plugins')

	def show_find_files(self, widget=None, data=None):
		"""Show find files tool"""
		if len(self.find_extension_classes) > 0:
			# create find files window
			FindFiles(self._active_object, self)

		else:
			# no extensions found, report error to user
			dialog = gtk.MessageDialog(
								self,
								gtk.DIALOG_DESTROY_WITH_PARENT,
								gtk.MESSAGE_INFO,
								gtk.BUTTONS_OK,
								_(
									'No extensions for finding files were found. Please '
									'enable basic find file options plugin and try again.'
								)
							)
			dialog.run()
			dialog.destroy()

			# show preferences window
			self.preferences_window._show(None, tab_name='plugins')
