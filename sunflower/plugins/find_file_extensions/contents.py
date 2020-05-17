from __future__ import absolute_import

from gi.repository import Gtk
from sunflower.plugin_base.provider import FileType, Mode
from sunflower.plugin_base.find_extension import FindExtension


class ContentsFindFiles(FindExtension):
	"""Extension for finding specified contents in files"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		# create container
		vbox = Gtk.VBox(False, 0)

		viewport = Gtk.ScrolledWindow()
		viewport.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		viewport.set_shadow_type(Gtk.ShadowType.IN)

		# create entry widget
		label_content = Gtk.Label(label=_('Search for:'))
		label_content.set_alignment(0, 0.5)

		self._buffer = Gtk.TextBuffer()
		self._text_view = Gtk.TextView(buffer=self._buffer)

		# pack interface
		viewport.add(self._text_view)

		vbox.pack_start(label_content, False, False, 0)
		vbox.pack_start(viewport, True, True, 0)

		self.container.pack_start(vbox, True, True, 0)

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Content')

	def is_path_ok(self, provider, path):
		"""Check if specified path fits the criteria"""
		result = False
		file_type = provider.get_stat(path).type

		if file_type is FileType.REGULAR:
			# get buffer
			text = self._buffer.get_text(*self._buffer.get_bounds(), include_hidden_chars=True)

			# try finding content in file
			try:
				with provider.get_file_handle(path, Mode.READ) as raw_file:  # make sure file is closed afterwards
					result = text.encode() in raw_file.read()

			except IOError:
				pass

		return result

