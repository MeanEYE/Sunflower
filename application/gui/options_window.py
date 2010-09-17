#!/usr/bin/env python

import gtk

class OptionsWindow(gtk.Window):

	def __init__(self, parent):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.connect('delete_event', self._hide)
		self.set_title('Options')
		self.set_size_request(600, 450)
		self.set_modal(True)
		self.set_skip_taskbar_hint(True)
		self.set_deletable(False)

		# create gui
		vbox = gtk.VBox(False, 5)
		vbox.set_border_width(5)

		# create tabs
		tabs = gtk.Notebook()
		tabs.set_tab_pos(gtk.POS_LEFT)

		tabs.append_page(
					DisplayOptions(),
					gtk.Label('Display')
					)
		tabs.append_page(
					ToolbarOptions(),
					gtk.Label('Toolbar')
					)
		tabs.append_page(
					BookmarkOptions(),
					gtk.Label('Bookmarks')
					)

		# create buttons
		hbox = gtk.HBox(False, 2)

		btn_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		btn_close.connect('clicked', self._hide)
		hbox.pack_end(btn_close, False, False, 0)

		# pack gui
		vbox.pack_start(tabs, True, True, 0)
		vbox.pack_start(hbox, False, False, 0)

		self.add(vbox)

	def _show(self, widget, data=None):
		self.show_all()

	def _hide(self, widget, data=None):
		self.hide()
		return True  # avoid destroying components
	
	
class DisplayOptions(gtk.VBox):
	"""Display options extension class"""
	
	def __init__(self):
		gtk.VBox.__init__(self, False, False)
		

class ToolbarOptions(gtk.VBox):
	"""Toolbar options extension class"""
	
	def __init__(self):
		gtk.VBox.__init__(self, False, 0)
		
		# configure self
		self.set_border_width(5)
		self.set_spacing(5)
		
		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)
		
		self._list = gtk.TreeView()
		container.add(self._list)
		
		# create controls
		button_box = gtk.HButtonBox()
		button_box.set_layout(gtk.BUTTONBOX_START)
		
		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		
		button_move_up = gtk.Button('Move Up')
		button_move_down = gtk.Button('Move Down')
		
		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_start(button_move_up, False, False, 0)
		button_box.pack_start(button_move_down, False, False, 0)
		
		button_box.set_child_secondary(button_move_up, True)
		button_box.set_child_secondary(button_move_down, True)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

		
class BookmarkOptions(gtk.VBox):
	"""Bookmark options extension class"""
	
	def __init__(self):
		gtk.VBox.__init__(self, False, 0)
		
		# configure self
		self.set_border_width(5)
		self.set_spacing(5)
		
		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._bookmarks = gtk.ListStore(str, str)
		
		self._list = gtk.TreeView()
		self._list.set_model(self._bookmarks)
		self._list.set_rules_hint(True)

		cell_title = gtk.CellRendererText()
		cell_title.set_property('editable', True)
		cell_title.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_title.connect('edited', self._edited_bookmark, 0)
		
		cell_command = gtk.CellRendererText()
		cell_command.set_property('editable', True)
		cell_command.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
		cell_command.connect('edited', self._edited_bookmark, 1)

		col_title = gtk.TreeViewColumn('Title', cell_title, text=0)
		col_title.set_min_width(200)
		col_title.set_resizable(True)
		
		col_command = gtk.TreeViewColumn('Command', cell_command, text=1)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)
		
		container.add(self._list)
		
		# create controls
		button_box = gtk.HButtonBox()
		button_box.set_layout(gtk.BUTTONBOX_START)
		
		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self._add_bookmark)
		
		button_delete = gtk.Button(stock=gtk.STOCK_DELETE)
		
		button_move_up = gtk.Button('Move Up')
		button_move_down = gtk.Button('Move Down')
		
		# pack ui
		button_box.pack_start(button_add, False, False, 0)
		button_box.pack_start(button_delete, False, False, 0)
		button_box.pack_start(button_move_up, False, False, 0)
		button_box.pack_start(button_move_down, False, False, 0)
		
		button_box.set_child_secondary(button_move_up, True)
		button_box.set_child_secondary(button_move_down, True)

		self.pack_start(container, True, True, 0)
		self.pack_start(button_box, False, False, 0)

	def _add_bookmark(self, widget, data=None):
		"""Add new bookmark to the store"""
		
		if data is None:
			data = ('New bookmark', '')
			
		self._bookmarks.append(data)
		
	def _edited_bookmark(self, cell, path, text, column):
		"""Record edited text"""
		iter = self._bookmarks.get_iter(path)
		self._bookmarks.set_value(iter, column, text)

	def _delete_bookmark(self, widget, data=None):
		"""Remove selected field from store"""
		selection = self._list.get_selection()
		list, iter = selection.get_selected()

		if iter is not None:
			list.remove(iter)