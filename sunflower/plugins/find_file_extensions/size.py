from __future__ import absolute_import

from gi.repository import Gtk
from sunflower.plugin_base.find_extension import FindExtension


class SizeFindFiles(FindExtension):
	"""Size extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)

		# create container
		table = Gtk.Grid.new()
		set_border_width(table, 5)
		table.set_column_spacing(5)

		# create interface
		self._adjustment_max = Gtk.Adjustment.new(50.0, 0.0, 100000.0, 0.1, 10.0, 0.0)
		self._adjustment_min = Gtk.Adjustment.new(0.0, 0.0, 10.0, 0.1, 10.0, 0.0)

		label = Gtk.Label(label='<b>{0}</b>'.format(_('Match file size')))
		label.set_xalign(0.0)
		label.set_yalign(0.5)
		label.set_use_markup(True)

		label_min = Gtk.Label(label=_('Minimum:'))
		label_min.set_xalign(0)
		label_min.set_yalign(0.5)
		label_min_unit = Gtk.Label(label=_('MB'))

		label_max = Gtk.Label(label=_('Maximum:'))
		label_max.set_xalign(0)
		label_max.set_yalign(0.5)
		label_max_unit = Gtk.Label(label=_('MB'))

		self._entry_max = Gtk.SpinButton(adjustment=self._adjustment_max, digits=2)
		self._entry_min = Gtk.SpinButton(adjustment=self._adjustment_min, digits=2)
		self._entry_max.connect('value-changed', self._max_value_changed)
		self._entry_min.connect('value-changed', self._min_value_changed)
		self._entry_max.connect('activate', self._parent.find_files)
		self._entry_min.connect('activate', lambda entry: self._entry_max.grab_focus())

		# pack interface
		table.attach(label, 0, 0, 3, 1)

		table.attach(label_min, 0, 1, 1, 1)
		table.attach(self._entry_min, 1, 1, 1, 1)
		table.attach(label_min_unit, 2, 1, 1, 1)

		table.attach(label_max, 0, 2, 1, 1)
		table.attach(self._entry_max, 1, 2, 1, 1)
		table.attach(label_max_unit, 2, 2, 1, 1)

		if Gtk.get_major_version() == 3:
			self.container.pack_start(table, False, False, 0)

		else:
			self.container.append(table)

	def _max_value_changed(self, entry):
		"""Assign value to adjustment handler"""
		self._adjustment_min.set_upper(entry.get_value())

	def _min_value_changed(self, entry):
		"""Assign value to adjustment handler"""
		self._adjustment_max.set_lower(entry.get_value())

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Size')

	def is_path_ok(self, provider, path):
		"""Check is specified path fits the cirteria"""
		size = provider.get_stat(path).size
		size_max = self._entry_max.get_value() * 1048576
		size_min = self._entry_min.get_value() * 1048576
		return size_min < size < size_max
