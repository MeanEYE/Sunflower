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
		self._extensions = []
		self._path = self._parent.path
		self._provider = None
		self._running = False

		# thread control object
		self._abort = Event()

		if hasattr(self._parent, 'get_provider'):
			self._provider = self._parent.get_provider()

		# configure window
		self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)

		self.window.set_title(_('Find files'))
		self.window.set_default_size(550, 500)
		self.window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self.window.set_transient_for(application)
		self.window.set_border_width(7)
		self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
		self.window.set_wmclass('Sunflower', 'Sunflower')

		self.window.connect('key-press-event', self._handle_key_press)

		# create interface
		vbox = Gtk.VBox(False, 7)

		# create path and basic options
		self._table_basic = Gtk.Table(3, 2, False)
		self._table_basic.set_col_spacings(5)
		self._table_basic.set_row_spacings(2)

		label_path = Gtk.Label(label=_('Search in:'))
		label_path.set_alignment(0, 0.5)

		self._entry_path = Gtk.Entry()
		self._entry_path.connect('activate', self.find_files)

		if hasattr(self._parent, 'path'):
			# get path from the parent
			self._entry_path.set_text(self._parent.path)

		else:
			# parent has no path, set user home directory
			self._entry_path.set_text(os.path.expanduser(os.path.expanduser('~')))

		button_browse = Gtk.Button(label=_('Browse'))
		button_browse.connect('clicked', self._choose_directory)

		self._checkbox_recursive = Gtk.CheckButton(label=_('Search recursively'))
		self._checkbox_recursive.set_active(True)

		# create extensions notebook
		self._extension_list = Gtk.Notebook()

		# create list
		self._list = Gtk.ListStore(str, str, str)
		self._names = Gtk.TreeView(model=self._list)

		cell_icon = Gtk.CellRendererPixbuf()
		cell_name = Gtk.CellRendererText()
		cell_directory = Gtk.CellRendererText()

		col_name = Gtk.TreeViewColumn(_('Name'))
		col_name.set_expand(True)

		col_directory = Gtk.TreeViewColumn(_('Location'))
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

		container = Gtk.ScrolledWindow()
		container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		container.set_shadow_type(Gtk.ShadowType.IN)

		# create status label
		self._status = Gtk.Label()
		self._status.set_alignment(0, 0.5)
		self._status.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
		self._status.set_property('no-show-all', True)

		# create controls
		hbox_controls = Gtk.HBox(False, 5)

		self._image_find = Gtk.Image()
		self._image_find.set_from_stock(Gtk.STOCK_MEDIA_PLAY, Gtk.IconSize.BUTTON)

		self._button_find = Gtk.Button()
		self._button_find.set_label(_('Start'))
		self._button_find.set_image(self._image_find)
		self._button_find.connect('clicked', self.find_files)

		button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._close_window)

		# pack interface
		self._table_basic.attach(label_path, 0, 1, 0, 1, xoptions=Gtk.AttachOptions.SHRINK|Gtk.AttachOptions.FILL)
		self._table_basic.attach(self._entry_path, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL)
		self._table_basic.attach(button_browse, 2, 3, 0, 1, xoptions=Gtk.AttachOptions.SHRINK|Gtk.AttachOptions.FILL)
		self._table_basic.attach(self._checkbox_recursive, 1, 2, 1, 2)

		container.add(self._names)

		hbox_controls.pack_end(self._button_find, False, False, 0)
		hbox_controls.pack_end(button_close, False, False, 0)

		vbox.pack_start(self._table_basic, False, False, 0)
		vbox.pack_start(self._extension_list, False, False, 0)
		vbox.pack_end(hbox_controls, False, False, 0)
		vbox.pack_end(self._status, False, False, 0)
		vbox.pack_end(container, True, True, 0)

		self.window.add(vbox)

		# create extensions
		self.__create_extensions()

		# show all widgets
		self.window.show_all()

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

			# add tab
			self._extension_list.append_page(extension.get_container(), Gtk.Label(label=title))

			# store extension for later use
			self._extensions.append(extension)

	def __update_status_label(self, path):
		"""Update status label with current scanning path"""
		self._status.set_text(path)

	def __update_status(self, running=True):
		"""Update button status"""
		self._running = running

		if running:
			# disable interface to prevent changes during search
			self._table_basic.set_sensitive(False)
			self._extension_list.set_sensitive(False)

			# show status bar
			self._status.show()

			# update find button
			self._image_find.set_from_stock(Gtk.STOCK_MEDIA_STOP, Gtk.IconSize.BUTTON)
			self._button_find.set_label(_('Stop'))

		else:
			# enable interface to prevent changes during search
			self._table_basic.set_sensitive(True)
			self._extension_list.set_sensitive(True)

			# hide status bar
			self._status.hide()

			# update find button
			self._image_find.set_from_stock(Gtk.STOCK_MEDIA_PLAY, Gtk.IconSize.BUTTON)
			self._button_find.set_label(_('Start'))

	def __find_files(self, path, children, scan_recursively):
		"""Threaded find files method"""
		scan_queue = []
		extension_list = []

		# prepare extension objects for operation
		for child in children:
			extension_list.append(child.extension)

		# tell extensions search is starting
		self.emit('notify-start')

		# update thread status
		GObject.idle_add(self.__update_status, True)
		GObject.idle_add(self.__update_status_label, path)

		# add current path to scan queue
		try:
			item_list = self._provider.list_dir(path)
			item_list = map(lambda new_item: os.path.join(path, new_item), item_list)
			scan_queue.extend(item_list)

		except:
			pass

		# traverse through directories
		while not self._abort.is_set() and len(scan_queue) > 0:
			# get next item in queue
			item = scan_queue.pop(0)

			if self._provider.is_dir(item) and scan_recursively:
				# extend scan queue with directory content
				GObject.idle_add(self.__update_status_label, item)

				try:
					item_list = self._provider.list_dir(item)
					item_list = map(lambda new_item: os.path.join(item, new_item), item_list)

					scan_queue.extend(item_list)

				except:
					pass

			# check if item fits cirteria
			match = True

			for extension in extension_list:
				if not extension.is_path_ok(item):
					match = False
					break

			# add item if score is right
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

	def _choose_directory(self, widget=None, data=None):
		"""Show 'FileChooser' dialog"""
		dialog = Gtk.FileChooserDialog(
							title=_('Find files'),
							parent=self._application,
							action=Gtk.FileChooserAction.SELECT_FOLDER,
							buttons=(
								Gtk.STOCK_CANCEL,
								Gtk.ResponseType.REJECT,
								Gtk.STOCK_OK,
								Gtk.ResponseType.ACCEPT
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
		pass

	def find_files(self, widget=None, data=None):
		"""Start searching for files"""
		if not self._running:
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
			active_children = [child for child in self._extension_list.get_children()
							   if child.extension.is_active()]

			if len(active_children) == 0:
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
					'children': active_children,
					'scan_recursively': self._checkbox_recursive.get_active()
				}
			thread = Thread(target=self.__find_files, kwargs=params)
			thread.start()

		else:
			# thread is running, set abort event
			self._abort.set()
