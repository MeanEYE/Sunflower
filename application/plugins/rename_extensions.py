import re
import os
import gtk

from plugin_base.rename_extension import RenameExtension


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_rename_extension('default', DefaultRename)
	

class DefaultRename(RenameExtension):
	"""Default rename extension support"""
	
	def __init__(self, parent):
		super(DefaultRename, self).__init__(parent)

		# default option needs to be active by default		
		self._checkbox_active.set_active(True)
		
		# create expressions
		self._regexp_name = re.compile('\[(N|E|C)([\d][^-]*)?-?([\d][^\]]*)?\]', re.I | re.U)
		
		self._template = '[N][E]'
		self._counter = 0
		self._counter_start = 0
		self._counter_step = 1
		self._counter_digits = 1;
		
		# create user interface
		hbox = gtk.HBox(True, 15)
		
		vbox_left = gtk.VBox(False, 5)
		vbox_right = gtk.VBox(False, 5)
		
		# help
		label_help = gtk.Label()
		label_help.set_alignment(0, 0)
		label_help.set_use_markup(True)
		
		label_help.set_markup(_(
							'<b>Template syntax</b>\n'
							'[N]\tItem name\n'
							'[E]\tExtension\n'
							'[C]\tCounter\n\n'
							'For name and extension you can\n'
							'use range in format [N#-#].'
						))
		
		# template
		vbox_template = gtk.VBox(False, 0)
		
		label_template = gtk.Label(_('Template:'))
		label_template.set_alignment(0, 0.5)
		
		self._entry_template = gtk.Entry()
		self._entry_template.set_text(self._template)
		self._entry_template.connect('activate', self.__template_changed)
		
		# counter
		frame_counter = gtk.Frame(label=_('Counter'))
		
		table_counter = gtk.Table(3, 2)
		table_counter.set_border_width(5)
		table_counter.set_col_spacings(5)
		
		label_start = gtk.Label(_('Start:'))
		label_start.set_alignment(0, 0.5)
		
		adjustment = gtk.Adjustment(0, 0, 10**10, 1, 10)
		self._entry_start = gtk.SpinButton(adjustment, 0, 0)
		self._entry_start.connect('value-changed', self.__counter_changed)
		
		label_step = gtk.Label(_('Step:'))
		label_step.set_alignment(0, 0.5)

		adjustment = gtk.Adjustment(1, 1, 10**10, 1, 10)
		self._entry_step = gtk.SpinButton(adjustment, 0, 0)
		self._entry_step.connect('value-changed', self.__counter_changed)
		
		label_digits = gtk.Label(_('Digits:'))
		label_digits.set_alignment(0, 0.5)

		adjustment = gtk.Adjustment(1, 1, 20, 1, 5)
		self._entry_digits = gtk.SpinButton(adjustment, 0, 0)
		self._entry_digits.connect('value-changed', self.__counter_changed)

		# repack 'active' check box
		self.remove(self._checkbox_active)
		vbox_left.pack_start(self._checkbox_active, False, False, 0)
		
		# pack interface
		table_counter.attach(label_start, 0, 1, 0, 1)
		table_counter.attach(self._entry_start, 0, 1, 1, 2, xoptions=gtk.EXPAND|gtk.FILL)
		table_counter.attach(label_step, 1, 2, 0, 1)
		table_counter.attach(self._entry_step, 1, 2, 1, 2, xoptions=gtk.EXPAND|gtk.FILL)
		table_counter.attach(label_digits, 2, 3, 0, 1)
		table_counter.attach(self._entry_digits, 2, 3, 1, 2, xoptions=gtk.EXPAND|gtk.FILL)
		
		frame_counter.add(table_counter)
		
		vbox_template.pack_start(label_template, False, False, 0)
		vbox_template.pack_start(self._entry_template, False, False, 0)
		
		vbox_left.pack_start(vbox_template, False, False, 0)
		vbox_left.pack_start(frame_counter, False, False, 0)
		
		vbox_right.pack_start(label_help, True, True, 0)
		
		hbox.pack_start(vbox_left, True, True, 0)
		hbox.pack_start(vbox_right, True, True, 0)
		
		self.pack_start(hbox, True, True, 0)

		self.show_all()
		
	def __template_changed(self, widget, data=None):
		"""Handle template string change"""
		self._template = widget.get_text()
		
		# update parent list
		self._update_parent_list()
		
	def __counter_changed(self, widget, data=None):
		"""Handle changing counter values"""
		self._counter_start = self._entry_start.get_value_as_int()
		self._counter_step = self._entry_step.get_value_as_int()
		self._counter_digits = self._entry_digits.get_value_as_int()
		
		self._update_parent_list()
		
	def reset(self):
		"""Reset counter"""
		self._counter = self._counter_start
		
	def get_title(self):
		"""Return extension title"""
		return _('Basic')
	
	def get_new_name(self, old_name, new_name):
		"""Get modified name"""
		result = new_name
		basename, extension = os.path.splitext(result)
		
		def replace_method(match):
			type = match.group(1)
			
			if type in ('N', 'E'):
				# match is name or extension
				name = basename if type == 'N' else extension
				
				# get starting point
				try:
					start = int(match.group(2))
				except:
					start = 0
	
				# get ending point				
				try:
					end = int(match.group(3))
				except:
					end = len(name)

				result = name[start:end]
				
			elif type == 'C':
				# match is a counter 
				result = str(self._counter).zfill(self._counter_digits)
				
			return result
		
		# replace all occurrences
		result = self._regexp_name.sub(replace_method, self._template)
		
		# increase counter
		self._counter += self._counter_step
		
		return result
		