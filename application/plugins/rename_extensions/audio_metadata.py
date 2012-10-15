import os
import gtk
import string

try:
	import mutagen
	USE_MUTAGEN = True

except ImportError:
	USE_MUTAGEN = False

from plugin_base.rename_extension import RenameExtension


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
		label_template = gtk.Label(_('Template:'))
		label_template.set_alignment(0, 0.5)

		self._entry_template = gtk.Entry()
		self._entry_template.set_text('[[t]] [A] - [T]')
		self._entry_template.connect('changed', self._update_parent_list)

		# create replace entry
		label_replace1 = gtk.Label(_('Replace:'))
		label_replace1.set_alignment(0, 0.5)

		self._entry_replace = gtk.Entry()
		self._entry_replace.set_text(',?/')
		self._entry_replace.connect('changed', self._update_parent_list)

		# create replace combo boxes
		label_replace2 = gtk.Label(_('With:'))
		label_replace2.set_alignment(0, 0.5)

		self._combobox_replace = gtk.combo_box_entry_new_text()
		self._combobox_replace.connect('changed', self._update_parent_list)

		for str_rep in ('_', '-', ''):
			self._combobox_replace.append_text(str_rep)

		# create syntax
		label_tip = gtk.Label()
		label_tip.set_alignment(0, 0)
		label_tip.set_use_markup(True)
		label_tip.set_markup('<b>{0}</b>\n{1}'.format(_('Template syntax'),
			'\n'.join(['{0}\t{1}'.format(k, v[1]) for k, v in self._templates.iteritems()])))

		# create boxes
		hbox = gtk.HBox(True, 15)
		vbox_left = gtk.VBox(False, 5)
		vbox_right = gtk.VBox(False, 0)
		vbox_template = gtk.VBox(False, 0)
		table_replace = gtk.Table(2, 2, False)
		table_replace.set_border_width(5)

		frame_replace = gtk.Frame(label=_('Character replacement'))

		# disable checkbox if mutagen is not available
		self._checkbox_active.set_sensitive(USE_MUTAGEN)

		# create warning label
		label_warning = gtk.Label(_(
							'In order to use this extension you need <b>mutagen</b> module installed!'
						))
		label_warning.set_use_markup(True)
		label_warning.set_property('no-show-all', USE_MUTAGEN)

		# pack gui
		vbox_template.pack_start(label_template, False, False, 0)
		vbox_template.pack_start(self._entry_template, False, False, 0)

		self.vbox.remove(self._checkbox_active)

		table_replace.attach(label_replace1, 0, 1, 0, 1)
		table_replace.attach(self._entry_replace, 1, 2, 0, 1, xoptions=gtk.FILL)
		table_replace.attach(label_replace2, 0, 1, 1, 2)
		table_replace.attach(self._combobox_replace, 1, 2, 1, 2, xoptions=gtk.FILL)

		frame_replace.add(table_replace)

		vbox_left.pack_start(self._checkbox_active, False, False, 0)
		vbox_left.pack_start(vbox_template, False, False, 0)
		vbox_left.pack_start(frame_replace, False, False, 0)

		vbox_right.pack_start(label_tip, False, False, 0)

		hbox.pack_start(vbox_left, True, True, 0)
		hbox.pack_start(vbox_right, True, True, 0)

		self.vbox.pack_start(hbox, False, False, 0)
		self.vbox.pack_end(label_warning, False, False, 0)

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
		if tags == None:
			return new_name

		# fill template
		for k, v in self._templates.iteritems():
			try:
				template = string.replace(template, k, tags[v[0]][0])
			except KeyError:
				template = string.replace(template, k, '')

		# replace unwanted characters
		str_rep = self._combobox_replace.get_active_text()
		for c in self._entry_replace.get_text():
			template = string.replace(template, c, str_rep)

		return '{0}{1}'.format(template, extension)

