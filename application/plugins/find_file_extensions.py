import os
import gtk
import fnmatch

from plugin_base.find_extension import FindExtension
from provider import FileType


def register_plugin(application):
	"""register plugin classes with application"""
	application.register_find_extension('default', DefaultFindFiles)
	application.register_find_extension('size', SizeFindFiles)
	application.register_find_extension('contents', ContentsFindFiles)


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


class SizeFindFiles(FindExtension):
	"""Size extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		# create interface
		self._adj_max = gtk.Adjustment(value=50.0, lower=0.0, upper=100000.0, step_incr=0.1, page_incr=10.0)
		self._adj_min = gtk.Adjustment(value=0.0, lower=0.0, upper=10.0, step_incr=0.1, page_incr=10.0)

		label = gtk.Label(_('Search for files:'))
		label.set_alignment(0.0, 0.5)
		label_max1 = gtk.Label(_('smaller than'))
		label_max2 = gtk.Label(_('MB'))
		label_min1 = gtk.Label(_('bigger than'))
		label_min2 = gtk.Label(_('MB'))

		self._entry_max = gtk.SpinButton(adjustment=self._adj_max, digits=2)
		self._entry_min = gtk.SpinButton(adjustment=self._adj_min, digits=2)
		self._entry_max.connect('value-changed', self._max_value_changed)
		self._entry_min.connect('value-changed', self._min_value_changed)

		# pack interface
		table =  gtk.Table(3, 3, False)
		table.set_border_width(5)
		table.set_col_spacings(5)
		table.set_row_spacings(5)

		table.attach(label, 0, 3, 0, 1, xoptions=gtk.FILL)

		table.attach(label_max1, 0, 1, 1, 2, xoptions=gtk.FILL)
		table.attach(self._entry_max,  1, 2, 1, 2, xoptions=gtk.FILL)
		table.attach(label_max2, 2, 3, 1, 2, xoptions=gtk.FILL)

		table.attach(label_min1, 0, 1, 2, 3, xoptions=gtk.FILL)
		table.attach(self._entry_min,  1, 2, 2, 3, xoptions=gtk.FILL)
		table.attach(label_min2, 2, 3, 2, 3, xoptions=gtk.FILL)

		self.vbox.pack_start(table, False, False, 0)

	def _max_value_changed(self, entry):
		self._adj_min.set_upper(entry.get_value());

	def _min_value_changed(self, entry):
		self._adj_max.set_lower(entry.get_value());

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Size')

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria"""
		size = self._parent._provider.get_stat(path).size
		size_max = self._entry_max.get_value() * 1048576
		size_min = self._entry_min.get_value() * 1048576
		return size_min < size < size_max


class ContentsFindFiles(FindExtension):
	"""Extension for finding specified contents in files"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		self._buffer = gtk.TextBuffer()
		self._text_view = gtk.TextView(self._buffer)

		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		
		scrolled_window.add(self._text_view)
		self.vbox.pack_start(scrolled_window, True, True, 5)

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Contents')

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria"""
		if not self._parent._provider.is_local:
			return False

		if self._parent._provider.get_stat(path).type is FileType.DIRECTORY:
			return False

		start = self._buffer.get_start_iter()
		end = self._buffer.get_end_iter()
		try:
			return self._buffer.get_text(start, end) in open(path).read()
		except IOError:
			return False

