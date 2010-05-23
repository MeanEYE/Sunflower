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

		tab1 = gtk.VBox(False, 0)
		tab1_label = gtk.Label('Display')

		tab2 = gtk.VBox(False, 0)
		tab2_label = gtk.Label('Colors')

		tab3 = gtk.VBox(False, 0)
		tab3_label = gtk.Label('Plugins')

		tabs.append_page(tab1, tab1_label)
		tabs.append_page(tab2, tab2_label)
		tabs.append_page(tab3, tab3_label)

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
