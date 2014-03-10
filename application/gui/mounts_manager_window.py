import gtk
import gio

from parameters import Parameters
from plugin_base.mount_manager_extension import MountManagerExtension, ExtensionFeatures

# redefine some GIO constants for legacy support
GIO_MOUNT_MOUNT_NONE = gio.MOUNT_MOUNT_NONE if hasattr(gio, 'MOUNT_MOUNT_NONE') else 0
GIO_MOUNT_UNMOUNT_NONE = gio.MOUNT_UNMOUNT_NONE if hasattr(gio, 'MOUNT_UNMOUNT_NONE') else 0


class MountsColumn:
	ICON = 0
	NAME = 1
	MARKUP_NAME = 2
	URI = 3
	OBJECT = 4
	SYSTEM_WIDE = 5


class VolumesColumn:
	ICON = 0
	NAME = 1
	UUID = 2
	URI = 3
	MOUNTED = 4
	OBJECT = 5


class PagesColumn:
	ICON = 0
	NAME = 1
	COUNT = 2
	TAB_NUMBER = 3


class MountsManagerWindow(gtk.Window):

	def __init__(self, parent):
		# create mount manager window
		gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)

		self._parent = parent
		self._application = self._parent._application
		self._mounts = None
		self._volumes = None
		self._volume_list = []
		self._extensions = []

		# main menu items
		self._menu_unmount = None
		
		# configure window
		self.set_title(_('Mount manager'))
		self.set_default_size(700, 400)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(self._application)
		self.set_wmclass('Sunflower', 'Sunflower')
		self.set_border_width(7)

		self.connect('delete-event', self._hide)
		self.connect('key-press-event', self._handle_key_press)

		# create store for window list
		self._pages_store = gtk.ListStore(str, str, int, int)
		
		# create user interface
		vbox = gtk.VBox(False, 5)
		hbox = gtk.HBox(False, 5)
		hbox_controls = gtk.HBox(False, 5)

		self._tabs = gtk.Notebook()
		self._tabs.set_show_tabs(False)
		self._tabs.set_show_border(False)
		self._tabs.connect('switch-page', self._handle_page_switch)

		# create page list
		label_container = gtk.ScrolledWindow()
		label_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		label_container.set_shadow_type(gtk.SHADOW_IN)
		label_container.set_size_request(130, -1)

		self._tab_labels = gtk.TreeView(model=self._pages_store)

		cell_icon = gtk.CellRendererPixbuf()
		cell_label = gtk.CellRendererText()
		cell_count = gtk.CellRendererText()

		col_label = gtk.TreeViewColumn(None)

		col_label.pack_start(cell_icon, False)
		col_label.pack_start(cell_label, True)
		col_label.pack_start(cell_count, False)

		col_label.add_attribute(cell_icon, 'icon-name', PagesColumn.ICON)
		col_label.add_attribute(cell_label, 'text', PagesColumn.NAME)
		col_label.set_cell_data_func(cell_count, self._mount_count_data_function)

		self._tab_labels.append_column(col_label)
		self._tab_labels.set_headers_visible(False)
		self._tab_labels.connect('cursor-changed', self._handle_cursor_change)
		
		# create buttons
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._hide)
		
		# pack user interface
		label_container.add(self._tab_labels)

		hbox_controls.pack_end(button_close, False, False, 0)

		hbox.pack_start(label_container, False, False, 0)
		hbox.pack_start(self._tabs, True, True, 0)

		vbox.pack_start(hbox, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)
		
		self.add(vbox)

	def create_extensions(self):
		"""Create all registered extensions"""
		class_list = [MountsExtension, VolumesExtension]
		class_list.extend(self._application.mount_manager_extensions)

		for ExtensionClass in class_list:
			extension = ExtensionClass(self._parent, self)

			# get extension information
			icon, name = extension.get_information()
			container = extension.get_container()

			# add page
			self.add_page(icon, name, container, extension)
			self._extensions.append(extension)

			# store local extensions for later use
			if isinstance(extension, MountsExtension):
				self._mounts = extension

			if isinstance(extension, VolumesExtension):
				self._volumes = extension

		# tell parent we are ready for mount list population
		self._parent._populate_list()

	def _mount_count_data_function(self, column, renderer, model, current_iter, data=None):
		"""Set content of cell renderer when drawing number of mounts extension has"""
		count = model.get_value(current_iter, PagesColumn.COUNT)
		renderer.set_property('text', count if count > 0 else '')

	def _attach_menus(self):
		"""Attach menu items to main window"""
		menu_manager = self._application.menu_manager

		# get unmount menu item from main menu
		self._menu_unmount = menu_manager.get_item_by_name('unmount_menu').get_submenu()

		# create item for usage when there are no mounts
		self._menu_item_no_mounts = menu_manager.get_item_by_name('mount_list_empty')
		self._menu_item_no_mounts.set_property('no-show-all', True)

	def _add_item(self, text, uri, icon):
		"""Add new menu item to the list"""
		self._application.bookmarks.add_mount(text, icon, uri)

	def _add_unmount_item(self, text, uri, icon):
		"""Add new menu item used for unmounting"""
		image = gtk.Image()
		image.set_from_icon_name(icon, gtk.ICON_SIZE_MENU)

		menu_item = gtk.ImageMenuItem()
		menu_item.set_label(text)
		menu_item.set_image(image)
		menu_item.set_always_show_image(True)
		menu_item.set_data('uri', uri)
		menu_item.connect('activate', self._parent._unmount_item_menu_callback)
		menu_item.show()

		self._menu_unmount.append(menu_item)

		# update menu
		self._menu_updated()

	def _remove_item(self, mount_point):
		"""Remove item based on device name"""
		self._application.bookmarks.remove_mount(mount_point)

		for item in self._menu_unmount.get_children():
			if item.get_data('uri') == mount_point: self._menu_unmount.remove(item)

		# update menu
		self._menu_updated()

	def _menu_updated(self):
		"""Method called whenever menu is updated"""
		has_mounts = self._application.bookmarks.get_mount_count() > 0

		try: 
			self._menu_item_no_mounts.set_visible(not has_mounts)

		except AttributeError:
			self._menu_item_no_mounts.set_property('visible', not has_mounts)

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in mount manager list"""
		result = False

		if gtk.keysyms._1 <= event.keyval <= gtk.keysyms._9:
			# handle switching to page number
			page_index = event.keyval - int(gtk.keysyms._1)
			self._tabs.set_current_page(page_index)
			result = True

		elif event.keyval == gtk.keysyms.Return:
			# handle pressing return
			result = True

		elif event.keyval == gtk.keysyms.Escape:
			# hide window on escape
			self._hide()
			result = True

		return result

	def _handle_cursor_change(self, widget, data=None):
		"""Change active tab when cursor is changed"""
		selection = self._tab_labels.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			new_tab = item_list.get_value(selected_iter, PagesColumn.TAB_NUMBER)

			self._tabs.handler_block_by_func(self._handle_page_switch)
			self._tabs.set_current_page(new_tab)
			self._tabs.handler_unblock_by_func(self._handle_page_switch)

			# tell extension to take focus
			new_object = self._tabs.get_nth_page(new_tab)
			extension = new_object.get_data('extension')

			if extension is not None and hasattr(extension, 'focus_object'):
				extension.focus_object()

		return True

	def _handle_page_switch(self, widget, page, page_num, data=None):
		"""Handle changing page without user interaction"""
		self._tab_labels.handler_block_by_func(self._handle_cursor_change)
		self._tab_labels.set_cursor((page_num,))
		self._tab_labels.handler_unblock_by_func(self._handle_cursor_change)

		# tell extension to take focus
		new_object = self._tabs.get_nth_page(page_num)
		extension = new_object.get_data('extension')

		if extension is not None and hasattr(extension, 'focus_object'):
			extension.focus_object()

		return True

	def _hide(self, widget=None, data=None):
		"""Hide mount manager"""
		self.hide()
		return True

	def _add_volume(self, volume, startup=False):
		"""Add volume entry"""
		if volume not in self._volume_list:
			self._volume_list.append(volume)
			self._volumes.add_volume(volume, startup)

	def _remove_volume(self, volume):
		"""Remove volume entry"""
		del self._volume_list[self._volume_list.index(volume)]
		self._volumes.remove_volume(volume)

	def _volume_mounted(self, volume):
		"""Mark volume as mounted"""
		self._volumes.volume_mounted(volume)

	def _volume_unmounted(self, volume):
		"""Mark volume as unmounted"""
		self._volumes.volume_unmounted(volume)

	def _notify_mount_add(self, icon, name, uri):
		"""Notification from mount manager about mounted volume"""
		self._mounts.add_mount(icon, name, uri, self._mounts)

	def _notify_mount_remove(self, uri):
		"""Notification from mount manager about unmounted volume"""
		self._mounts.remove_mount(uri)

	def add_page(self, icon_name, name, container, extension):
		"""Create new page in mounts manager with specified parameters.
		
		This method provides easy way to extend mounts manager by adding container
		of your choice to notebook presented to users. Extension parameter must be class
		descendant of MountManagerExtension.

		"""
		# add tab to store
		tab_number = self._tabs.get_n_pages()
		self._pages_store.append((icon_name, name, 0, tab_number))

		# assign extension to container
		container.set_data('extension', extension)

		# append new page
		self._tabs.append_page(container)

	def add_mount(self, icon, name, uri, extension):
		"""Add mount entry"""
		self._mounts.add_mount(icon, name, uri, extension)

	def remove_mount(self, uri):
		"""Remove mount entry"""
		self._mounts.remove_mount(uri)

	def set_count(self, extension, count):
		"""Set number of mounts extension has"""
		icon_name, extension_name = extension.get_information()

		# set count
		for row in self._pages_store:
			if self._pages_store.get_value(row.iter, PagesColumn.NAME) == extension_name:
				self._pages_store.set_value(row.iter, PagesColumn.COUNT, count)
				break


class MountsExtension(MountManagerExtension):
	"""Extension that provides list of all mounted resources"""

	features = set([ExtensionFeatures.SYSTEM_WIDE,])
	
	def __init__(self, parent, window):
		MountManagerExtension.__init__(self, parent, window)

		# create store for mounts
		self._store = gtk.ListStore(str, str, str, str, object, bool)
		self._mounts = {}

		# create interface
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		self._list = gtk.TreeView(model=self._store)
		self._list.set_show_expanders(True)
		self._list.set_search_column(MountsColumn.NAME)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_system = gtk.CellRendererToggle()

		# try to set icon size
		try:
			cell_icon.props.stock_size = gtk.ICON_SIZE_LARGE_TOOLBAR
		except:
			pass

		col_name = gtk.TreeViewColumn(_('Name'))
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.set_expand(True)

		col_name.add_attribute(cell_icon, 'icon-name', MountsColumn.ICON)
		col_name.add_attribute(cell_name, 'markup', MountsColumn.MARKUP_NAME)

		col_system = gtk.TreeViewColumn(_('Systemwide'), cell_system, active=MountsColumn.SYSTEM_WIDE)

		self._list.append_column(col_name)
		self._list.append_column(col_system)

		# create controls
		image_jump = gtk.Image()
		image_jump.set_from_icon_name(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
		button_jump = gtk.Button()
		button_jump.set_image(image_jump)
		button_jump.set_label(_('Open'))
		button_jump.connect('clicked', self._open_selected, False)
		try:
			button_jump.set_can_default(True)
		except AttributeError:
			button_jump.set_property('can-default', True)

		image_new_tab = gtk.Image()
		image_new_tab.set_from_icon_name('tab-new', gtk.ICON_SIZE_BUTTON)
		button_new_tab = gtk.Button()
		button_new_tab.set_image(image_new_tab)
		button_new_tab.set_label(_('Open in tab'))
		button_new_tab.set_tooltip_text(_('Open selected URI in new tab'))
		button_new_tab.connect('clicked', self._open_selected, True)

		button_unmount = gtk.Button()
		button_unmount.set_label(_('Unmount'))
		button_unmount.connect('clicked', self._unmount_selected)

		# use spinner if possible to denote busy operation
		if hasattr(gtk, 'Spinner'):
			self._spinner = gtk.Spinner()
			self._spinner.set_size_request(20, 20)
			self._spinner.set_property('no-show-all', True)

		else:
			self._spinner = None

		# pack interface
		container.add(self._list)

		self._controls.pack_start(button_jump, False, False, 0)
		self._controls.pack_start(button_new_tab, False, False, 0)
		self._controls.pack_end(button_unmount, False, False, 0)
		
		self._container.pack_start(container, True, True, 0)

	def _get_iter_by_uri(self, uri):
		"""Get mount list iter by URI"""
		result = None
		
		# find iter by uuid
		for mount_row in self._store:
			if self._store.get_value(mount_row.iter, MountsColumn.URI) == uri:
				result = mount_row.iter
				break

		return result

	def _open_selected(self, widget, in_new_tab=False):
		"""Open selected mount"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			uri = item_list.get_value(selected_iter, MountsColumn.URI)
			active_object = self._application.get_active_object()
			
			if not in_new_tab and hasattr(active_object, 'change_path'):
				active_object.change_path(uri)

			else:
				# create new tab
				options = Parameters()
				options.set('path', uri)

				self._application.create_tab(
								active_object._notebook,
								active_object.__class__,
								options
							)
		return True

	def _unmount_selected(self, widget, data=None):
		"""Unmount selected item"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()
		
		if selected_iter is not None:
			uri = item_list.get_value(selected_iter, MountsColumn.URI)

			# let all extensions know we are performing unmount
			for extension in self._window._extensions:
				if extension.can_handle(uri):
					extension.unmount(uri)

	def can_handle(self, uri):
		"""Returns boolean denoting if specified URI can be handled by this extension"""
		return True

	def get_information(self):
		"""Get extension information"""
		return 'harddrive', _('Mounts')

	def focus_object(self):
		"""Focus main list on managers request"""
		self._list.grab_focus()

	def add_mount(self, icon, name, uri, extension):
		"""Add mount to the list"""
		system_wide = True

		# check extension features
		if extension is not None:
			system_wide = ExtensionFeatures.SYSTEM_WIDE in extension.get_features()

		# create markup name
		if uri is not None:
			markup_name = '{0}\n<small>{1}</small>'.format(name, uri)

		else:
			markup_name = name

		self._store.append((icon, name, markup_name, uri, extension, system_wide))

		# notify main window about number change
		self._window.set_count(self, len(self._store))

	def remove_mount(self, uri):
		"""Remove mount from the list"""
		mount_iter = self._get_iter_by_uri(uri)

		# remove mount if exists
		if mount_iter is not None:
			self._store.remove(mount_iter)

		# remove mount objects if exists
		if uri in self._mounts:
			self._mounts.pop(uri)

		# notify main window about number change
		self._window.set_count(self, len(self._store))

	def unmount(self, uri):
		"""Unmount item with specified URI"""
		self._parent._unmount_by_uri(uri)


class VolumesExtension(MountManagerExtension):
	"""Extension that provides access to volumes"""
	
	def __init__(self, parent, window):
		MountManagerExtension.__init__(self, parent, window)
		self._store = gtk.ListStore(str, str, str, str, bool, object)
		self._volumes = {}

		# create interface
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		self._list = gtk.TreeView(model=self._store)
		self._list.set_show_expanders(True)
		self._list.set_search_column(MountsColumn.NAME)

		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()
		cell_mounted = gtk.CellRendererToggle()
		cell_mounted.connect('toggled', self._mount_toggled)

		col_name = gtk.TreeViewColumn(_('Name'))
		col_name.pack_start(cell_icon, False)
		col_name.pack_start(cell_name, True)
		col_name.set_expand(True)

		col_name.add_attribute(cell_icon, 'icon-name', VolumesColumn.ICON)
		col_name.add_attribute(cell_name, 'text', VolumesColumn.NAME)

		col_mounted = gtk.TreeViewColumn(_('Mounted'), cell_mounted, active=VolumesColumn.MOUNTED)

		self._list.append_column(col_name)
		self._list.append_column(col_mounted)

		# create buttons
		button_mount = gtk.Button()
		button_mount.set_label(_('Mount'))
		button_mount.connect('clicked', self._mount_volume)

		button_unmount = gtk.Button()
		button_unmount.set_label(_('Unmount'))
		button_unmount.connect('clicked', self._unmount_volume)

		# use spinner if possible to denote busy operation
		if hasattr(gtk, 'Spinner'):
			self._spinner = gtk.Spinner()
			self._spinner.set_size_request(20, 20)
			self._spinner.set_property('no-show-all', True)

		else:
			self._spinner = None

		# pack interface
		container.add(self._list)

		if self._spinner is not None:
			self._controls.pack_start(self._spinner, False, False, 0)
		self._controls.pack_end(button_unmount, False, False, 0)
		self._controls.pack_end(button_mount, False, False, 0)

		self._container.pack_start(container, True, True, 0)

	def _get_iter_by_uuid(self, uuid):
		"""Get volume list iter by UUID"""
		result = None
		
		# find iter by uuid
		for volume_row in self._store:
			if self._store.get_value(volume_row.iter, VolumesColumn.UUID) == uuid:
				result = volume_row.iter
				break

		return result

	def _get_iter_by_object(self, volume):
		"""Get volume list iter by UUID"""
		result = None
		
		# find iter by uuid
		for volume_row in self._store:
			if self._store.get_value(volume_row.iter, VolumesColumn.OBJECT) is volume:
				result = volume_row.iter
				break

		return result

	def _show_spinner(self):
		"""Show spinner"""
		if self._spinner is not None:
			self._spinner.show()
			self._spinner.start()

	def _hide_spinner(self):
		"""Hide spinner"""
		if self._spinner is not None:
			self._spinner.stop()
			self._spinner.hide()

	def _mount_toggled(self, cell, path):
		"""Handle changing mounted state of a volume"""
		volume = self._store[path][VolumesColumn.OBJECT]
		is_mounted = self._store[path][VolumesColumn.MOUNTED]

		# show spinner animation
		self._show_spinner()

		if is_mounted:
			# unmount volume
			mount = volume.get_mount()
			mount.unmount(self._unmount_finish, GIO_MOUNT_UNMOUNT_NONE, None, volume)

		else:
			# mount volume
			volume.mount(None, self._mount_finish, GIO_MOUNT_MOUNT_NONE, None, None)

	def _mount_finish(self, volume, result, data=None):
		"""Callback function for volume mount"""
		try:
			volume.mount_finish(result)
		except:
			pass

		# update volume list
		mount = volume.get_mount()

		if mount is not None:
			self.volume_mounted(volume)

		else:
			self.volume_unmounted(volume)

		# hide spinner
		self._hide_spinner()

	def _unmount_finish(self, mount, result, volume=None):
		"""Callback function for unmounting"""
		try:
			mount.unmount_finish(result)
		except:
			pass

		# update volume status
		self.volume_unmounted(volume)

		# hide spinner
		self._hide_spinner()

	def _mount_volume(self, widget, data=None):
		"""Mount selected volume"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None \
		and not item_list.get_value(selected_iter, VolumesColumn.MOUNTED):
			# show busy spinner if possible
			self._show_spinner()

			# perform auto-mount of volume
			volume = item_list.get_value(selected_iter, VolumesColumn.OBJECT)
			volume.mount(None, self._mount_finish, GIO_MOUNT_MOUNT_NONE, None, None)

	def _unmount_volume(self, widget, data=None):
		"""Unmount selected volume"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None \
		and item_list.get_value(selected_iter, VolumesColumn.MOUNTED):
			# show spinner
			self._show_spinner()

			# unmount
			volume = item_list.get_value(selected_iter, VolumesColumn.OBJECT)
			mount = volume.get_mount()
			mount.unmount(self._unmount_finish, GIO_MOUNT_UNMOUNT_NONE, None, volume)

	def get_information(self):
		"""Get extension information"""
		return 'computer', _('Volumes')

	def focus_object(self):
		"""Focus main list on managers request"""
		self._list.grab_focus()

	def add_volume(self, volume, startup=False):
		"""Add volume to the list"""
		icon_names = volume.get_icon().to_string()
		icon = self._application.icon_manager.get_mount_icon_name(icon_names)
		name = volume.get_name()
		uuid = volume.get_uuid()
		mounted = False
		mount_uri = None

		# get mount if possible
		mount = volume.get_mount()
		if mount is not None:
			mounted = True
			mount_uri = mount.get_root().get_uri()

		# add new entry to store
		self._store.append((icon, name, uuid, mount_uri, mounted, volume))

		# get automount options
		options = self._parent._application.options
		section = options.section('operations')

		if startup:
			option = section.get('automount_start')
			should_mount = option and volume.can_mount()

		else:
			option = section.get('automount_insert')
			should_mount = option and volume.can_mount()

		# auto mount if needed
		if mount is None \
		and should_mount:
			# show busy spinner if possible
			self._show_spinner()
		
			# perform auto-mount of volume
			volume.mount(None, self._mount_finish, GIO_MOUNT_MOUNT_NONE, None, None)

		# notify main window about number change
		self._window.set_count(self, len(self._store))

	def remove_volume(self, volume):
		"""Remove volume from the list"""
		volume_iter = self._get_iter_by_object(volume)

		# remove if volume exists
		if volume_iter is not None:
			self._store.remove(volume_iter)

		# notify main window about number change
		self._window.set_count(self, len(self._store))

	def volume_mounted(self, volume):
		"""Mark volume with specified UUID as mounted"""
		volume_iter = self._get_iter_by_object(volume)
		mount = volume.get_mount()
		uri = mount.get_root().get_uri()

		# set data if volume exists
		if volume_iter is not None:
			self._store.set_value(volume_iter, VolumesColumn.URI, uri)
			self._store.set_value(volume_iter, VolumesColumn.MOUNTED, True)

	def volume_unmounted(self, volume):
		"""Mark volume with as unmounted"""
		volume_iter = self._get_iter_by_object(volume)

		# set data if volume exists
		if volume_iter is not None:
			self._store.set_value(volume_iter, VolumesColumn.URI, None)
			self._store.set_value(volume_iter, VolumesColumn.MOUNTED, False)
