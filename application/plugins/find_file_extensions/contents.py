import gtk

from plugin_base.provider import FileType, Mode
from plugin_base.find_extension import FindExtension


class ContentsFindFiles(FindExtension):
	"""Extension for finding specified contents in files"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		# connect notify signal
		parent.connect('notify-start', self.__handle_notify_start)

		# create container
		vbox = gtk.VBox(False, 0)

		viewport = gtk.ScrolledWindow()
		viewport.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		viewport.set_shadow_type(gtk.SHADOW_IN)

		# create entry widget
		label_content = gtk.Label(_('Search for:'))
		label_content.set_alignment(0, 0.5)

		self._buffer = gtk.TextBuffer()
		self._text_view = gtk.TextView(self._buffer)

		# pack interface
		viewport.add(self._text_view)

		vbox.pack_start(label_content, False, False, 0)
		vbox.pack_start(viewport, True, True, 0)

		self.vbox.pack_start(vbox, True, True, 0)

	def __handle_notify_start(self, data=None):
		"""Handle starting search."""
		Provider = self._parent._application.get_provider_by_path(self._parent._entry_path.get_text())
		self._provider = Provider(self._parent._application)

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Content')

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria"""
		result = False
		file_type = self._provider.get_stat(path).type

		if file_type is FileType.REGULAR:
			# get buffer
			text = self._buffer.get_text(*self._buffer.get_bounds())

			# try finding content in file
			try:
				with self._provider.get_file_handle(path, Mode.READ) as raw_file:  # make sure file is closed afterwards
					result = text in raw_file.read()

			except IOError:
				pass

		return result

