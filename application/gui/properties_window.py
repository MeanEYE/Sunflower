import os
import gtk
import gio
import pango
import locale
import time
import pwd
import grp
import common

from plugin_base.monitor import MonitorSignals
from plugin_base.provider import Support


class Column:
	SELECTED = 0
	ICON_NAME = 1
	APPLICATION_NAME = 2
	APPLICATION_ID = 3


class EmblemColumn:
	SELECTED = 0
	NAME = 1
	ICON_NAME = 2


class PropertiesWindow(gtk.Window):
	"""Properties window for files and directories"""

	def __init__(self, application, provider, path):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		# store parameters locally
		self._application = application
		self._provider = provider
		self._path = path
		self._is_file = self._provider.is_file(self._path)
		self._permission_updating = False
		self._mode = None

		# get content type
		if self._provider.is_dir(self._path):
			self._mime_type = 'inode/directory'

		else:
			self._mime_type = application.associations_manager.get_mime_type(self._path)

			# content type is unknown, try to detect using content
			if application.associations_manager.is_mime_type_unknown(self._mime_type):
				data = application.associations_manager.get_sample_data(path, provider)
				self._mime_type = application.associations_manager.get_mime_type(data=data)

		# file monitor, we'd like to update info if file changes
		self._create_monitor()

		# get item information
		title = _('{0} Properties').format(os.path.basename(path))

		icon_manager = application.icon_manager
		if self._is_file:
			# get icon for specified file
			self._icon_name = icon_manager.get_icon_for_file(path)

		else:
			# get folder icon
			self._icon_name = icon_manager.get_icon_for_directory(path)

		# configure window
		self.set_title(title)
		self.set_geometry_hints(min_width=410, min_height=410)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_border_width(5)
		self.set_icon_name(self._icon_name)
		self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.set_wmclass('Sunflower', 'Sunflower')

		self.connect('key-press-event', self._handle_key_press)
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
		self._notebook.append_page(
								self._create_emblems_tab(),
								gtk.Label(_('Emblems'))
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

		# update widgets to represent item state
		self._update_data()

		# show all widgets
		self.show_all()

	def _close_window(self, widget=None, data=None):
		"""Close properties window"""
		self._monitor.cancel()
		self.destroy()

	def _item_changes(self, monitor, file, other_file, event, data=None):
		"""Event triggered when monitored file changes"""
		if event is gio.FILE_MONITOR_EVENT_DELETED:
			# item was removed, close dialog
			self.destroy()

		else:
			# item was changed, update data
			self._update_data()

	def _rename_item(self, widget=None, data=None):
		"""Handle renaming item"""
		item_exists = self._provider.exists(
							self._entry_name.get_text(),
							relative_to=os.path.dirname(self._path)
						)

		if item_exists:
			# item with the same name already exists
			dialog = gtk.MessageDialog(
									self,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_OK,
									_(
										"File or directory with specified name already "
										"exists in current directory. Item could not "
										"be renamed."
									)
								)
			dialog.run()
			dialog.destroy()

			# restore old name
			self._entry_name.set_text(os.path.basename(self._path))

		else:
			# rename item
			try:
				self._provider.rename_path(
									os.path.basename(self._path),
									self._entry_name.get_text()
								)

				self._path = os.path.join(
									os.path.dirname(self._path),
									self._entry_name.get_text()
								)

				# recreate item monitor
				self._create_monitor()

			except IOError as error:
				# problem renaming item
				dialog = gtk.MessageDialog(
										self,
										gtk.DIALOG_DESTROY_WITH_PARENT,
										gtk.MESSAGE_ERROR,
										gtk.BUTTONS_OK,
										_(
											"Error renaming specified item. Make sure "
											"you have enough permissions."
										) +	"\n\n{0}".format(error)
									)
				dialog.run()
				dialog.destroy()

	def _create_monitor(self):
		"""Create item monitor"""
		self._monitor = gio.File(self._path).monitor_file()
		self._monitor.connect('changed', self._item_changes)

	def _load_associated_applications(self):
		"""Get associated applications with file/directory"""
		associations_manager = self._application.associations_manager
		application_list = associations_manager.get_application_list_for_type(self._mime_type)
		default_application = associations_manager.get_default_application_for_type(self._mime_type)

		# clear existing list
		self._store.clear()

		# add all applications to the list
		for application in application_list:
			self._store.append((
							application.id == default_application.id,
							application.icon,
							application.name,
							application.id
						))

	def _update_data(self):
		"""Update widgets to represent item state"""
		associations_manager = self._application.associations_manager

		# get the rest of the infromation
		description = associations_manager.get_mime_description(self._mime_type)
		time_format = self._application.options.section('item_list').get('time_format')
		size_format = self._application.options.get('size_format')
		item_stat = self._provider.get_stat(self._path, extended=True)

		# get item size
		if self._is_file:
			# file size
			item_size = common.format_size(item_stat.size, size_format)

		else:
			# directory size
			try:
				dir_size = len(self._provider.list_dir(self._path))

			except OSError:
				dir_size = 0

			finally:
				item_size = '{0} {1}'.format(
									locale.format('%d', dir_size, True),
									ngettext('item', 'items', dir_size)
								)

		# set mode
		self._mode = item_stat.mode

		# time_format item time
		item_a_date = time.strftime(time_format, time.localtime(item_stat.time_access))
		item_m_date = time.strftime(time_format, time.localtime(item_stat.time_modify))

		# get volume
		try:
			mount = gio.File(self._path).find_enclosing_mount()
			volume_name = mount.get_name()

		except gio.Error:
			# item is not on any known volume
			volume_name = _('unknown')

		# update widgets
		self._entry_name.set_text(os.path.basename(self._path))
		self._label_type.set_text('{0}\n{1}'.format(description, self._mime_type))
		self._label_size.set_text(item_size)
		self._label_location.set_text(os.path.dirname(os.path.abspath(self._path)))
		self._label_volume.set_text(volume_name)
		self._label_accessed.set_text(item_a_date)
		self._label_modified.set_text(item_m_date)

		# update permissions list
		self._permission_update_mode(initial_update=True)

		# update ownership
		self._ownership_update()

		# update "open with" list
		self._load_associated_applications()

	def _permission_update_octal(self, widget, data=None):
		"""Update octal entry box"""
		if self._permission_updating: return

		data = int(str(data), 8)
		self._mode += (-1, 1)[widget.get_active()] * data

		self._permission_update_mode()

	def _permission_update_checkboxes(self, widget=None, data=None):
		"""Update checkboxes accordingly"""
		self._permission_updating = True
		self._permission_owner_read.set_active(self._mode & 0b100000000)
		self._permission_owner_write.set_active(self._mode & 0b010000000)
		self._permission_owner_execute.set_active(self._mode & 0b001000000)
		self._permission_group_read.set_active(self._mode & 0b000100000)
		self._permission_group_write.set_active(self._mode & 0b000010000)
		self._permission_group_execute.set_active(self._mode & 0b000001000)
		self._permission_others_read.set_active(self._mode & 0b000000100)
		self._permission_others_write.set_active(self._mode & 0b000000010)
		self._permission_others_execute.set_active(self._mode & 0b000000001)
		self._permission_updating = False

	def _permission_entry_activate(self, widget, data=None):
		"""Handle octal mode change"""
		self._mode = int(widget.get_text(), 8)
		self._permission_update_mode()

	def _permission_update_mode(self, initial_update=False):
		"""Update widgets"""
		self._permission_octal_entry.set_text('{0}'.format(oct(self._mode)))
		self._permission_update_checkboxes()

		# set file mode
		if not initial_update:
			self._provider.set_mode(self._path, self._mode)

	def _ownership_update(self):
		"""Update owner and group"""
		stat = self._provider.get_stat(self._path)

		self._combobox_owner.handler_block_by_func(self._ownership_changed)
		self._combobox_group.handler_block_by_func(self._ownership_changed)

		# remove old entries
		self._list_owner.clear()
		self._list_group.clear()

		# for local file system fill comboboxes with available user and group names
		if self._provider.is_local:
			for i, user in enumerate(pwd.getpwall()):
				self._list_owner.append((user.pw_name, user.pw_uid))
				if user.pw_uid == stat.user_id:
					self._combobox_owner.set_active(i)

			for i, group in enumerate(grp.getgrall()):
				self._list_group.append((group.gr_name, group.gr_gid))
				if group.gr_gid == stat.group_id:
					self._combobox_group.set_active(i)

		# for remote file systems simply set owner and group
		else:
			self._list_owner.append((stat.user_id, stat.user_id))
			self._list_group.append((stat.group_id, stat.group_id))
			self._combobox_owner.set_active(0)
			self._combobox_group.set_active(0)

		self._combobox_owner.handler_unblock_by_func(self._ownership_changed)
		self._combobox_group.handler_unblock_by_func(self._ownership_changed)

	def _ownership_changed(self, widget, data=None):
		"""Handle changing owner or group"""
		# get new owner and group
		owner_iter = self._combobox_owner.get_active_iter()
		group_iter = self._combobox_group.get_active_iter()
		owner_id = self._list_owner.get_value(owner_iter, 1)
		group_id = self._list_group.get_value(group_iter, 1)

		# save new owner and group
		try:
			self._provider.set_owner(self._path, owner_id, group_id)

		except OSError as error:
			dialog = gtk.MessageDialog(
			                        self,
			                        gtk.DIALOG_DESTROY_WITH_PARENT,
			                        gtk.MESSAGE_ERROR,
			                        gtk.BUTTONS_OK,
			                        _(
										'Error changing owner or group'
									) + '\n\n{0}'.format(error)
			                   )
			dialog.run()
			dialog.destroy()
			self._ownership_update()

	def _change_default_application(self, renderer, path, data=None):
		"""Handle changing default application"""
		active_item = self._store[path]
		application_id = active_item[Column.APPLICATION_ID]
		associations_manager = self._application.associations_manager

		# set default application for mime type
		application_set = associations_manager.set_default_application_for_type(self._mime_type, application_id)

		# select active item
		if application_set:
			for item in self._store:
				item[Column.SELECTED] = item.path == active_item.path

		return True

	def _toggle_emblem(self, renderer, path, data=None):
		"""Handle toggling emblem selection"""
		active_item = self._emblems_store.get_iter(path)
		is_selected = not self._emblems_store.get_value(active_item, EmblemColumn.SELECTED)
		emblem = self._emblems_store.get_value(active_item, EmblemColumn.NAME)

		# modify value in list store
		self._emblems_store.set_value(active_item, EmblemColumn.SELECTED, is_selected)

		# update emblem database
		update_method = (
					self._application.emblem_manager.remove_emblem,
					self._application.emblem_manager.add_emblem
				)[is_selected]

		path, item_name = os.path.split(self._path)
		update_method(path, item_name, emblem)

		# notify monitor of our change
		parent = self._provider.get_parent()
		parent_path = self._provider.get_path()

		if parent_path == self._provider.get_root_path(parent_path):
			item_path = self._path[len(parent_path):]

		else:
			item_path = self._path[len(parent_path) + 1:]

		queue = parent.get_monitor().get_queue()
		queue.put((MonitorSignals.EMBLEM_CHANGED, item_path, None))

		return True

	def _create_basic_tab(self):
		"""Create tab containing basic information"""
		tab = gtk.VBox(False, 0)
		table = gtk.Table(7, 3)

		# configure table
		tab.set_border_width(10)

		# create icon
		icon = gtk.Image()
		icon.set_from_icon_name(self._icon_name, gtk.ICON_SIZE_DIALOG)

		vbox_icon = gtk.VBox(False, 0)
		vbox_icon.pack_start(icon, False, False)
		table.attach(vbox_icon, 0, 1, 0, 7, gtk.SHRINK)

		# labels
		label_name = gtk.Label(_('Name:'))
		label_type = gtk.Label(_('Type:'))
		label_size = gtk.Label(_('Size:'))
		label_location = gtk.Label(_('Location:'))
		label_volume = gtk.Label(_('Volume:'))
		label_accessed = gtk.Label(_('Accessed:'))
		label_modified = gtk.Label(_('Modified:'))

		# configure labels
		label_name.set_alignment(0, 0.5)
		label_type.set_alignment(0, 0)
		label_size.set_alignment(0, 0)
		label_location.set_alignment(0, 0)
		label_volume.set_alignment(0, 0)
		label_accessed.set_alignment(0, 0)
		label_modified.set_alignment(0, 0)

		# pack labels
		table.attach(label_name, 1, 2, 0, 1)
		table.attach(label_type, 1, 2, 1, 2)
		table.attach(label_size, 1, 2, 2, 3)
		table.attach(label_location, 1, 2, 3, 4)
		table.attach(label_volume, 1, 2, 4, 5)
		table.attach(label_accessed, 1, 2, 5, 6)
		table.attach(label_modified, 1, 2, 6, 7)

		# value containers
		self._entry_name = gtk.Entry()
		self._label_type = gtk.Label()
		self._label_size = gtk.Label()
		self._label_location = gtk.Label()
		self._label_volume = gtk.Label()
		self._label_accessed = gtk.Label()
		self._label_modified = gtk.Label()

		# configure labels
		self._label_type.set_alignment(0, 0)
		self._label_type.set_selectable(True)
		self._label_size.set_alignment(0, 0)
		self._label_size.set_selectable(True)
		self._label_location.set_alignment(0, 0)
		self._label_location.set_selectable(True)
		self._label_location.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
		self._label_volume.set_alignment(0, 0)
		self._label_volume.set_selectable(True)
		self._label_accessed.set_alignment(0, 0)
		self._label_accessed.set_selectable(True)
		self._label_modified.set_alignment(0, 0)
		self._label_modified.set_selectable(True)

		# pack value containers
		table.attach(self._entry_name, 2, 3, 0, 1)
		table.attach(self._label_type, 2, 3, 1, 2)
		table.attach(self._label_size, 2, 3, 2, 3)
		table.attach(self._label_location, 2, 3, 3, 4)
		table.attach(self._label_volume, 2, 3, 4, 5)
		table.attach(self._label_accessed, 2, 3, 5, 6)
		table.attach(self._label_modified, 2, 3, 6, 7)

		# connect events
		self._entry_name.connect('activate', self._rename_item)

		# configure table
		table.set_row_spacings(5)
		table.set_row_spacing(2, 30)
		table.set_row_spacing(4, 30)
		table.set_col_spacing(0, 10)
		table.set_col_spacing(1, 10)

		# pack table
		tab.pack_start(table, False, False, 0)

		return tab

	def _create_permissions_tab(self):
		"""Create tab containing item permissions and ownership"""
		tab = gtk.VBox(False, 5)
		tab.set_border_width(10)

		# create 'Access' frame
		frame_access = gtk.Frame()
		frame_access.set_label(_('Access'))

		table_access = gtk.Table(4, 4, False)
		table_access.set_border_width(5)

		# create widgets
		label = gtk.Label(_('User:'))
		label.set_alignment(0, 0.5)
		table_access.attach(label, 0, 1, 0, 1)

		label = gtk.Label(_('Group:'))
		label.set_alignment(0, 0.5)
		table_access.attach(label, 0, 1, 1, 2)

		label = gtk.Label(_('Others:'))
		label.set_alignment(0, 0.5)
		table_access.attach(label, 0, 1, 2, 3)

		# owner checkboxes
		self._permission_owner_read = gtk.CheckButton(_('Read'))
		self._permission_owner_read.connect('toggled', self._permission_update_octal, (1 << 2) * 100)
		table_access.attach(self._permission_owner_read, 1, 2, 0, 1)

		self._permission_owner_write = gtk.CheckButton(_('Write'))
		self._permission_owner_write.connect('toggled', self._permission_update_octal, (1 << 1) * 100)
		table_access.attach(self._permission_owner_write, 2, 3, 0, 1)

		self._permission_owner_execute = gtk.CheckButton(_('Execute'))
		self._permission_owner_execute.connect('toggled', self._permission_update_octal, (1 << 0) * 100)
		table_access.attach(self._permission_owner_execute, 3, 4, 0, 1)

		# group checkboxes
		self._permission_group_read = gtk.CheckButton(_('Read'))
		self._permission_group_read.connect('toggled', self._permission_update_octal, (1 << 2) * 10)
		table_access.attach(self._permission_group_read, 1, 2, 1, 2)

		self._permission_group_write = gtk.CheckButton(_('Write'))
		self._permission_group_write.connect('toggled', self._permission_update_octal, (1 << 1) * 10)
		table_access.attach(self._permission_group_write, 2, 3, 1, 2)

		self._permission_group_execute = gtk.CheckButton(_('Execute'))
		self._permission_group_execute.connect('toggled', self._permission_update_octal, (1 << 0) * 10)
		table_access.attach(self._permission_group_execute, 3, 4, 1, 2)

		# others checkboxes
		self._permission_others_read = gtk.CheckButton(_('Read'))
		self._permission_others_read.connect('toggled', self._permission_update_octal, (1 << 2))
		table_access.attach(self._permission_others_read, 1, 2, 2, 3)

		self._permission_others_write = gtk.CheckButton(_('Write'))
		self._permission_others_write.connect('toggled', self._permission_update_octal, (1 << 1))
		table_access.attach(self._permission_others_write, 2, 3, 2, 3)

		self._permission_others_execute = gtk.CheckButton(_('Execute'))
		self._permission_others_execute.connect('toggled', self._permission_update_octal, (1 << 0))
		table_access.attach(self._permission_others_execute, 3, 4, 2, 3)

		# octal representation
		label = gtk.Label(_('Octal:'))
		label.set_alignment(0, 0.5)
		table_access.attach(label, 0, 1, 3, 4)

		self._permission_octal_entry = gtk.Entry(4)
		self._permission_octal_entry.set_width_chars(5)
		self._permission_octal_entry.connect('activate', self._permission_entry_activate)
		table_access.attach(self._permission_octal_entry, 1, 2, 3, 4)
		table_access.set_row_spacing(2, 10)

		# create ownership frame
		frame_ownership = gtk.Frame()
		frame_ownership.set_label(_('Ownership'))

		table_ownership = gtk.Table(2, 2, False)
		table_ownership.set_border_width(5)

		# create widgets
		label = gtk.Label(_('User:'))
		label.set_alignment(0, 0.5)
		table_ownership.attach(label, 0, 1, 0, 1)

		label = gtk.Label(_('Group:'))
		label.set_alignment(0, 0.5)
		table_ownership.attach(label, 0, 1, 1, 2)

		# create owner combobox
		self._list_owner = gtk.ListStore(str, int)
		cell_owner = gtk.CellRendererText()

		self._combobox_owner = gtk.ComboBox(self._list_owner)
		self._combobox_owner.connect('changed', self._ownership_changed)
		self._combobox_owner.pack_start(cell_owner)
		self._combobox_owner.add_attribute(cell_owner, 'text', 0)

		table_ownership.attach(self._combobox_owner, 1, 2, 0, 1)

		# create group combobox
		self._list_group = gtk.ListStore(str, int)
		cell_group = gtk.CellRendererText()

		self._combobox_group = gtk.ComboBox(self._list_group)
		self._combobox_group.connect('changed', self._ownership_changed)
		self._combobox_group.pack_start(cell_group)
		self._combobox_group.add_attribute(cell_group, 'text', 0)

		table_ownership.attach(self._combobox_group, 1, 2, 1, 2)

		# make controls insensitive if provider doesn't support them
		supported_features = self._provider.get_support()

		if Support.SET_OWNER not in supported_features:
			self._combobox_owner.set_sensitive(False)
			self._combobox_group.set_sensitive(False)

		if Support.SET_ACCESS not in supported_features:
			self._permission_owner_read.set_sensitive(False)
			self._permission_owner_write.set_sensitive(False)
			self._permission_owner_execute.set_sensitive(False)
			self._permission_group_read.set_sensitive(False)
			self._permission_group_write.set_sensitive(False)
			self._permission_group_execute.set_sensitive(False)
			self._permission_others_read.set_sensitive(False)
			self._permission_others_write.set_sensitive(False)
			self._permission_others_execute.set_sensitive(False)
			self._permission_octal_entry.set_sensitive(False)

		# pack interface
		frame_access.add(table_access)
		frame_ownership.add(table_ownership)

		tab.pack_start(frame_access, False, False, 0)
		tab.pack_start(frame_ownership, False, False, 0)

		return tab

	def _create_open_with_tab(self):
		"""Create tab containing list of applications that can open this file"""
		tab = gtk.VBox(False, 5)
		tab.set_border_width(10)

		# get item description
		description = self._application.associations_manager.get_mime_description(self._mime_type)

		# create label
		text = _(
				'Select an application to open <i>{0}</i> and '
				'other files of type "{1}"'
			).format(
				os.path.basename(self._path).replace('&', '&amp;'),
				description
			)
		label = gtk.Label(text)
		label.set_alignment(0, 0)
		label.set_line_wrap(True)
		label.set_use_markup(True)

		# create application list
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._store = gtk.ListStore(bool, str, str, str)
		self._list = gtk.TreeView()
		self._list.set_model(self._store)
		self._list.set_headers_visible(False)

		cell_radio = gtk.CellRendererToggle()
		cell_radio.set_radio(True)
		cell_radio.connect('toggled', self._change_default_application)
		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()

		# create column_name
		column_radio = gtk.TreeViewColumn()
		column_name = gtk.TreeViewColumn()

		# pack renderer
		column_radio.pack_start(cell_radio, False)
		column_name.pack_start(cell_icon, False)
		column_name.pack_start(cell_name, True)

		# configure renderer
		column_radio.add_attribute(cell_radio, 'active', Column.SELECTED)
		column_name.add_attribute(cell_icon, 'icon-name', Column.ICON_NAME)
		column_name.add_attribute(cell_name, 'text', Column.APPLICATION_NAME)

		# add column_name to the list
		self._list.append_column(column_radio)
		self._list.append_column(column_name)

		container.add(self._list)
		tab.pack_start(label, False, False, 0)
		tab.pack_start(container, True, True, 0)

		return tab

	def _create_emblems_tab(self):
		"""Create tab for editing emblems"""
		tab = gtk.VBox(False, 5)
		tab.set_border_width(10)

		# create scrollable container
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		container.set_shadow_type(gtk.SHADOW_IN)

		# create list
		self._emblems_store = gtk.ListStore(bool, str, str)
		self._emblems = gtk.TreeView(model=self._emblems_store)

		cell_selected = gtk.CellRendererToggle()
		cell_icon = gtk.CellRendererPixbuf()
		cell_name = gtk.CellRendererText()

		cell_selected.connect('toggled', self._toggle_emblem)

		column_name = gtk.TreeViewColumn()
		column_name.pack_start(cell_selected, False)
		column_name.pack_start(cell_icon, False)
		column_name.pack_start(cell_name, True)

		column_name.add_attribute(cell_selected, 'active', EmblemColumn.SELECTED)
		column_name.add_attribute(cell_icon, 'icon-name', EmblemColumn.ICON_NAME)
		column_name.add_attribute(cell_name, 'text', EmblemColumn.NAME)

		self._emblems.set_headers_visible(False)
		self._emblems.set_search_column(EmblemColumn.NAME)
		self._emblems.append_column(column_name)

		# set search function
		compare = lambda model, column, key, iter_: key.lower() not in model.get_value(iter_, column).lower()
		self._emblems.set_search_equal_func(compare)

		# get list of assigned emblems
		path, item_name = os.path.split(self._path)
		assigned_emblems = self._application.emblem_manager.get_emblems(path, item_name) or []

		# populate emblem list
		emblems = self._application.emblem_manager.get_available_emblems()

		for emblem in emblems:
			self._emblems_store.append((emblem in assigned_emblems, emblem, emblem))

		# pack user interface
		container.add(self._emblems)

		tab.pack_start(container)

		return tab

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys"""
		if event.keyval == gtk.keysyms.Escape:
			self._close_window()
