# coding: utf-8
from __future__ import absolute_import

import os
import sys
import zipfile

from sunflower import common
from gi.repository import Gtk, Gdk, Pango, GLib, GdkPixbuf, Gio
from collections import namedtuple


Contributor = namedtuple(
				'Contributor',
				[
					'name',  # contributor's full name
					'email',
				])


class AboutWindow:
	# list of contributors
	contributors = [
		Contributor(name='Wojciech Kluczka', email='wojtekkluczka@gmail.com'),
		Contributor(name='Grigory Petrov', email='grigory.v.p@gmail.com'),
		Contributor(name='Sebastian Gaul', email='sebastian@dev.mgvmedia.com'),
		Contributor(name='Arseniy Krasnov ', email='arseniy@krasnoff.org'),
		Contributor(name='Sevka Fedoroff', email='sevka.fedoroff@gmail.com'),
		Contributor(name='multiSnow', email='infinity.blick.winkel@gmail.com')
	]

	# list of artists
	artists = [
		Contributor(name='Andrea Pavlović', email='octogirl.design@gmail.com'),
		Contributor(name='Michael Kerch', email='michael@way2cu.com'),
	]

	def __init__(self, parent):
		# create main window
		self._dialog = Gtk.AboutDialog.new()

		# prepare version template
		if parent.version['stage'] != 'f':
			version = '{0[major]}.{0[minor]}{0[stage]} ({0[build]})'.format(parent.version)
		else:
			version = '{0[major]}.{0[minor]} ({0[build]})'.format(parent.version)

		# set about dialog image
		image = Gtk.Image()
		image_path = os.path.join(common.get_base_directory(), 'images', 'splash.png')
		path = os.path.abspath(image_path)

		if os.path.isfile(sys.path[0]) and sys.path[0] != '':
			archive = zipfile.ZipFile(sys.path[0])
			with archive.open('images/splash.png') as raw_file:
				buff = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(raw_file.read()))
				pixbuf = GdkPixbuf.Pixbuf.new_from_stream(buff, None)
				image.set_from_pixbuf(pixbuf)
			archive.close()

		elif not os.path.exists(path):
			path = '/usr/share/pixmaps/sunflower/splash.png'
			image.set_from_file(path)

		# configure dialog
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		# connect signals
		self._dialog.connect('activate-link', parent.goto_web)

		# set dialog data
		self._dialog.set_name(_('Sunflower'))
		self._dialog.set_program_name(_('Sunflower'))
		self._dialog.set_version(version)
		self._dialog.set_logo(image.get_pixbuf())
		self._dialog.set_website('sunflower-fm.org')
		self._dialog.set_comments(_('Twin-panel file manager for Linux.'))

		# set license
		self._dialog.set_copyright(_(u'Copyright \u00a9 2010-2019 by Mladen Mijatov and contributors.'))

		if os.path.isfile('COPYING'):
			license_file = open('COPYING', 'r')

			if license_file:
				license_text = license_file.read()
				license_file.close()

				self._dialog.set_license(license_text)

		else:
			self._dialog.set_license('http://www.gnu.org/licenses/old-licenses/gpl-3.0.html')

		# set authors
		self._dialog.set_authors(['Mladen Mijatov <meaneye.rcf@gmail.com>'])
		self._dialog.add_credit_section(_('Contributors'), ['{0} <{1}>'.format(
					contributor.name,
					contributor.email,
				) for contributor in self.contributors])

		self._dialog.set_artists(['{0} <{1}>'.format(
					contributor.name,
					contributor.email,
				) for contributor in self.artists])

	def show(self):
		"""Show dialog"""
		self._dialog.run()
		self._dialog.destroy()
