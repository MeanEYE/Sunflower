#!/usr/bin/env python

import sys
import os
import gtk
import urllib

class AboutWindow(gtk.Window):
	def __init__(self, parent):
		# create main window
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.connect('delete_event', self._hide)
		self.set_title(_('About program'))
		self.set_size_request(550, 350)
		self.set_resizable(False)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(parent)
		self.realize()

		# create gui
		vbox = gtk.VBox(False, 0)

		# program logo
		image_file = os.path.join(
								os.path.dirname(sys.argv[0]),
								'images',
								'sunflower_hi-def_64x64.png'
							)
		image = gtk.Image()
		image.set_from_file(image_file)
		image.set_size_request(70, 70)

		# program label
		style = self.get_style().copy()
		program_label = gtk.Label(
							'<span color="{0}">'
							'<span size="x-large" weight="bold">'
							'{2}</span>\n{3} {1[major]}.{1[minor]}{1[stage]} '
							'<span size="small"><i>({1[build]})</i></span>'
							'</span>'.format(
										style.fg[gtk.STATE_SELECTED].to_string(),
										parent.version,
										_('Sunflower'),
										_('Version')
									)
							)
		program_label.set_use_markup(True)

		# top horizontal box containing image and program title
		frame = gtk.EventBox()
		frame.modify_bg(gtk.STATE_NORMAL, style.bg[gtk.STATE_SELECTED])

		hbox1 = gtk.HBox(False, 0)
		frame.add(hbox1)

		hbox1.pack_start(image, False, False, 0)
		hbox1.pack_start(program_label, False, False, 5)

		# bottom vbox
		vbox2 = gtk.VBox(False, 5)
		vbox2.set_border_width(10)

		# middle content
		notebook = gtk.Notebook()

		tab1 = gtk.VBox(False, 10)
		tab1.set_border_width(10)

		program_info = gtk.Label(_(
						'This software is being developed under GNU general '
						'public license. If you would like to obtain source code '
						'please visit our web site. Any bug reports, suggestions '
						'or questions are more than welcome.'
						))
		program_info.set_alignment(0,0)
		program_info.set_line_wrap(True)
		program_info.connect('size-allocate', self._adjust_label)
		tab1.pack_start(program_info, False, True, 0)

		developer_info = gtk.Label(
							'<b>' + _('Developer') + '</b>\n\tMeanEYE, <i>'
							'<span size="small">RCF Group</span></i>'
							)
		developer_info.set_use_markup(True)
		developer_info.set_alignment(0,0)
		tab1.pack_start(developer_info, False, True, 0)

		artist_info = gtk.Label(
							'<b>' + _('Artist') + '</b>\n\tMrakoslava, <i>'
							'<span size="small">Studio Spectra</span></i>'
							)
		artist_info.set_use_markup(True)
		artist_info.set_alignment(0,0)
		tab1.pack_start(artist_info, False, True, 0)

		tab1_label = gtk.Label(_('Copyright'))
		notebook.append_page(tab1, tab1_label)

		# license tab
		tab2 = gtk.ScrolledWindow()
		tab2.set_border_width(5)
		tab2.set_shadow_type(gtk.SHADOW_IN)

		license_location = os.path.join('/', 'usr', 'share', 'common-licenses', 'GPL')
		if not os.path.isfile(license_location):
			license_location = os.path.join(
										os.path.dirname(sys.argv[0]),
										'application',
										'GPL.txt'
									)

		license_file = open(license_location, 'r')

		if license_file:
			license_text = license_file.read()
			license_file.close()

		license = gtk.TextView()
		license.set_editable(False)
		license.set_cursor_visible(False)

		if license_text is not None:
			buffer_ = license.get_buffer()
			buffer_.set_text(license_text)

		tab2.add(license)

		tab2_label = gtk.Label(_('License'))
		notebook.append_page(tab2, tab2_label)

		# create statistics tab
		notebook.append_page(*self._create_statistics_tab())

		# bottom button controls
		hbox2 = gtk.HBox(False, 3)

		btn_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		btn_close.connect('clicked', self._hide)
		hbox2.pack_end(btn_close, False, False, 0)

		btn_web1 = gtk.Button('RCF Group')
		btn_web1.connect('clicked', parent.goto_web, 'rcf-group.com')
		hbox2.pack_start(btn_web1, False, False, 0)

		btn_web2 = gtk.Button('Google Code')
		btn_web2.connect('clicked', parent.goto_web, 'code.google.com/p/sunflower-fm')
		hbox2.pack_start(btn_web2, False, False, 0)

		# pack ui
		vbox.pack_start(frame, False, False, padding=0)
		vbox.pack_start(vbox2, True, True, padding=0)

		vbox2.pack_start(notebook, True, True, padding=0)
		vbox2.pack_start(hbox2, False, False, padding=0)

		self.add(vbox)

	def _show(self, widget, data=None):
		self.show_all()

	def _hide(self, widget, data=None):
		self.hide()
		return True  # return True so we get to keep our controls safe from GC

	def _create_statistics_tab(self):
		"""Create tab for all the promotional sites"""
		tab = gtk.Notebook()
		tab.set_tab_pos(gtk.POS_RIGHT)
		tab.set_border_width(5)
		tab_label = gtk.Label(_('Statistics'))

		# wakoopa statistics
		tab_wakoopa = gtk.VBox(False, 5)
		tab_wakoopa.set_border_width(10);

		warning = gtk.Label('In order to avoid slow program starting and '
			'unnecessary bandwidth usage, automatic <b>Wakoopa</b> statistics loading '
			'has been disabled. Please click on <i>load</i> button to retrieve data. ')
		warning.set_use_markup(True)
		warning.set_line_wrap(True)
		warning.set_alignment(0,0)
		warning.connect('size-allocate', self._adjust_label)

		self._wakoopa_image = gtk.Image()

		hbox3 = gtk.HBox(False, 0)
		load_button = gtk.Button('Load');
		load_button.connect('clicked', self.load_wakoopa_image)

		hbox3.pack_end(load_button, False, True, 0)

		tab_wakoopa.pack_start(warning, False, True, 0)
		tab_wakoopa.pack_start(self._wakoopa_image, False, True, 0)
		tab_wakoopa.pack_end(hbox3, False, True, 0)

		image_wakoopa = gtk.Image()
		image_wakoopa.set_from_file(
								os.path.join(
									os.path.dirname(sys.argv[0]),
									'images',
									'wakoopa.png'
								))
		tab.append_page(tab_wakoopa, image_wakoopa)

		# alternative to
		tab_alternativeto = gtk.VBox(False, 5)
		tab_alternativeto.set_border_width(10)

		image_alternativeto = gtk.Image()
		image_alternativeto.set_from_file(
								os.path.join(
									os.path.dirname(sys.argv[0]),
									'images',
									'alternativeto.png'
								))
		tab.append_page(tab_alternativeto, image_alternativeto)

		return (tab, tab_label)

	def _adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)

	def load_wakoopa_image(self, widget, data=None):
		"""Retrieve wakoopa statistics image"""
		file_name = urllib.urlretrieve('http://wakoopa.com/software/sunflower-py/badge.png')[0]
		self._wakoopa_image.set_from_file(file_name)
