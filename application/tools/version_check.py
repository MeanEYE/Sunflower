import gtk
import urllib

from threading import Thread


class VersionCheck:
	"""Small class used for checking and displaying current and
	latest version of software detected by getting a file from 
	project hosting site.

	"""

	URL = 'http://sunflower-fm.googlecode.com/hg/.hgtags'

	def __init__(self, application):
		self._dialog = gtk.Window(type=gtk.WINDOW_TOPLEVEL)

		self._application = application

		# configure window
		self._dialog.set_title(_('Version check'))
		self._dialog.set_wmclass('Sunflower', 'Sunflower')
		self._dialog.set_border_width(7)
		self._dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self._dialog.set_resizable(False)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)
		self._dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self._dialog.connect('key-press-event', self._handle_key_press)

		# create user interface
		vbox = gtk.VBox(False, 5)
		hbox = gtk.HBox(False, 0)
		table = gtk.Table(2, 2)

		table.set_row_spacings(5)
		table.set_col_spacings(5)

		label_current = gtk.Label(_('Current:'))
		label_current.set_alignment(0, 0.5)

		label_latest = gtk.Label(_('Latest:'))
		label_latest.set_alignment(0, 0.5)

		self._entry_current = gtk.Entry()
		self._entry_current.set_editable(False)

		self._entry_latest = gtk.Entry()
		self._entry_latest.set_editable(False)

		separator = gtk.HSeparator()

		# create controls
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
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
			url_handler = urllib.urlopen(self.URL)
			data = url_handler.read().split('\n')

		finally:
			latest_data = data[-2].split(' ')

			with gtk.gdk.lock:
				self._entry_latest.set_text(latest_data[1])

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys"""
		if event.keyval == gtk.keysyms.Escape:
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

