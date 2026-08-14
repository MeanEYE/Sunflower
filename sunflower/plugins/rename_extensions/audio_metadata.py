from __future__ import absolute_import

import os
import string

from gi.repository import Gtk
from sunflower.plugin_base.rename_extension import RenameExtension

try:
	import mutagen
	USE_MUTAGEN = True

except ImportError:
	USE_MUTAGEN = False


class AudioMetadataRename(RenameExtension):
	"""Song tags rename extension"""

	def __init__(self, parent):
		RenameExtension.__init__(self, parent)

		self._templates = {
					'[a]': ('album', _('Album')),
					'[A]': ('artist', _('Artist')),
					'[T]': ('title', _('Title')),
					'[G]': ('genre', _('Genre')),
					'[D]': ('date', _('Date')),
					'[t]': ('tracknumber', _('Track number')),
				}

		# create template entry
		label_template = Gtk.Label(label=_('Template:'))
		label_template.set_xalign(0)
		label_template.set_yalign(0.5)

		self._entry_template = Gtk.Entry()
		self._entry_template.set_text('[[t]] [A] - [T]')
		self._entry_template.connect('changed', self._update_parent_list)

		# create replace entry
		label_replace1 = Gtk.Label(label=_('Replace:'))
		label_replace1.set_xalign(0)
		label_replace1.set_yalign(0.5)

		self._entry_replace = Gtk.Entry()
		self._entry_replace.set_text(',?/')
		self._entry_replace.connect('changed', self._update_parent_list)

		# create replace combo boxes
		label_replace2 = Gtk.Label(label=_('With:'))
		label_replace2.set_xalign(0)
		label_replace2.set_yalign(0.5)

		self._combobox_replace = Gtk.ComboBoxText.new_with_entry()
		self._combobox_replace.connect('changed', self._update_parent_list)

		for str_rep in ('_', '-', ''):
			self._combobox_replace.append_text(str_rep)

		# create syntax
		label_tip = Gtk.Label()
		label_tip.set_xalign(0)
		label_tip.set_yalign(0)
		label_tip.set_use_markup(True)
		label_tip.set_markup('<b>{0}</b>\n{1}'.format(_('Template syntax'),
			'\n'.join(['{0}\t{1}'.format(k, v[1]) for k, v in self._templates.items()])))

		# create boxes
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 15)
		vbox_left = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		vbox_right = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_template = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		table_replace = Gtk.Grid.new()
		set_border_width(table_replace, 5)

		frame_replace = Gtk.Frame(label=_('Character replacement'))

		# disable checkbox if mutagen is not available
		self._checkbox_active.set_sensitive(USE_MUTAGEN)

		# create warning label
		label_warning = Gtk.Label(label=_(
			'In order to use this extension you need <b>mutagen</b> module installed!'
		))
		label_warning.set_use_markup(True)

		infobar = Gtk.InfoBar()
		if Gtk.get_major_version() == 3:
			infobar.set_property('no-show-all', USE_MUTAGEN)
			infobar_content = infobar.get_content_area()
			infobar_content.add(label_warning)

		else:
			infobar.set_visible(not (USE_MUTAGEN))
			infobar.add_child(label_warning)

		# pack gui
		if Gtk.get_major_version() == 3:
			vbox_template.pack_start(label_template, False, False, 0)
			vbox_template.pack_start(self._entry_template, False, False, 0)

		else:
			vbox_template.append(label_template)
			vbox_template.append(self._entry_template)

		self.vbox.remove(self._checkbox_active)

		table_replace.attach(label_replace1, 0, 0, 1, 1)
		table_replace.attach(self._entry_replace, 1, 0, 1, 1)
		table_replace.attach(label_replace2, 0, 1, 1, 1)
		table_replace.attach(self._combobox_replace, 1, 1, 1, 1)

		if Gtk.get_major_version() == 3:
			frame_replace.add(table_replace)

		else:
			frame_replace.set_child(table_replace)

		if Gtk.get_major_version() == 3:
			vbox_left.pack_start(self._checkbox_active, False, False, 0)
			vbox_left.pack_start(vbox_template, False, False, 0)
			vbox_left.pack_start(frame_replace, False, False, 0)

			vbox_right.pack_start(label_tip, False, False, 0)

			hbox.pack_start(vbox_left, True, True, 0)
			hbox.pack_start(vbox_right, True, True, 0)

			self.vbox.pack_start(infobar, False, False, 0)
			self.vbox.pack_start(hbox, False, False, 0)

		else:
			vbox_left.append(self._checkbox_active)
			vbox_left.append(vbox_template)
			vbox_left.append(frame_replace)

			vbox_right.append(label_tip)

			vbox_left.set_hexpand(True)
			hbox.append(vbox_left)
			vbox_right.set_hexpand(True)
			hbox.append(vbox_right)

			self.vbox.append(infobar)
			self.vbox.append(hbox)

	def get_title(self):
		"""Return extension title"""
		return _('Audio Metadata')

	def get_new_name(self, old_name, new_name):
		"""Get modified name"""
		basename, extension = os.path.splitext(new_name)
		path = os.path.join(self._parent._parent._parent.get_active_object().path, old_name)
		template = self._entry_template.get_text()
		tags = mutagen.File(path, easy=True)

		# check if filetype is supported by mutagen
		if tags is None:
			return new_name

		# fill template
		for k, v in self._templates.items():
			try:
				template = string.replace(template, k, tags[v[0]][0])
			except KeyError:
				template = string.replace(template, k, '')

		# replace unwanted characters
		str_rep = self._combobox_replace.get_active_text()
		for c in self._entry_replace.get_text():
			template = string.replace(template, c, str_rep)

		return '{0}{1}'.format(template, extension)

