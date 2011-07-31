import gtk

from plugin_base.find_extension import FindExtension


def register_plugin(application):
	"""register plugin classes with application"""
	application.register_find_extension('default', DefaultFindFiles)


class DefaultFindFiles(FindExtension):
	"""Default extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)
	
		# enabled by default
		self._checkbox_active.set_active(True)

		# help
		label_help = gtk.Label()
		label_help.set_alignment(0, 0)
		label_help.set_use_markup(True)

		label_help.set_markup(_(
							'<b>Pattern matching</b>\n'
							'*\t\tEverything\n'
							'?\t\tAny single character\n'
							'[seq]\tAny character in <i>seq</i>\n'
							'[!seq]\tAny character <u>not</u> in <i>seq</i>'
						))

		# create containers
		hbox = gtk.HBox(True, 15)
		vbox_left = gtk.VBox(False, 5)
		vbox_right = gtk.VBox(False, 0)

		# create interface
		vbox_entry = gtk.VBox(False, 0)

		label_entry = gtk.Label(_('Search for:'))
		label_entry.set_alignment(0, 0.5)
		
		self._entry = gtk.Entry()
		self._entry.set_text('*')

		self._checkbox_case_sensitive = gtk.CheckButton(_('Case sensitive'))

		# pack interface
		self.vbox.remove(self._checkbox_active)

		vbox_entry.pack_start(label_entry, False, False, 0)
		vbox_entry.pack_start(self._entry, False, False, 0)

		vbox_left.pack_start(self._checkbox_active, False, False, 0)
		vbox_left.pack_start(vbox_entry, False, False, 0)
		vbox_left.pack_start(self._checkbox_case_sensitive, False, False, 0)

		vbox_right.pack_start(label_help, True, True, 0)

		hbox.pack_start(vbox_left, True, True, 0)
		hbox.pack_start(vbox_right, True, True, 0)

		self.vbox.pack_start(hbox, True, True, 0)

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Basic')

	def is_file_ok(self, path):
		"""Check is specified path fits the cirteria"""
		return True
