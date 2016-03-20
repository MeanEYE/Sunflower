# coding: utf-8

import os
import sys

from gi.repository import Gtk, Gdk, Pango
from collections import namedtuple


Contributor = namedtuple(
				'Contributor',
				[
					'name',  # contributor's full name
					'email',
					'website',  # contributor's website url
				])


class AboutWindow:
	# list of contributors
	contributors = [
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
		Contributor(
			name = 'Arseniy Krasnov ',
			email = 'arseniy@krasnoff.org',
			website = None,
		),
		Contributor(
			name = 'Sevka Fedoroff',
			email = 'sevka.fedoroff@gmail.com',
			website = None
		),
		Contributor(
			name = 'multiSnow',
			email = 'infinity.blick.winkel@gmail.com',
			website = None
		)
	]

	# list of artists
	artists = [
		Contributor(
			name = 'Andrea Pavlović',
			email = 'octogirl.design@gmail.com',
			website = None,
		),
		Contributor(
			name = 'Michael Kerch',
			email = 'michael@way2cu.com',
			website = 'misha.co.il',
		),
	]

	translators = [

	]

	def __init__(self, parent):
		# create main window
		self._dialog = Gtk.AboutDialog()

		# prepare version template
		if parent.version['stage'] != 'f':
			version = '{0[major]}.{0[minor]}{0[stage]} ({0[build]})'.format(parent.version)
		else:
			version = '{0[major]}.{0[minor]} ({0[build]})'.format(parent.version)

		# set about dialog image
		base_path = os.path.dirname(os.path.dirname(sys.argv[0]))
		image = Gtk.Image()
		image.set_from_file(os.path.abspath(os.path.join(base_path, 'images', 'splash.png')))

		# configure dialog
		self._dialog.set_resizable(False)
		self._dialog.set_skip_taskbar_hint(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(parent)
		self._dialog.set_type_hint(Gdk.WindowTypeHint.DIALOG)
		self._dialog.set_wmclass('Sunflower', 'Sunflower')

		# connect signals
		self._dialog.connect('activate-link', parent.goto_web)

		# set dialog data
		self._dialog.set_name(_('Sunflower'))
		self._dialog.set_program_name(_('Sunflower'))
		self._dialog.set_version(version)
		self._dialog.set_logo(image.get_pixbuf())
		self._dialog.set_website('github.com/MeanEYE/Sunflower')
		self._dialog.set_comments(_('Twin-panel file manager for Linux.'))

		# set license
		self._dialog.set_copyright(_(u'Copyright \u00a9 2010-2016 by Mladen Mijatov and contributors.'))

		if os.path.isfile('COPYING'):
			license_file = open('COPYING', 'r')

			if license_file:
				license_text = license_file.read()
				license_file.close()

				self._dialog.set_license(license_text)

		else:
			# link to GPL3
			self._dialog.set_license('http://www.gnu.org/licenses/old-licenses/gpl-3.0.html')

		# set authors
		self._dialog.set_authors(['{0} <{1}> {2}'.format(
					contributor.name,
					contributor.email,
					contributor.website or ''
				) for contributor in self.contributors])

		self._dialog.set_artists(['{0} <{1}> {2}'.format(
					contributor.name,
					contributor.email,
					contributor.website or ''
				) for contributor in self.artists])

		self._dialog.set_translator_credits('\n'.join(['{0} <{1}> {2} - {3}'.format(
					contributor.name,
					contributor.email,
					contributor.website or '',
					contributor.language
				) for contributor in self.translators]))

	def show(self):
		"""Show dialog"""
		self._dialog.run()
		self._dialog.destroy()
