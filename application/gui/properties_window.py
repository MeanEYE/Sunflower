import os
import gtk
import gio


class PropertiesWindow(gtk.Window):
	"""Properties window for files and directories"""
	
	def __init__(self, application, provider, path):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		# store parameters locally
		self._application = application
		self._provider = provider
		self._path = path
		
		# file monitor, we'd like to update info if file changes
		self._monitor = gio.File(self._path).monitor_file()
		
		# get item information
		title = _('{0} Properties').format(os.path.basename(path))
		
		icon_manager = application.icon_manager 
		icon_list = (
					icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_MENU),
					icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_BUTTON),
					icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_SMALL_TOOLBAR),
					icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_LARGE_TOOLBAR),
					icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_DIALOG)
				)
		
		# configure window
		self.set_title(title)
		self.set_size_request(410, 410)
		self.set_border_width(5)
		self.set_icon_list(*icon_list)
		
		# create interface
		vbox = gtk.VBox(False, 5)
		
		self._notebook = gtk.Notebook()
		
		self._notebook.append_page(
								self._create_basic_tab(),
								gtk.Label(_('Basic'))
							)
		self._notebook.append_page(
								self._create_permissions_tab(),
								gtk.Label(_('Permissions'))
							)
		self._notebook.append_page(
								self._create_open_with_tab(),
								gtk.Label(_('Open With'))
							)
		
		# create buttons
		hbox_buttons = gtk.HBox(False, 5)
		
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._close_window)
		
		# pack interface
		hbox_buttons.pack_end(button_close, False, False, 0)
		
		vbox.pack_start(self._notebook, True, True, 0)
		vbox.pack_start(hbox_buttons, False, False, 0)
		
		self.add(vbox)
		
		# show all widgets
		self.show_all()
		
	def _close_window(self, widget=None, data=None):
		"""Close properties window"""
		self._monitor.cancel()
		self.hide()
		
	def _item_changes(self, monitor, file, other_file, event, data=None):
		"""Event triggered when monitored file changes"""
		pass
		
	def _create_basic_tab(self):
		"""Create tab containing basic information"""
		tab = gtk.Table(7, 3)
		
		# configure table
		tab.set_border_width(10)
		
		# create icon
		pixbuf = self._application.icon_manager.get_icon_for_file(
															self._path,
															gtk.ICON_SIZE_DIALOG 
														)
		icon = gtk.Image()
		icon.set_from_pixbuf(pixbuf)
		
		tab.attach(icon, 0, 1, 0, 7)
		
		# labels
		label_name = gtk.Label(_('Name:'))
		label_type = gtk.Label(_('Type:'))
		label_size = gtk.Label(_('Size:'))
		label_location = gtk.Label(_('Location:'))
		label_volume = gtk.Label(_('Volume:'))
		label_accessed = gtk.Label(_('Accessed:'))
		label_modified = gtk.Label(_('Modified:'))
		
		label_name.set_alignment(0, 0.5)
		label_type.set_alignment(0, 0.5)
		label_size.set_alignment(0, 0.5)
		label_location.set_alignment(0, 0.5)
		label_volume.set_alignment(0, 0.5)
		label_accessed.set_alignment(0, 0.5)
		label_modified.set_alignment(0, 0.5)
		
		tab.attach(label_name, 1, 2, 0, 1)
		tab.attach(label_type, 1, 2, 1, 2)
		tab.attach(label_size, 1, 2, 2, 3)
		tab.attach(label_location, 1, 2, 3, 4)
		tab.attach(label_volume, 1, 2, 4, 5)
		tab.attach(label_accessed, 1, 2, 5, 6)
		tab.attach(label_modified, 1, 2, 6, 7)
		
		# values
		self._entry_name = gtk.Entry()
		self._label_type = gtk.Label()
		self._label_size = gtk.Label()
		
		
		return tab
	
	def _create_permissions_tab(self):
		"""Create tab containing item permissions and ownership"""
		tab = gtk.Table()
		
		return tab
	
	def _create_open_with_tab(self):
		"""Create tab containing list of applications that can open this file"""
		tab = gtk.VBox(False, 5)
		
		return tab


