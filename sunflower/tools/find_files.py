from __future__ import absolute_import

import os

from gi.repository import Gtk, Gdk, Pango, GObject
from threading import Thread, Event


class Column:
	ICON = 0
	NAME = 1
	DIRECTORY = 2


class FindFiles(GObject.GObject):
	"""Find files tool"""

	__gtype_name__ = 'Sunflower_FindFiles'
	__gsignals__ = {
				'notify-start': (GObject.SignalFlags.RUN_LAST, None, ()),
				'notify-stop': (GObject.SignalFlags.RUN_LAST, None, ())
			}

	def __init__(self, parent, application):
		GObject.GObject.__init__(self)

		# store parameters
		self._parent = parent
		self._application = application
		self._path = self._parent.path
		self._provider = None
		self._running = False

		# thread control object
		self._abort = Event()

		if hasattr(self._parent, 'get_provider'):
			self._provider = self._parent.get_provider()

		# configure window
		self.window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)

		self.window.set_title(_('Find files'))
		self.window.set_default_size(550, 400)
		self.window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self.window.set_transient_for(application)
		self.window.set_wmclass('Sunflower', 'Sunflower')

		self.window.connect('key-press-event', self._handle_key_press)

		# create header
		self.header_bar = Gtk.HeaderBar.new()
		self.header_bar.set_show_close_button(True)
		self.window.set_titlebar(self.header_bar)

		self.stack_switcher = Gtk.StackSwitcher.new()
		self.header_bar.set_custom_title(self.stack_switcher)

		self.stack = Gtk.Stack.new()
		self.stack_switcher.set_stack(self.stack)
		self.window.add(self.stack)

		# busy indicator
		self.spinner = Gtk.Spinner.new()
		self.spinner.set_margin_left(10)
		self.header_bar.pack_start(self.spinner)

		# create configuration interface
		vbox = Gtk.VBox.new(False, 0)
		self.stack.add_titled(vbox, 'criteria', _('Criteria'))

		search_bar = Gtk.SearchBar.new()
		search_bar.set_search_mode(True)
		vbox.pack_start(search_bar, False, False, 0)

		# create path and basic options
		vbox_search = Gtk.VBox.new(False, 5)
		search_bar.add(vbox_search)

		hbox = Gtk.HBox.new(False, 5)
		vbox_search.pack_start(hbox, True, False, 0)

		self._entry_path = Gtk.Entry()
		self._entry_path.set_size_request(300, -1)
		self._entry_path.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'folder-symbolic')
		self._entry_path.connect('icon-release', self._browse_directory)
		self._entry_path.connect('activate', self.find_files)

		path = self._parent.path if hasattr(self._parent, 'path') else os.path.expanduser('~')
		self._entry_path.set_text(path)
		hbox.pack_start(self._entry_path, False, False, 0)

		self.button_start = Gtk.Button.new_with_label(_('Start'))
		self.button_start.connect('clicked', self.find_files)
		hbox.pack_start(self.button_start, False, False, 0)

		self.button_stop = Gtk.Button.new_from_icon_name('media-playback-stop-symbolic', Gtk.IconSize.BUTTON)
		self.button_stop.connect('clicked', self.stop_search)
		self.button_stop.set_sensitive(False)
		self.header_bar.pack_end(self.button_stop)

		self._checkbox_recursive = Gtk.CheckButton.new_with_label(_('Search recursively'))
		self._checkbox_recursive.set_active(True)
		vbox_search.pack_start(self._checkbox_recursive, False, False, 0)

		# create extensions container
		hbox = Gtk.HBox.new(False, 0)
		vbox.pack_start(hbox, True, True, 0)

		self.extensions_list = Gtk.ListBox.new()
		self.extensions_list.set_size_request(200, -1)
		self.extensions_list.connect('row-selected', self.__handle_extension_click)

		self.extensions_container = Gtk.Stack.new()

		hbox.pack_start(self.extensions_list, False, False, 0)
		hbox.pack_start(Gtk.Separator.new(Gtk.Orientation.VERTICAL), False, False, 0)
		hbox.pack_start(self.extensions_container, False, False, 0)

		# create list
		results_container = Gtk.ScrolledWindow.new()
		results_container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		self.stack.add_titled(results_container, 'results', _('Results'))

		self._list = Gtk.ListStore.new((str, str, str))
		self._names = Gtk.TreeView.new_with_model(self._list)
		results_container.add(self._names)

		cell_icon = Gtk.CellRendererPixbuf.new()
		cell_name = Gtk.CellRendererText.new()
		cell_directory = Gtk.CellRendererText.new()

		col_name = Gtk.TreeViewColumn.new()
		col_name.set_title(_('Name'))
		col_name.set_expand(True)

		col_directory = Gtk.TreeViewColumn.new()
		col_directory.set_title(_('Location'))
		col_directory.set_expand(True)

		# pack renderer
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_directory.pack_start(cell_directory, True)

		# connect renderer attributes
		col_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_name.add_attribute(cell_name, 'text', Column.NAME)
		col_directory.add_attribute(cell_directory, 'text', Column.DIRECTORY)

		self._names.append_column(col_name)
		self._names.append_column(col_directory)

		self._names.connect('row-activated', self.__handle_row_activated)

		self.__create_extensions()
		self.window.show_all()

	def __handle_extension_click(self, widget, title, data=None):
		"""Handle clicking on extension's title widget."""
		container = title.get_extension().get_container()
		self.extensions_container.set_visible_child(container)

	def __handle_row_activated(self, treeview, path, view_column, data=None):
		"""Handle actions on list"""
		# get list selection
		selection = treeview.get_selection()
		list_, iter_ = selection.get_selected()

		# we need selection for this
		if iter_ is None: return

		name = list_.get_value(iter_, Column.NAME)
		path = list_.get_value(iter_, Column.DIRECTORY)

		# get active object
		active_object = self._application.get_active_object()

		if hasattr(active_object, 'change_path'):
			# change path
			active_object.change_path(path, name)

			# close window
			self._close_window()

		else:
			# notify user about active object
			dialog = Gtk.MessageDialog(
								self.window,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.INFO,
								Gtk.ButtonsType.OK,
								_(
									'Active object doesn\'t support changing '
									'path. Set focus on a different object, '
									'preferably file list, and try again.'
								)
							)
			dialog.run()
			dialog.destroy()

	def __create_extensions(self):
		"""Create rename extensions"""
		for ExtensionClass in self._application.find_extension_classes.values():
			extension = ExtensionClass(self)
			title = extension.get_title()
			list_row = extension.get_title_widget()

			self.extensions_list.add(list_row)
			self.extensions_container.add_named(extension.get_container(), title)

	def __update_status(self, running=True):
		"""Update button status"""
		self._running = running

		if running:
			self.stack.set_visible_child_name('results')
			self.button_start.set_sensitive(False)
			self.button_stop.set_sensitive(True)
			self.spinner.start()

		else:
			self.button_start.set_sensitive(True)
			self.button_stop.set_sensitive(False)
			self.spinner.stop()

	def __find_files(self, path, children, scan_recursively):
		"""Threaded find files method."""
		scan_queue = []
		extension_list = list(map(lambda child: child.extension, children))

		self.emit('notify-start')
		GObject.idle_add(self.__update_status, True)

		# add current path to scan queue
		try:
			item_list = self._provider.list_dir(path)
			item_list = map(lambda new_item: os.path.join(path, new_item), item_list)
			scan_queue.extend(item_list)
		except:
			pass

		# traverse through directories
		while not self._abort.is_set() and len(scan_queue) > 0:
			item = scan_queue.pop(0)

			# extend scan queue with directory content
			if self._provider.is_dir(item) and scan_recursively:
				try:
					item_list = self._provider.list_dir(item)
					item_list = map(lambda new_item: os.path.join(item, new_item), item_list)
					scan_queue.extend(item_list)
				except:
					pass

			match = True
			for extension in extension_list:
				match &= extension.is_path_ok(self._provider, item)
				if not match: break  # no point in testing other extensions

			if match:
				name = os.path.basename(item)
				path = os.path.dirname(item)
				icon = self._application.icon_manager.get_icon_for_file(item)

				self._list.append((icon, name, path))

		# update thread status
		GObject.idle_add(self.__update_status, False)

		# tell extensions search has been stopped
		self.emit('notify-stop')

	def _close_window(self, widget=None, data=None):
		"""Close window"""
		self._abort.set()  # notify search thread we are terminating
		self.window.destroy()

	def _browse_directory(self, widget=None, icon_position=None, event=None, data=None):
		"""Prompt user for directoy selection."""
		dialog = Gtk.FileChooserDialog(
							title=_('Find files'),
							parent=self._application,
							action=Gtk.FileChooserAction.SELECT_FOLDER,
							buttons=(
								_('Cancel'), Gtk.ResponseType.REJECT,
								_('Select'), Gtk.ResponseType.ACCEPT
								)
						)
		dialog.set_filename(self._entry_path.get_text())
		response = dialog.run()

		if response == Gtk.ResponseType.ACCEPT:
			self._entry_path.set_text(dialog.get_filename())

		dialog.destroy()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys"""
		if event.keyval == Gdk.KEY_Escape:
			self._close_window()

	def stop_search(self, widget=None, data=None):
		"""Stop searching for files"""
		self._abort.set()

	def find_files(self, widget=None, data=None):
		"""Start searching for files"""
		if self._running:
			return

		# thread is not running, start it
		path = self._entry_path.get_text()

		# make sure we have a valid provider
		if self._provider is None:
			ProviderClass = self._application.get_provider_by_protocol('file')
			self._provider = ProviderClass(self._parent)

		# check if specified path exists
		if not self._provider.is_dir(path):
			dialog = Gtk.MessageDialog(
								self.window,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.ERROR,
								Gtk.ButtonsType.OK,
								_(
									'Specified path is not valid or doesn\'t '
									'exist anymore. Please check your selection '
									'and try again.'
								)
							)
			dialog.run()
			dialog.destroy()

			return

		# get list of active extensions
		extension_containers = self.extensions_container.get_children()
		active_extensions = list(filter(lambda cont: cont.extension.active, extension_containers))

		if len(active_extensions) == 0:
			dialog = Gtk.MessageDialog(
								self.window,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.WARNING,
								Gtk.ButtonsType.OK,
								_(
									'You need to enable at least one extension '
									'in order to find files and directories!'
								)
							)
			dialog.run()
			dialog.destroy()
			return

		# set thread control objects
		self._abort.clear()

		# clear existing list
		self._list.clear()

		# start the thread
		params = {
				'path': path,
				'children': active_extensions,
				'scan_recursively': self._checkbox_recursive.get_active()
			}
		thread = Thread(target=self.__find_files, kwargs=params)
		thread.start()
