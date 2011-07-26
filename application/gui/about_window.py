# coding: utf-8

import os
import gtk
import pango

class AboutWindow(gtk.Window):

	def __init__(self, parent):
		# create main window
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		# store parent locally, we'll need it later
		self._parent = parent

		# configure dialog
		self.set_title(_('About program'))
		self.set_size_request(550, 450)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_resizable(False)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(parent)
		self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.set_wmclass('Sunflower', 'Sunflower')

		# connect signals
		self.connect('delete_event', self._hide)

		# create gui
		vbox = gtk.VBox(False, 0)

		# program logo
		image_file = os.path.abspath(os.path.join(
								'images',
								'sunflower_64.png'
							))
		image = gtk.Image()
		image.set_from_file(image_file)
		image.set_size_request(70, 70)

		# program label
		self._program_label = gtk.Label(
							'<span size="x-large" weight="bold">{1}</span>\n'
		                    '{2} {0[major]}.{0[minor]}{0[stage]} '
							'<span size="small"><i>({0[build]})</i>'
							'</span>'.format(
										parent.version,
										_('Sunflower'),
										_('Version')
									)
							)
		self._program_label.set_use_markup(True)
		self._program_label.set_alignment(0, 0.5)

		# top horizontal box containing image and program title
		hbox1 = gtk.HBox(False, 0)
		hbox1.set_border_width(5)

		hbox1.pack_start(image, False, False, 0)
		hbox1.pack_start(self._program_label, True, True, 5)

		frame = gtk.EventBox()
		frame.add(hbox1)

		# bottom vbox
		vbox2 = gtk.VBox(False, 7)
		vbox2.set_border_width(7)

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

	def _show(self, widget=None, data=None):
		"""Show about dialog"""
		# update color for header label
		style = self._parent._menu_item_tools.get_style().copy()

		label = self._program_label
		parent = self._program_label.get_parent().get_parent()

		label.modify_fg(gtk.STATE_NORMAL, style.fg[gtk.STATE_NORMAL])
		parent.modify_bg(gtk.STATE_NORMAL, style.bg[gtk.STATE_NORMAL])

		# show all widgets and dialog
		self.show_all()

	def _hide(self, widget, data=None):
		"""Hide about dialog"""
		self.destroy()

	def _create_copyright_tab(self):
		"""Create license tab"""
		tab = gtk.ScrolledWindow()
		tab.set_border_width(5)
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
		programmers = gtk.Table(2, 2, False)
		programmers.set_row_spacings(7)
		programmers.set_row_spacing(0, 3)

		label_programming = gtk.Label('<b>{0}</b>'.format(_('Programming:')))
		label_programming.set_alignment(0, 0)
		label_programming.set_use_markup(True)

		programmers.attach(label_programming, 0, 2, 0, 1)

		# developers
		developer = gtk.Label('\tMeanEYE')
		developer.set_alignment(0, 0)
		developer.set_selectable(True)

		email = gtk.Label('meaneye.rcf@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		programmers.attach(developer, 0, 1, 1, 2)
		programmers.attach(email, 1, 2, 1, 2)

		developer = gtk.Label('\tWojciech Kluczka')
		developer.set_alignment(0, 0)
		developer.set_selectable(True)

		email = gtk.Label('wojtekkluczka@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		programmers.attach(developer, 0, 1, 2, 3)
		programmers.attach(email, 1, 2, 2, 3)

		# artist info
		artists = gtk.Table(1, 2, False)
		artists.set_row_spacings(7)
		artists.set_row_spacing(0, 3)

		label_art = gtk.Label('<b>{0}</b>'.format(_('Artists:')))
		label_art.set_alignment(0, 0)
		label_art.set_use_markup(True)

		artists.attach(label_art, 0, 2, 0, 1)

		# artists
		artist = gtk.Label('\tMrakoslava')
		artist.set_alignment(0, 0)
		artist.set_selectable(True)

		email = gtk.Label('octogirl.design@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		artists.attach(artist, 0, 1, 1, 2)
		artists.attach(email, 1, 2, 1, 2)

		# translators
		translators = gtk.Table(2, 3, False)
		translators.set_row_spacings(7)
		translators.set_row_spacing(0, 3)

		label_translating = gtk.Label('<b>{0}</b>'.format(_('Translating:')))
		label_translating.set_alignment(0, 0)
		label_translating.set_use_markup(True)
		translators.attach(label_translating, 0, 3, 0, 1)

		# add translators
		translator = gtk.Label('\tRadek Tříška')
		translator.set_alignment(0, 0)
		translator.set_selectable(True)

		email = gtk.Label(
		                'radek@fastlinux.eu\n'
						'www.fastlinux.eu'
					)
		email.set_alignment(0, 0)
		email.set_selectable(True)

		language = gtk.Label('Czech language')
		language.set_alignment(0, 0)

		translators.attach(translator, 0, 1, 1, 2)
		translators.attach(email, 1, 2, 1, 2)
		translators.attach(language, 2, 3, 1, 2)

		# Polish
		translator = gtk.Label('\tJakub Dyszkiewicz')
		translator.set_alignment(0, 0)
		translator.set_selectable(True)

		email = gtk.Label('144.kuba@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		language = gtk.Label('Polish language')
		language.set_alignment(0, 0)

		translators.attach(translator, 0, 1, 2, 3)
		translators.attach(email, 1, 2, 2, 3)
		translators.attach(language, 2, 3, 2, 3)

		translator = gtk.Label('\tWojciech Kluczka')
		translator.set_alignment(0, 0)
		translator.set_selectable(True)

		email = gtk.Label('wojtekkluczka@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		translators.attach(translator, 0, 1, 3, 4)
		translators.attach(email, 1, 2, 3, 4)
		translators.set_row_spacing(2, 0)

		# Bulgarian
		translator = gtk.Label('\tVladimir Kolev')
		translator.set_alignment(0, 0)
		translator.set_selectable(True)

		email = gtk.Label('vladimir.r.kolev@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		language = gtk.Label('Bulgarian language')
		language.set_alignment(0, 0)

		translators.attach(translator, 0, 1, 4, 5)
		translators.attach(email, 1, 2, 4, 5)
		translators.attach(language, 2, 3, 4, 5)

		# Hungarian
		translator = gtk.Label('\tKeringer László')
		translator.set_alignment(0, 0)
		translator.set_selectable(True)

		email = gtk.Label('keringer.laszlo@gmail.com')
		email.set_alignment(0, 0)
		email.set_selectable(True)

		language = gtk.Label('Hungarian language')
		language.set_alignment(0, 0)

		translators.attach(translator, 0, 1, 5, 6)
		translators.attach(email, 1, 2, 5, 6)
		translators.attach(language, 2, 3, 5, 6)

		# separators
		separator1 = gtk.HSeparator()
		separator2 = gtk.HSeparator()

		# pack interface
		vbox.pack_start(program_info, False, False, 0)
		vbox.pack_start(programmers, False, False, 0)
		vbox.pack_start(separator1, False, False, 0)
		vbox.pack_start(artists, False, False, 0)
		vbox.pack_start(separator2, False, False, 0)
		vbox.pack_start(translators, False, False, 0)

		tab.add_with_viewport(vbox)

		return (tab, tab_label)

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
			license_location = os.path.abspath(os.path.join('docs', 'license'))

		# load license file
		license_file = open(license_location, 'r')

		if license_file:
			license_text = license_file.read()
			license_file.close()

		# create license container and configure it
		font = pango.FontDescription('monospace 9')
		license_ = gtk.TextView()
		license_.set_editable(False)
		license_.set_cursor_visible(False)
		license_.modify_font(font)

		if license_text is not None:
			buffer_ = license_.get_buffer()
			buffer_.set_text(license_text)

		tab.add(license_)

		return (tab, tab_label)

	def _create_changelog_tab(self):
		"""Create change log tab"""
		tab = gtk.ScrolledWindow()
		tab.set_border_width(5)
		tab.set_shadow_type(gtk.SHADOW_IN)
		tab.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
		tab_label = gtk.Label(_('Change log'))

		data = ''
		changelog_location = os.path.abspath('change.log')

		if os.path.isfile(changelog_location):
			with open(changelog_location, 'r') as file_:
				data = file_.read()

		font = pango.FontDescription('monospace 9')
		changelog = gtk.TextView()
		changelog.set_editable(False)
		changelog.set_cursor_visible(False)
		changelog.set_wrap_mode(gtk.WRAP_WORD)
		changelog.modify_font(font)

		changelog.get_buffer().set_text(data)

		tab.add(changelog)

		return (tab, tab_label)

	def _adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)

