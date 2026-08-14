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
		if Gtk.get_major_version() == 3:
			self._dialog = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)

		else:
			self._dialog = Gtk.Window.new()
		self._application = application

		# configure window
		self._dialog.set_title(_('Version check'))
		self._dialog.set_resizable(False)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)
		if Gtk.get_major_version() == 3:
			self._dialog.set_type_hint(Gdk.WindowTypeHint.DIALOG)

			self._dialog.connect('key-press-event', self._handle_key_press)

		else:
			key_controller = Gtk.EventControllerKey.new()
			key_controller.connect('key-pressed', self._handle_key_pressed)
			self._dialog.add_controller(key_controller)
		# create user interface
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(vbox, 7)
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
		table = Gtk.Grid.new()

		table.set_row_spacing(5)
		table.set_column_spacing(5)

		label_current = Gtk.Label(label=_('Current:'))
		label_current.set_xalign(0)
		label_current.set_yalign(0.5)

		label_latest = Gtk.Label(label=_('Latest:'))
		label_latest.set_xalign(0)
		label_latest.set_yalign(0.5)

		self._entry_current = Gtk.Entry()
		self._entry_current.set_editable(False)

		self._entry_latest = Gtk.Entry()
		self._entry_latest.set_editable(False)

		separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		# create controls
		button_close = Gtk.Button.new_with_label(_('Close'))
		button_close.connect('clicked', lambda widget: self._dialog.hide())

		# pack user interface
		if Gtk.get_major_version() == 3:
			self._dialog.add(vbox)

			vbox.pack_start(table, True, True, 0)
			vbox.pack_start(separator, True, True, 0)
			vbox.pack_start(hbox, True, True, 0)

			hbox.pack_end(button_close, False, False, 0)

		else:
			self._dialog.set_child(vbox)

			table.set_vexpand(True)
			vbox.append(table)
			separator.set_vexpand(True)
			vbox.append(separator)
			hbox.set_vexpand(True)
			vbox.append(hbox)

			button_close.set_hexpand(True)
			button_close.set_halign(Gtk.Align.END)
			hbox.append(button_close)

		table.attach(label_current, 0, 0, 1, 1)
		table.attach(label_latest, 0, 1, 1, 1)
		table.attach(self._entry_current, 1, 0, 1, 1)
		table.attach(self._entry_latest, 1, 1, 1, 1)

		if Gtk.get_major_version() == 3:
			vbox.show_all()

		else:
			vbox.show()

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
		"""Handle pressing keys (GTK 3)"""
		return self._handle_keyval(event.keyval, event.get_state())

	def _handle_key_pressed(self, controller, keyval, keycode, state):
		"""Handle pressing keys (GTK 4)"""
		return self._handle_keyval(keyval, state)

	def _handle_keyval(self, keyval, state):
		"""Handle pressing keys"""
		if keyval == Gdk.KEY_Escape:
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

