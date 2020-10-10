from __future__ import absolute_import

from gi.repository import Gtk, Gdk, GObject
from urllib.request import urlopen
from json import JSONDecoder
from threading import Thread


class VersionCheck:
	"""Small class used for checking and displaying current and
	latest version of software detected by getting a file from
	project hosting site.

	"""

	URL = 'https://api.github.com/repos/MeanEYE/Sunflower/releases'

	def __init__(self, application):
		self._dialog = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
		self._application = application

		# configure window
		self._dialog.set_title(_('Version check'))
		self._dialog.set_border_width(7)
		self._dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self._dialog.set_resizable(False)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)
		self._dialog.set_type_hint(Gdk.WindowTypeHint.DIALOG)
		self._dialog.connect('key-press-event', self._handle_key_press)

		# create user interface
		vbox = Gtk.VBox(False, 5)
		hbox = Gtk.HBox(False, 0)
		table = Gtk.Table(2, 2)

		table.set_row_spacings(5)
		table.set_col_spacings(5)

		label_current = Gtk.Label(label=_('Current:'))
		label_current.set_alignment(0, 0.5)

		label_latest = Gtk.Label(label=_('Latest:'))
		label_latest.set_alignment(0, 0.5)

		self._entry_current = Gtk.Entry()
		self._entry_current.set_editable(False)

		self._entry_latest = Gtk.Entry()
		self._entry_latest.set_editable(False)

		separator = Gtk.HSeparator()

		# create controls
		button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
		button_close.connect('clicked', lambda widget: self._dialog.hide())

		# pack user interface
		self._dialog.add(vbox)

		vbox.pack_start(table, True, True, 0)
		vbox.pack_start(separator, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)

		hbox.pack_end(button_close, False, False, 0)

		table.attach(label_current, 0, 1, 0, 1)
		table.attach(label_latest, 0, 1, 1, 2)
		table.attach(self._entry_current, 1, 2, 0, 1)
		table.attach(self._entry_latest, 1, 2, 1, 2)

		vbox.show_all()

	def __threaded_check(self):
		"""Method called in separate thread"""
		try:
			# get data from web
			url_handler = urlopen(self.URL)
			encoding = url_handler.headers.get_content_charset()
			data = url_handler.read().decode(encoding)

		finally:
			decoder = JSONDecoder()
			releases = decoder.decode(data)

			GObject.idle_add(self._entry_latest.set_text, releases[0]['tag_name'])

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys"""
		if event.keyval == Gdk.KEY_Escape:
			self._dialog.hide()

	def check(self):
		"""Check for new version online"""
		version = self._application.version

		# prepare template
		if version['stage'] != 'f':
			template = '{0[major]}.{0[minor]}{0[stage]}-{0[build]}'
		else:
			template = '{0[major]}.{0[minor]}-{0[build]}'

		# populate version values
		self._entry_current.set_text(template.format(version))
		self._entry_latest.set_text(_('Checking...'))

		# show dialog
		self._dialog.show()

		# start new thread and check for new version
		thread = Thread(target=self.__threaded_check)
		thread.start()

