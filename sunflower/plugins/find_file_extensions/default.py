import os
import fnmatch

from gi.repository import Gtk
from sunflower.plugin_base.find_extension import FindExtension


class DefaultFindFiles(FindExtension):
	"""Default extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		self._pattern = '*'
		self._compare_method = fnmatch.fnmatch

		# prepare options
		plugin_options = parent._application.plugin_options
		self._options = plugin_options.create_section(self.__class__.__name__)

		# connect notify signal
		parent.connect('notify-start', self.__handle_notify_start)

		# enabled by default
		self._checkbox_active.set_active(True)

		# create label showing pattern help
		label_help = Gtk.Label()
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
		hbox = Gtk.HBox(True, 15)
		vbox_left = Gtk.VBox(False, 5)
		vbox_right = Gtk.VBox(False, 0)

		# create interface
		vbox_pattern = Gtk.VBox(False, 0)

		label_pattern = Gtk.Label(label=_('Search for:'))
		label_pattern.set_alignment(0, 0.5)

		self._entry_pattern = Gtk.ComboBoxText.new_with_entry()
		self._entry_pattern.connect('changed', self.__handle_pattern_change)

		self._checkbox_case_sensitive = Gtk.CheckButton(_('Case sensitive'))
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

		# load saved values
		self._load_history()
		self._pattern = self._entry_pattern.get_active_text()
		self._case_sensitive = False

	def __handle_case_sensitive_toggle(self, widget, data=None):
		"""Handle toggling case sensitive check box"""
		self._compare_method = (
							fnmatch.fnmatch,
							fnmatch.fnmatchcase
						)[widget.get_active()]
		self._case_sensitive = widget.get_active()

	def __handle_pattern_change(self, widget, data=None):
		"""Handle changing pattern"""
		self._pattern = widget.get_child().get_text()

	def __handle_notify_start(self, data=None):
		"""Handle starting search."""
		entries = self._options.get('patterns') or []

		# insert pattern to search history
		if self._pattern is not None and self._pattern not in entries:
			entries.insert(0, self._pattern)
			entries = entries[:20]

			# save history
			self._options.set('patterns', entries)

	def _load_history(self):
		"""Load previously stored patterns."""
		entries = self._options.get('patterns') or ['*']

		for entry in entries:
			self._entry_pattern.append_text(entry)

		# select first entry
		self._entry_pattern.handler_block_by_func(self.__handle_pattern_change)
		self._entry_pattern.get_child().set_text(entries[0])
		self._entry_pattern.handler_unblock_by_func(self.__handle_pattern_change)

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Basic')

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria"""
		result = False
		file_name = os.path.basename(path)

		# prepare patterns
		patterns = (self._pattern,) if ';' not in self._pattern else self._pattern.split(';')

		if not self._case_sensitive:
			file_name = file_name.lower()
			patterns = map(lambda x: x.lower(), patterns)

		# try to match any of the patterns
		for pattern in patterns:
			if self._compare_method(file_name, pattern):
				result = True
				break

		return result
