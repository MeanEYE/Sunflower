import os
import gtk
import string

from plugin_base.rename_extension import RenameExtension


class LetterCaseRename(RenameExtension):
	"""Letter case rename extension support"""

	def __init__(self, parent):
		RenameExtension.__init__(self, parent)

		self._basename_methods = (
					(_('Do nothing'), self.__do_nothing),
					(_('Capitalize'), self.__capitalize),
					(_('Upper case'), self.__upper),
					(_('Lower case'), self.__lower),
					(_('Swap case'), self.__swap),
				)

		self._extension_methods = (
					(_('Do nothing'), self.__do_nothing),
					(_('Upper case'), self.__upper),
					(_('Lower case'), self.__lower),
				)

		# create labels
		label_basename = gtk.Label(_('Item name:'))
		label_basename.set_alignment(0, 0.5)

		label_extension = gtk.Label(_('Extension:'))
		label_extension.set_alignment(0, 0.5)

		# create combo boxes
		self._combo_basename = gtk.combo_box_new_text()
		self._combo_basename.connect('changed', self._update_parent_list)

		self._combo_extension = gtk.combo_box_new_text()
		self._combo_extension.connect('changed', self._update_parent_list)

		# fill comboboxes
		for method in self._basename_methods:
			self._combo_basename.append_text(method[0])

		for method in self._extension_methods:
			self._combo_extension.append_text(method[0])

		self._combo_basename.set_active(0)
		self._combo_extension.set_active(0)

		# pack gui
		table = gtk.Table(2, 2, False)
		table.set_col_spacing(0, 5)
		table.set_row_spacings(5)

		table.attach(label_basename, 0, 1, 0, 1, xoptions=gtk.FILL)
		table.attach(label_extension, 0, 1, 1, 2, xoptions=gtk.FILL)

		table.attach(self._combo_basename, 1, 2, 0, 1, xoptions=gtk.FILL)
		table.attach(self._combo_extension, 1, 2, 1, 2, xoptions=gtk.FILL)

		self.vbox.pack_start(table, False, False, 0)

	def __do_nothing(self, name):
		"""Return the same string"""
		return name

	def __capitalize(self, name):
		"""Return capitalized string"""
		return string.capwords(name)

	def __upper(self, name):
		"""Return upper case string"""
		return name.upper()

	def __lower(self, name):
		"""Return lower case string"""
		return name.lower()

	def __swap(self, name):
		"""Swap case in string"""
		return name.swapcase()

	def get_title(self):
		"""Return extension title"""
		return _('Letter Case')

	def get_new_name(self, old_name, new_name):
		"""Get modified name"""
		basename, extension = os.path.splitext(new_name)
		new_basename = self._basename_methods[self._combo_basename.get_active()][1](basename)
		new_extension = self._extension_methods[self._combo_extension.get_active()][1](extension)
		return "{0}{1}".format(new_basename, new_extension)
