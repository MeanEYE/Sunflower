# coding: utf-8

import os
import gtk
import pango

from collections import namedtuple


Contributor = namedtuple(
				'Contributor',
				[
					'name',  # contributor's full name
					'email',
					'website',  # contributor's website url
				])


Translator = namedtuple('Translator', Contributor._fields + ('language',))


class AboutWindow(gtk.Window):

	# list of developers
	developers = [
		Contributor(
			name = 'Mladen Mijatov',
			email = 'meaneye.rcf@gmail.com',
			website = None,
		),
		Contributor(
			name = 'Wojciech Kluczka',
			email = 'wojtekkluczka@gmail.com',
			website = None,
		),
		Contributor(
			name = 'Grigory Petrov',
			email = 'grigory.v.p@gmail.com',
			website = None,
		),
		Contributor(
			name = 'Sebastian Gaul',
			email = 'sebastian@dev.mgvmedia.com',
			website = 'http://sgaul.de',
		),
	]

	# list of artists
	artists = [
		Contributor(
			name = 'Mrakoslava',
			email = 'octogirl.design@gmail.com',
			website = None,
		),
	]

	# list of translators
	translators = [
		Translator(
			name = 'Radek Tříška',
			email = 'radek@fastlinux.eu',
			website = 'http://www.fastlinux.eu',
			language = 'Czech',
		),
		Translator(
			name = 'Jakub Dyszkiewicz',
			email = '144.kuba@gmail.com',
			website = None,
			language = 'Polish',
		),
		Translator(
			name = 'Wojciech Kluczka',
			email = 'wojtekkluczka@gmail.com',
			website = None,
			language = 'Polish',
		),
		Translator(
			name = 'Vladimir Kolev',
			email = 'vladimir.r.kolev@gmail.com',
			website = None,
			language = 'Bulgarian',
		),
		Translator(
			name = 'Keringer László',
			email = 'keringer.laszlo@gmail.com',
			website = None,
			language = 'Hungarian',
		),
		Translator(
			name = 'Sergey Malkin',
			email = 'adresatt@gmail.com',
			website = None,
			language = 'Russian',
		),
		Translator(
			name = 'Sebastian Gaul',
			email = 'sebastian@dev.mgvmedia.com',
			website = 'http://sgaul.de',
			language = 'German',
		),
		Translator(
			name = 'Damián Nohales',
			email = 'damiannohales@gmail.com',
			website = None,
			language = 'Spanish',
		),
		Translator(
			name = 'Андрій Кондратьєв',
			email = 'kondratiev.work@gmail.com',
			website = None,
			language = 'Ukrainian',
		),
		Translator(
			name = 'Халіманенко Тарас',
			email = 'mr.haltar@yandex.ru',
			website = None,
			language = 'Ukrainian',
		),
		Translator(
			name = 'Táncos Tamás',
			email = 'h868315@gmail.com',
			website = None,
			language = 'Hungarian' 
		)
	]

	# contributor table's current row
	table_row_index = -1

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

		# create tabs
		notebook.append_page(*self._create_copyright_tab())
		notebook.append_page(*self._create_license_tab())
		notebook.append_page(*self._create_changelog_tab())

		# bottom button controls
		hbox2 = gtk.HBox(False, 3)

		btn_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		btn_close.connect('clicked', self._hide)
		hbox2.pack_end(btn_close, False, False, 0)

		btn_web1 = gtk.Button('Google Code')
		btn_web1.connect('clicked', parent.goto_web, 'code.google.com/p/sunflower-fm')
		hbox2.pack_start(btn_web1, False, False, 0)

		# pack ui
		vbox.pack_start(frame, False, False, padding=0)
		vbox.pack_start(vbox2, True, True, padding=0)

		vbox2.pack_start(notebook, True, True, padding=0)
		vbox2.pack_start(hbox2, False, False, padding=0)

		self.add(vbox)

	def _show(self, widget=None, data=None):
		"""Show about dialog"""
		# update color for header label
		style = self._parent._menu_item_commands.get_style().copy()

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
		contributors = self._create_contributor_table(
			'<b>{0}</b>'.format(_('Programming:')),
			self._create_single_group(self.developers))

		# artist info
		contributors = self._add_contributors_to_table(contributors,
			'<b>{0}</b>'.format(_('Artists:')),
			self._create_single_group(self.artists))

		# translators
		contributors = self._add_contributors_to_table(contributors,
			'<b>{0}</b>'.format(_('Translating:')),
			self._create_language_groups(self.translators))

		# pack interface
		vbox.pack_start(program_info, False, False, 0)
		vbox.pack_start(contributors, False, False, 0)

		tab.add_with_viewport(vbox)

		return (tab, tab_label)

	def _create_single_group(self, contributors):
		"""Puts all contributors into a nameless group"""
		return [(None, contributors)]

	def _create_language_groups(self, contributors):
		"""Splits the list of contributors by language"""
		groups = []
		lang_dict = {}

		for contributor in contributors:
			if not contributor.language in lang_dict:
				lang_dict[contributor.language] = []

			lang_dict[contributor.language].append(contributor)

		for lang in lang_dict:
			groups.append((lang, lang_dict[lang]))

		return groups

	def _create_contributor_table(self, caption, contributors):
		"""Create a GTK table from a list of contributors"""
		table = gtk.Table(2, 3, False)
		table.set_row_spacings(5)
		table.set_col_spacings(3)

		return self._add_contributors_to_table(table, caption, contributors)

	def _add_contributors_to_table(self, table, caption, contributors):
		"""Add a list of contributors to a given table"""
		# table's caption
		row_index = self.table_row_index + 1
		label_caption = gtk.Label(caption)
		label_caption.set_alignment(0, 0)
		label_caption.set_use_markup(True)
		table.attach(label_caption, 0, 2, row_index, row_index + 1)
		# adjust spacing of the caption cell
		table.set_row_spacing(row_index, 10)
		if row_index > 0:
			table.set_row_spacing(row_index - 1, 15)
		first_group = True

		# add contributors
		for group in contributors:
			# add group language (e.g. language)
			if group[0]:
				if not first_group:
					table.attach(gtk.HSeparator(), 0, 3, row_index + 1, row_index + 2)
					row_index += 1
				first_group = False

				lang = gtk.Label('\t<i>' + group[0] + '</i>')
				lang.set_alignment(0, 0)
				lang.set_selectable(True)
				lang.set_use_markup(True)
				table.attach(lang, 0, 1, row_index + 1, row_index + 2)
				row_index += 1

			# append all contributors from group
			for contributor in group[1]:
				# set name
				label = gtk.Label('\t' + contributor.name)
				label.set_alignment(0, 0)

				# show mail as hyperlink
				email = gtk.Label('<a href="mailto:' + contributor.email + '">'
					+ contributor.email + '</a>')
				email.set_use_markup(True)
				email.set_alignment(0, 0)
				email.set_selectable(True)

				# attach name and email
				table.attach(label, 0, 1, row_index + 1, row_index + 2)
				table.attach(email, 1, 2, row_index + 1, row_index + 2)

				# attach hyperlink if web page is given
				if contributor.website:
					web = gtk.Label('<a href="' + contributor.website
						+ '" title="' + contributor.website + '">WWW</a>')
					web.set_use_markup(True)
					table.attach(web, 2, 3, row_index + 1, row_index + 2)

				row_index += 1

		# store current row_index for upcoming method calls
		self.table_row_index = row_index

		return table

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
			license_location = os.path.abspath('COPYING')

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
		changelog_location = os.path.abspath('CHANGES')

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

