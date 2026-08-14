from __future__ import absolute_import

import os

from gi.repository import Gtk, Gdk
from sunflower.operation import RenameOperation


class Column:
	ICON = 0
	OLD_NAME = 1
	NEW_NAME = 2


class AdvancedRename:
	"""Advanced rename tool"""

	def __init__(self, parent, application):
		# store parameters
		self._parent = parent
		self._provider = self._parent.get_provider()
		self._application = application
		self._extensions = []
		self._path = self._parent.path

		# create and configure window
		if Gtk.get_major_version() == 3:
			self.window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
		else:
			self.window = Gtk.Window.new()

		self.window.set_title(_('Advanced rename'))
		self.window.set_default_size(640, 600)
		self.window.set_transient_for(application)
		if Gtk.get_major_version() == 3:
			self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
		self.window.set_modal(True)

		if Gtk.get_major_version() == 3:
			self.window.connect('key-press-event', self._handle_key_press)

		else:
			key_controller = Gtk.EventControllerKey.new()
			key_controller.connect('key-pressed', self._handle_key_pressed)
			self.window.add_controller(key_controller)
		# create interface
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
		set_border_width(vbox, 7)

		# create modifiers notebook
		self._extension_list = Gtk.Notebook()
		self._extension_list.connect('page-reordered', self.__handle_reorder)

		# create list
		self._list = Gtk.ListStore(str, str, str)
		self._names = Gtk.TreeView(model=self._list)

		cell_icon = Gtk.CellRendererPixbuf()
		cell_old_name = Gtk.CellRendererText()
		cell_new_name = Gtk.CellRendererText()

		col_old_name = Gtk.TreeViewColumn(_('Old name'))
		col_old_name.set_expand(True)

		col_new_name = Gtk.TreeViewColumn(_('New name'))
		col_new_name.set_expand(True)

		# pack renderer
		col_old_name.pack_start(cell_icon, False)
		col_old_name.pack_start(cell_old_name, True)
		col_new_name.pack_start(cell_new_name, True)

		# connect renderer attributes
		col_old_name.add_attribute(cell_icon, 'icon-name', Column.ICON)
		col_old_name.add_attribute(cell_old_name, 'text', Column.OLD_NAME)
		col_new_name.add_attribute(cell_new_name, 'text', Column.NEW_NAME)

		self._names.append_column(col_old_name)
		self._names.append_column(col_new_name)

		container = Gtk.ScrolledWindow()
		container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		if Gtk.get_major_version() == 3:
			container.set_shadow_type(Gtk.ShadowType.IN)

		else:
			container.set_has_frame(True)

		# create location
		vbox_location = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_location = Gtk.Label(label=_('Items located in:'))
		label_location.set_xalign(0)
		label_location.set_yalign(0.5)

		entry_location = Gtk.Entry()
		entry_location.set_text(self._path)
		entry_location.set_editable(False)

		# create controls
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

		if Gtk.get_major_version() == 3:
			button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)

		else:
			button_close = Gtk.Button.new_with_label(_('Close'))
		button_close.connect('clicked', lambda widget: self.window.destroy())

		image_rename = Gtk.Image()
		if Gtk.get_major_version() == 3:
			image_rename.set_from_icon_name('edit-find-replace', Gtk.IconSize.BUTTON)

		else:
			image_rename.set_from_icon_name('edit-find-replace')
		button_rename = Gtk.Button(label=_('Rename'))
		if Gtk.get_major_version() == 3:
			button_rename.set_image(image_rename)

		else:
			button_rename.set_child(image_rename)
		button_rename.connect('clicked', self.rename_files)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_location.pack_start(label_location, False, False, 0)
			vbox_location.pack_start(entry_location, False, False, 0)

			hbox.pack_end(button_rename, False, False, 0)
			hbox.pack_end(button_close, False, False, 0)

		else:
			vbox_location.append(label_location)
			vbox_location.append(entry_location)

			# end packed children are shown in reverse order of addition
			button_close.set_hexpand(True)
			button_close.set_halign(Gtk.Align.END)
			hbox.append(button_close)
			hbox.append(button_rename)

		if Gtk.get_major_version() == 3:
			container.add(self._names)

		else:
			container.set_child(self._names)

		if Gtk.get_major_version() == 3:
			vbox.pack_start(self._extension_list, False, False, 0)
			vbox.pack_end(hbox, False, False, 0)
			vbox.pack_end(vbox_location, False, False, 0)
			vbox.pack_end(container, True, True, 0)

		else:
			vbox.append(self._extension_list)

			# end packed children are shown in reverse order of addition
			container.set_vexpand(True)
			vbox.append(container)
			vbox.append(vbox_location)
			vbox.append(hbox)

		if Gtk.get_major_version() == 3:
			self.window.add(vbox)

		else:
			self.window.set_child(vbox)

		# prepare UI
		self.__create_extensions()
		self.__populate_list()

		# update list initially
		self.update_list()

		# show all widgets
		if Gtk.get_major_version() == 3:
			self.window.show_all()

		else:
			self.window.show()

	def __create_extensions(self):
		"""Create rename extensions"""
		for ExtensionClass in self._application.rename_extension_classes.values():
			extension = ExtensionClass(self)
			title = extension.get_title()
			container = extension.get_container()

			# add tab
			self._extension_list.append_page(container, Gtk.Label(label=title))
			self._extension_list.set_tab_reorderable(container, True)

			# store extension for later use
			self._extensions.append(extension)

	def __populate_list(self):
		"""Populate list with data from parent"""
		parent_list = self._parent._get_selection_list()

		if parent_list is None:
			return

		# clear selection on source directory
		if self._path == self._parent.path:
			self._parent.deselect_all()

		# clear items
		self._list.clear()

		# add all the items from the list
		for item in parent_list:
			name = os.path.basename(item)

			if self._provider.is_file(item):
				icon = self._application.icon_manager.get_icon_for_file(item)

			else:
				icon = self._application.icon_manager.get_icon_for_directory(item)

			self._list.append((icon, name, ''))

	def __handle_reorder(self, notebook, child, page_number, data=None):
		"""Handle extension reordering"""
		self.update_list()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys (GTK 3)"""
		return self._handle_keyval(event.keyval, event.get_state())

	def _handle_key_pressed(self, controller, keyval, keycode, state):
		"""Handle pressing keys (GTK 4)"""
		return self._handle_keyval(keyval, state)

	def _handle_keyval(self, keyval, state):
		"""Handle pressing keys"""
		if keyval == Gdk.KEY_Escape:
			self.window.destroy()

	def update_list(self):
		"""Update file list"""
		children = [self._extension_list.get_nth_page(number)
					for number in range(self._extension_list.get_n_pages())]
		active_children = [child for child in children if child.extension.is_active()]

		for child in active_children:
			# call reset on all extensions
			child.extension.reset()

		for row in self._list:
			old_name = row[Column.OLD_NAME]
			new_name = old_name

			# run new name through extensions
			for child in active_children:
				new_name = child.extension.get_new_name(old_name, new_name)

			# store new name to list
			row[Column.NEW_NAME] = new_name

	def rename_files(self, widget=None, data=None):
		"""Rename selected files"""
		dialog = Gtk.MessageDialog(
								transient_for=self.window,
								destroy_with_parent=True,
								message_type=Gtk.MessageType.QUESTION,
								buttons=Gtk.ButtonsType.YES_NO,
								text=ngettext(
									"You are about to rename {0} item.\n"
									"Are you sure about this?",
									"You are about to rename {0} items.\n"
									"Are you sure about this?",
									len(self._list)
								).format(len(self._list))
							)
		dialog.set_default_response(Gtk.ResponseType.YES)
		result = run_dialog(dialog)
		dialog.destroy()

		if result == Gtk.ResponseType.YES:
			# user confirmed rename
			item_list = []
			for item in self._list:
				item_list.append((item[Column.OLD_NAME], item[Column.NEW_NAME]))

			# create thread and start operation
			operation = RenameOperation(
									self._application,
									self._provider,
									self._path,
									item_list
								)

			# set event queue
			event_queue = self._parent.get_monitor_queue()
			if event_queue is not None:
				operation.set_source_queue(event_queue)

			operation.start()
