import os
import gtk

from parameters import Parameters


class Column:
	NAME = 0
	PATH = 1
	TIMESTAMP = 2


class HistoryList(gtk.Window):
	"""History list is used to display complete browsing history."""

	def __init__(self, parent, application):
		# create main window
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		# store parameters locally, we'll need them later
		self._parent = parent
		self._application = application

		# configure dialog
		self.set_title(_('History'))
		self.set_size_request(500, 300)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_resizable(True)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(application)
		self.set_wmclass('Sunflower', 'Sunflower')
		self.set_border_width(7)

		# create UI
		vbox = gtk.VBox(False, 7)

		list_container = gtk.ScrolledWindow()
		list_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		list_container.set_shadow_type(gtk.SHADOW_IN)

		self._history = gtk.ListStore(str, str)

		cell_name = gtk.CellRendererText()
		cell_path = gtk.CellRendererText()

		col_name = gtk.TreeViewColumn(_('Name'), cell_name, text=Column.NAME)
		col_path = gtk.TreeViewColumn(_('Path'), cell_path, text=Column.PATH)

		self._history_list = gtk.TreeView(self._history)
		self._history_list.connect('key-press-event', self._handle_key_press)
		self._history_list.append_column(col_name)
		self._history_list.append_column(col_path)

		# create controls
		hbox_controls = gtk.HBox(False, 5)

		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._close)

		image_jump = gtk.Image()
		image_jump.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
		button_jump = gtk.Button()
		button_jump.set_image(image_jump)
		button_jump.set_label(_('Open'))
		button_jump.set_can_default(True)
		button_jump.connect('clicked', self._change_path, False)

		image_new_tab = gtk.Image()
		image_new_tab.set_from_icon_name('tab-new', gtk.ICON_SIZE_BUTTON)

		button_new_tab = gtk.Button()
		button_new_tab.set_image(image_new_tab)
		button_new_tab.set_label(_('Open in tab'))
		button_new_tab.set_tooltip_text(_('Open selected path in new tab'))
		button_new_tab.connect('clicked', self._change_path, True)

		button_opposite = gtk.Button(label=_('Open in opposite list'))
		button_opposite.set_tooltip_text(_('Open selected path in opposite list'))
		button_opposite.connect('clicked', self._open_in_opposite_list)

		# pack UI
		list_container.add(self._history_list)

		hbox_controls.pack_end(button_close, False, False, 0)
		hbox_controls.pack_end(button_jump, False, False, 0)
		hbox_controls.pack_end(button_new_tab, False, False, 0)
		hbox_controls.pack_end(button_opposite, False, False, 0)

		vbox.pack_start(list_container, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)

		self.add(vbox)

		# populate history list
		self._populate_list()

		# show all elements
		self.show_all()

	def _close(self, widget=None, data=None):
		"""Handle clicking on close button"""
		self.destroy()

	def _change_path(self, widget=None, new_tab=False):
		"""Change to selected path"""
		selection = self._history_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# if selection is valid, change to selected path
		if selected_iter is not None:
			path = item_list.get_value(selected_iter, Column.PATH)

			if not new_tab:
				# change path
				self._parent._handle_history_click(path=path)

			else:
				# create a new tab
				options = Parameters()
				options.set('path', path)

				self._application.create_tab(
								self._parent._notebook,
								self._parent.__class__,
								options
							)

			# close dialog
			self._close()

	def _open_in_opposite_list(self, widget=None, data=None):
		"""Open selected item in opposite list"""
		selection = self._history_list.get_selection()
		item_list, selected_iter = selection.get_selected()

		# if selection is valid, change to selected path
		if selected_iter is not None:
			path = item_list.get_value(selected_iter, Column.PATH)

			# open in opposite list
			opposite_object = self._application.get_opposite_object(self._application.get_active_object())
			if hasattr(opposite_object, 'change_path'):
				opposite_object.change_path(path)

			# close dialog
			self._close()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in history list"""
		result = False

		if event.keyval == gtk.keysyms.Return:
			if event.state & gtk.gdk.CONTROL_MASK:
				# open path in new tab
				self._change_path(new_tab=True)

			else:
				# open path in existing tab
				self._change_path(new_tab=False)

			result = True

		elif event.keyval == gtk.keysyms.Escape:
			# close window on escape
			self._close()
			result = True

		return result

	def _populate_list(self):
		"""Populate history list"""
		target_iter = None
		current_path = self._parent._options.get('path')

		# add all entries to the list
		for path in self._parent.history:
			name = os.path.basename(path)
			if name == '':
				name = path

			new_iter = self._history.append((name, path))

			# assign row to be selected
			if target_iter is None or path == current_path:
				target_iter = new_iter

		# select row
		path = self._history.get_path(target_iter)
		self._history_list.set_cursor(path)
