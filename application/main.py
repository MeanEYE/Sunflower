import os
import sys


try:
	# check if gtk is available
	import gi
	gi.require_version('Gtk', '3.0')
	gi.require_version('Notify', '0.7')

except:
	# print error and die
	print 'Error starting Sunflower, missing GTK 3.0+'
	sys.exit(1)

else:
	# import required modules
	from gi.repository import Gtk, Gdk, GObject, Gio, GLib

# try to set process title
try:
	from setproctitle import setproctitle
	setproctitle('sunflower')

except ImportError:
	pass

# handle UTF-8 encoded strings while interacting with GTK
import sys; reload(sys)
sys.setdefaultencoding('utf-8')

import common
from config import Config
from gui.main_window import MainWindow


class Arguments(object):
	def __init__(self):
		self.dont_load_plugins = False
		self.dont_load_tabs = False
		self.is_remote = False
		self.left_tabs = None
		self.right_tabs = None
		self.left_terminals = None
		self.right_terminals  = None


class Sunflower(Gtk.Application):
	application_id = 'org.sunflower'

	def __init__(self):
		self.window = None

		# temporary loading config to find multiple_instances setting
		options = Config('config', common.get_config_path())
		if options.get('multiple_instances'):
			application_id = None # defining no application id enables multiple instances

		# call parent constructor
		Gtk.Application.__init__(
				self,
				application_id=self.application_id,
				flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
			)

		# load translations
		common.load_translation()

		# create command line option entries
		version_entry = GLib.OptionEntry()
		version_entry.long_name = 'version'
		version_entry.short_name = ord('v')
		version_entry.flags = 0
		version_entry.arg = GLib.OptionArg.NONE
		version_entry.arg_date = None
		version_entry.description = _('Version')
		version_entry.arg_description = None

		no_plugins_entry = GLib.OptionEntry()
		no_plugins_entry.long_name = 'no-plugins'
		no_plugins_entry.short_name = ord('p')
		no_plugins_entry.flags = 0
		no_plugins_entry.arg = GLib.OptionArg.NONE
		no_plugins_entry.arg_date = None
		no_plugins_entry.description = _('skip loading additional plugins')
		no_plugins_entry.arg_description = None

		no_load_tabs_entry = GLib.OptionEntry()
		no_load_tabs_entry.long_name = 'no-load-tabs'
		no_load_tabs_entry.short_name = ord('t')
		no_load_tabs_entry.flags = 0
		no_load_tabs_entry.arg = GLib.OptionArg.NONE
		no_load_tabs_entry.arg_date = None
		no_load_tabs_entry.description = _('skip loading additional plugins')
		no_load_tabs_entry.arg_description = None

		left_tab_entry = GLib.OptionEntry()
		left_tab_entry.long_name = 'left-tab'
		left_tab_entry.short_name = ord('l')
		left_tab_entry.flags = 0
		left_tab_entry.arg = GLib.OptionArg.STRING_ARRAY
		left_tab_entry.arg_date = None
		left_tab_entry.description = _('open new tab on the left notebook')
		left_tab_entry.arg_description = None

		right_tab_entry = GLib.OptionEntry()
		right_tab_entry.long_name = 'right-tab'
		right_tab_entry.short_name = ord('r')
		right_tab_entry.flags = 0
		right_tab_entry.arg = GLib.OptionArg.STRING_ARRAY
		right_tab_entry.arg_date = None
		right_tab_entry.description = _('open new tab on the right notebook')
		right_tab_entry.arg_description = None

		left_terminal_entry = GLib.OptionEntry()
		left_terminal_entry.long_name = 'left-terminal'
		left_terminal_entry.short_name = ord('L')
		left_terminal_entry.flags = 0
		left_terminal_entry.arg = GLib.OptionArg.STRING_ARRAY
		left_terminal_entry.arg_date = None
		left_terminal_entry.description = _('open terminal tab on the left notebook')
		left_terminal_entry.arg_description = None

		right_terminal_entry = GLib.OptionEntry()
		right_terminal_entry.long_name = 'right-terminal'
		right_terminal_entry.short_name = ord('R')
		right_terminal_entry.flags = 0
		right_terminal_entry.arg = GLib.OptionArg.STRING_ARRAY
		right_terminal_entry.arg_date = None
		right_terminal_entry.description = _('open terminal tab on the right notebook')
		right_terminal_entry.arg_description = None

		option_entries = [
				version_entry, no_plugins_entry, no_load_tabs_entry,
				left_tab_entry, right_tab_entry, left_terminal_entry,
				right_terminal_entry
			]

		self.add_main_option_entries(option_entries)

	def do_startup(self):
		"""Handle application startup."""
		application_path = os.path.abspath(os.path.dirname(sys.argv[0]))
		if application_path not in sys.path:
			sys.path.insert(1, application_path)

		Gtk.Application.do_startup(self)

	def do_activate(self):
		"""Handle application activation."""
		if not self.window:
			self.window = MainWindow(
					application=self,
					dont_load_plugins=self.arguments is not None and self.arguments.dont_load_plugins
				)

		self.window.create_tabs(self.arguments)

	def do_command_line(self, command_line):
		"""Handle command line argumens and flags."""

		def absolute_path(cwd, path):
			if '://' not in path:
				path = os.path.normpath(os.path.join(cwd, path))
			return path

		self.arguments = Arguments()
		self.arguments.is_remote = command_line.get_is_remote()

		options = command_line.get_options_dict()
		working_directory = command_line.get_cwd()

		if options.contains('no-plugins'):
			self.arguments.dont_load_plugins = True

		if options.contains('no-load-tabs'):
			self.arguments.dont_load_tabs = True

		if options.contains('left-tab'):
			paths = options.lookup_value('left-tab')
			self.arguments.left_tabs =  map(lambda path: absolute_path(working_directory, path), paths)

		if options.contains('right-tab'):
			paths = options.lookup_value('right-tab')
			self.arguments.right_tabs = map(lambda path: absolute_path(working_directory, path), paths)

		if options.contains('left-terminal'):
			paths = options.lookup_value('left-terminal')
			self.arguments.left_terminals = map(lambda path: absolute_path(working_directory, path), paths)

		if options.contains('right-terminal'):
			paths = options.lookup_value('right-terminal')
			self.arguments.right_terminals = map(lambda path: absolute_path(working_directory, path), paths)

		self.activate()
		return 0

	def do_handle_local_options(self, options):
		"""Handle local command line options."""
		if options.contains('version'):
			print ('{0} {1[major]}.{1[minor]}{1[stage]} ({1[build]})').format(_('Sunflower'), MainWindow.version)
			return 0

		return -1


# create application
application = Sunflower()
exit_status = application.run(sys.argv)
sys.exit(exit_status)
