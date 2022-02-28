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
		self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)

		self.window.set_title(_('Advanced rename'))
		self.window.set_default_size(640, 600)
		self.window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self.window.set_transient_for(application)
		self.window.set_border_width(7)
		self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
		self.window.set_modal(True)
		self.window.set_wmclass('Sunflower', 'Sunflower')

		self.window.connect('key-press-event', self._handle_key_press)

		# create interface
		vbox = Gtk.VBox(False, 7)

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
		container.set_shadow_type(Gtk.ShadowType.IN)

		# create location
		vbox_location = Gtk.VBox(False, 0)

		label_location = Gtk.Label(label=_('Items located in:'))
		label_location.set_alignment(0, 0.5)

		entry_location = Gtk.Entry()
		entry_location.set_text(self._path)
		entry_location.set_editable(False)

		# create controls
		hbox = Gtk.HBox(False, 5)

		button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
		button_close.connect('clicked', lambda widget: self.window.destroy())

		image_rename = Gtk.Image()
		image_rename.set_from_icon_name('edit-find-replace', Gtk.IconSize.BUTTON)
		button_rename = Gtk.Button(label=_('Rename'))
		button_rename.set_image(image_rename)
		button_rename.connect('clicked', self.rename_files)

		# pack interface
		vbox_location.pack_start(label_location, False, False, 0)
		vbox_location.pack_start(entry_location, False, False, 0)

		hbox.pack_end(button_rename, False, False, 0)
		hbox.pack_end(button_close, False, False, 0)

		container.add(self._names)

		vbox.pack_start(self._extension_list, False, False, 0)
		vbox.pack_end(hbox, False, False, 0)
		vbox.pack_end(vbox_location, False, False, 0)
		vbox.pack_end(container, True, True, 0)

		self.window.add(vbox)

		# prepare UI
		self.__create_extensions()
		self.__populate_list()

		# update list initially
		self.update_list()

		# show all widgets
		self.window.show_all()

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
		"""Handle pressing keys"""
		if event.keyval == Gdk.KEY_Escape:
			self.window.destroy()

	def update_list(self):
		"""Update file list"""
		active_children = [child for child in self._extension_list.get_children()
						   if child.extension.is_active()]

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
								self.window,
								Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.QUESTION,
								Gtk.ButtonsType.YES_NO,
								ngettext(
									"You are about to rename {0} item.\n"
									"Are you sure about this?",
									"You are about to rename {0} items.\n"
									"Are you sure about this?",
									len(self._list)
								).format(len(self._list))
							)
		dialog.set_default_response(Gtk.ResponseType.YES)
		result = dialog.run()
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
