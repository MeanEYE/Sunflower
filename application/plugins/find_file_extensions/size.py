import gtk

from plugin_base.find_extension import FindExtension


class SizeFindFiles(FindExtension):
	"""Size extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		# create container
		table =  gtk.Table(2, 4, False)
		table.set_border_width(5)
		table.set_col_spacings(5)

		# create interface
		self._adjustment_max = gtk.Adjustment(value=50.0, lower=0.0, upper=100000.0, step_incr=0.1, page_incr=10.0)
		self._adjustment_min = gtk.Adjustment(value=0.0, lower=0.0, upper=10.0, step_incr=0.1, page_incr=10.0)

		label = gtk.Label('<b>{0}</b>'.format(_('Match file size')))
		label.set_alignment(0.0, 0.5)
		label.set_use_markup(True)

		label_min = gtk.Label(_('Minimum:'))
		label_min.set_alignment(0, 0.5)
		label_min_unit = gtk.Label(_('MB'))

		label_max = gtk.Label(_('Maximum:'))
		label_max.set_alignment(0, 0.5)
		label_max_unit = gtk.Label(_('MB'))

		self._entry_max = gtk.SpinButton(adjustment=self._adjustment_max, digits=2)
		self._entry_min = gtk.SpinButton(adjustment=self._adjustment_min, digits=2)
		self._entry_max.connect('value-changed', self._max_value_changed)
		self._entry_min.connect('value-changed', self._min_value_changed)
		self._entry_max.connect('activate', self._parent.find_files)
		self._entry_min.connect('activate', lambda entry: self._entry_max.grab_focus())

		# pack interface
		table.attach(label, 0, 3, 0, 1, xoptions=gtk.FILL)

		table.attach(label_min, 0, 1, 1, 2, xoptions=gtk.FILL)
		table.attach(self._entry_min, 1, 2, 1, 2, xoptions=gtk.FILL)
		table.attach(label_min_unit, 2, 3, 1, 2, xoptions=gtk.FILL)

		table.attach(label_max, 0, 1, 2, 3, xoptions=gtk.FILL)
		table.attach(self._entry_max, 1, 2, 2, 3, xoptions=gtk.FILL)
		table.attach(label_max_unit, 2, 3, 2, 3, xoptions=gtk.FILL)

		self.vbox.pack_start(table, False, False, 0)

	def _max_value_changed(self, entry):
		"""Assign value to adjustment handler"""
		self._adjustment_min.set_upper(entry.get_value())

	def _min_value_changed(self, entry):
		"""Assign value to adjustment handler"""
		self._adjustment_max.set_lower(entry.get_value())

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Size')

	def is_path_ok(self, path):
		"""Check is specified path fits the cirteria"""
		size = self._parent._provider.get_stat(path).size
		size_max = self._entry_max.get_value() * 1048576
		size_min = self._entry_min.get_value() * 1048576
		return size_min < size < size_max
