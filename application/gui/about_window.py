#!/usr/bin/env python
# coding: utf-8

import os
import sys
import gtk
import pango
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

		# copyright tab
		notebook.append_page(*self._create_copyright_tab())

		# license tab
		notebook.append_page(*self._create_license_tab())

		# change log tab
		notebook.append_page(*self._create_changelog_tab())

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

	def _create_license_tab(self):
		"""Create license tab"""
		tab = gtk.ScrolledWindow()
		tab.set_border_width(5)
		tab.set_shadow_type(gtk.SHADOW_IN)
		tab.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		tab_label = gtk.Label(_('License'))

		# determine location of license file
		license_location = os.path.join('/', 'usr', 'share', 'common-licenses', 'GPL')
		if not os.path.isfile(license_location):
			license_location = os.path.join(
										os.path.dirname(sys.argv[0]),
										'application',
										'GPL.txt'
									)

		# load license file
		license_file = open(license_location, 'r')

		if license_file:
			license_text = license_file.read()
			license_file.close()

		# create license container and configure it
		font = pango.FontDescription('monospace 8')
		license_ = gtk.TextView()
		license_.set_editable(False)
		license_.set_cursor_visible(False)
		license_.modify_font(font)

		if license_text is not None:
			buffer_ = license_.get_buffer()
			buffer_.set_text(license_text)

		tab.add(license_)

		return (tab, tab_label)

	def _create_copyright_tab(self):
		"""Create license tab"""
		tab = gtk.ScrolledWindow()
		tab.set_border_width(5)
		#tab.set_shadow_type(gtk.SHADOW_IN)
		tab.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		tab_label = gtk.Label(_('Copyright'))

		# container for all the lists
		vbox = gtk.VBox(False, 10)
		vbox.set_border_width(5)

		# program copyright
		program_info = gtk.Label(_(
						'This software is being developed under GNU General '
						'Public License.\nBug reports, suggestions or questions '
		                'are more than welcome.'
						))
		program_info.set_alignment(0,0)
		program_info.set_line_wrap(True)
		program_info.connect('size-allocate', self._adjust_label)

		# developer info
		programmers = gtk.VBox(False, 0)

		label_programming = gtk.Label('<b>{0}</b>'.format(_('Programming:')))
		label_programming.set_alignment(0, 0.5)
		label_programming.set_use_markup(True)
		programmers.pack_start(label_programming, False, False, 0)

		# developers
		developer = gtk.Label('\tMeanEYE, <small><i>RCF Group</i></small>')
		developer.set_alignment(0, 0.5)
		developer.set_use_markup(True)

		programmers.pack_start(developer, False, False, 0)

		# artist info
		artists = gtk.VBox(False, 0)

		label_art = gtk.Label('<b>{0}</b>'.format(_('Artists:')))
		label_art.set_alignment(0, 0.5)
		label_art.set_use_markup(True)
		artists.pack_start(label_art, False, False, 0)

		# artists
		artist = gtk.Label('\tMrakoslava, <small><i>Studio Specttra</i></small>')
		artist.set_alignment(0, 0.5)
		artist.set_use_markup(True)

		artists.pack_start(artist, False, False, 0)

		# translators
		translators = gtk.VBox(False, 0)

		label_translating = gtk.Label('<b>{0}</b>'.format(_('Translating:')))
		label_translating.set_alignment(0, 0.5)
		label_translating.set_use_markup(True)
		translators.pack_start(label_translating, False, False, 0)

		# add translators
		label_name = gtk.Label('\tCzech\t\tRadek Tříška')
		label_name.set_alignment(0, 0.1)
		label_name.set_use_markup(True)

		translators.pack_start(label_name, False, False, 0)

		# pack interface
		vbox.pack_start(program_info, False, False, 0)
		vbox.pack_start(programmers, False, True, 0)
		vbox.pack_start(artists, False, False, 0)
		vbox.pack_start(translators, False, False, 0)

		tab.add(vbox)

		return (tab, tab_label)

	def _create_changelog_tab(self):
		"""Create change log tab"""
		tab = gtk.ScrolledWindow()
		tab.set_border_width(5)
		tab.set_shadow_type(gtk.SHADOW_IN)
		tab_label = gtk.Label(_('Change log'))

		data = ''
		changelog_location = os.path.join(os.path.dirname(sys.argv[0]), 'change.log')

		if os.path.isfile(changelog_location):
			with open(changelog_location, 'r') as file_:
				data = file_.read()

		changelog = gtk.TextView()
		changelog.set_editable(False)
		changelog.set_cursor_visible(False)

		changelog.get_buffer().set_text(data)

		tab.add(changelog)

		return (tab, tab_label)

	def _adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)

	def load_wakoopa_image(self, widget, data=None):
		"""Retrieve wakoopa statistics image"""
		file_name = urllib.urlretrieve('http://wakoopa.com/software/sunflower-py/badge.png')[0]
		self._wakoopa_image.set_from_file(file_name)
