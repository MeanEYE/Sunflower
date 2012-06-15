import os
import gtk
import fnmatch

from plugin_base.find_extension import FindExtension


class DefaultFindFiles(FindExtension):
	"""Default extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		self._pattern = '*'
		self._compare_method = fnmatch.fnmatch

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
		vbox_pattern = gtk.VBox(False, 0)

		label_pattern = gtk.Label(_('Search for:'))
		label_pattern.set_alignment(0, 0.5)

		self._entry_pattern = gtk.Entry()
		self._entry_pattern.set_text('*')
		self._entry_pattern.connect('changed', self.__handle_pattern_change)
		self._entry_pattern.connect('activate', self._parent.find_files)

		self._checkbox_case_sensitive = gtk.CheckButton(_('Case sensitive'))
		self._checkbox_case_sensitive.connect('toggled', self.__handle_case_sensitive_toggle)

		# pack interface
		self.vbox.remove(self._checkbox_active)

		vbox_pattern.pack_start(label_pattern, False, False, 0)
		vbox_pattern.pack_start(self._entry_pattern, False, False, 0)

		vbox_left.pack_start(self._checkbox_active, False, False, 0)
		vbox_left.pack_start(vbox_pattern, False, False, 0)
		vbox_left.pack_start(self._checkbox_case_sensitive, False, False, 0)

		vbox_right.pack_start(label_help, True, True, 0)

		hbox.pack_start(vbox_left, True, True, 0)
		hbox.pack_start(vbox_right, True, True, 0)

		self.vbox.pack_start(hbox, True, True, 0)

	def __handle_case_sensitive_toggle(self, widget, data=None):
		"""Handle toggling case sensitive check box"""
		self._compare_method = (
							fnmatch.fnmatch,
							fnmatch.fnmatchcase
						)[widget.get_active()]

	def __handle_pattern_change(self, widget, data=None):
		"""Handle changing pattern"""
		self._pattern = widget.get_text()

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Basic')

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria"""
		file_name = os.path.basename(path)
		return self._compare_method(file_name, self._pattern)
