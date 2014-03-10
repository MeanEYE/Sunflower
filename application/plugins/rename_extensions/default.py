import re
import os
import gtk

from plugin_base.rename_extension import RenameExtension
from gui.input_dialog import InputRangeDialog
from tools.advanced_rename import Column as RenameColumn


class DefaultRename(RenameExtension):
	"""Default rename extension support"""

	def __init__(self, parent):
		RenameExtension.__init__(self, parent)

		# default option needs to be active by default
		self._checkbox_active.set_active(True)

		# create expressions
		self._regexp_name = re.compile('\[(N|E|C)([\d][^-]*)?-?([\d][^\]]*)?\]', re.I | re.U)

		self._template = '[N][E]'
		self._counter = 0
		self._counter_start = 0
		self._counter_step = 1
		self._counter_digits = 1

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
		hbox_template = gtk.HBox(False, 2)

		label_template = gtk.Label(_('Template:'))
		label_template.set_alignment(0, 0.5)

		self._entry_template = gtk.Entry()
		self._entry_template.set_text(self._template)
		self._entry_template.connect('changed', self.__template_changed)

		style = gtk.RcStyle()
		style.xthickness = 0
		style.ythickness = 0

		image_add = gtk.Image()
		image_add.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
		button_add = gtk.Button()
		button_add.set_image(image_add)
		button_add.modify_style(style)
		button_add.connect('clicked', self.__button_add_clicked)

		# create popup menu
		self._add_menu = gtk.Menu()

		item_add_name = gtk.MenuItem(label=_('Name'))
		item_add_name.connect('activate', self.__add_to_template, 'N')

		item_add_name_part = gtk.MenuItem(label=_('Part of name'))
		item_add_name_part.connect('activate', self.__add_range_to_template, 'N')

		item_separator1 = gtk.SeparatorMenuItem()

		item_add_extension = gtk.MenuItem(label=_('Extension'))
		item_add_extension.connect('activate', self.__add_to_template, 'E')

		item_add_extension_part = gtk.MenuItem(label=_('Part of extension'))
		item_add_extension_part.connect('activate', self.__add_range_to_template, 'E')

		item_separator2 = gtk.SeparatorMenuItem()

		item_add_counter = gtk.MenuItem(label=_('Counter'))
		item_add_counter.connect('activate', self.__add_to_template, 'C')

		self._add_menu.append(item_add_name)
		self._add_menu.append(item_add_name_part)
		self._add_menu.append(item_separator1)
		self._add_menu.append(item_add_extension)
		self._add_menu.append(item_add_extension_part)
		self._add_menu.append(item_separator2)
		self._add_menu.append(item_add_counter)

		self._add_menu.show_all()

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
		self.vbox.remove(self._checkbox_active)
		vbox_left.pack_start(self._checkbox_active, False, False, 0)

		# pack interface
		table_counter.attach(label_start, 0, 1, 0, 1)
		table_counter.attach(self._entry_start, 0, 1, 1, 2, xoptions=gtk.EXPAND|gtk.FILL)
		table_counter.attach(label_step, 1, 2, 0, 1)
		table_counter.attach(self._entry_step, 1, 2, 1, 2, xoptions=gtk.EXPAND|gtk.FILL)
		table_counter.attach(label_digits, 2, 3, 0, 1)
		table_counter.attach(self._entry_digits, 2, 3, 1, 2, xoptions=gtk.EXPAND|gtk.FILL)

		frame_counter.add(table_counter)

		hbox_template.pack_start(self._entry_template, True, True, 0)
		hbox_template.pack_start(button_add, False, False, 0)

		vbox_template.pack_start(label_template, False, False, 0)
		vbox_template.pack_start(hbox_template, False, False, 0)

		vbox_left.pack_start(vbox_template, False, False, 0)
		vbox_left.pack_start(frame_counter, False, False, 0)

		vbox_right.pack_start(label_help, True, True, 0)

		hbox.pack_start(vbox_left, True, True, 0)
		hbox.pack_start(vbox_right, True, True, 0)

		self.vbox.pack_start(hbox, True, True, 0)

		self.vbox.show_all()

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

	def __button_add_clicked(self, widget, data=None):
		"""Handle clicking on add button"""
		self._add_menu.popup(
						None, None,
						self.__get_menu_position,
						1, 0, widget
					)

	def __get_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent.window, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def __add_to_template(self, widget, type):
		"""Add variable to template"""
		position = self._entry_template.get_property('cursor-position')
		self._entry_template.insert_text('[{0}]'.format(type), position)

		# update parent list
		self._template = self._entry_template.get_text()
		self._update_parent_list()

	def __add_range_to_template(self, widget, type):
		"""Add variable range to template"""
		if len(self._parent._list) > 0:
			# get selection from parent list
			selection = self._parent._names.get_selection()
			list_, iter_ = selection.get_selected()

			# ensure we have something to select
			if iter_ is None:
				iter_ = list_.get_iter_first()

			# get text for range selection and position of cursor in template
			name, extension = os.path.splitext(list_.get_value(iter_, RenameColumn.OLD_NAME))
			text = name if type == 'N' else extension
			position = self._entry_template.get_property('cursor-position')

			# get response from user
			dialog = InputRangeDialog(self._parent._application, text)
			code, range = dialog.get_response()

			if code == gtk.RESPONSE_OK:
				# user confirmed range selection, proceed

				if len(range) == 2:
					# get range from dialog
					start = range[0]
					end = range[1]

				else:
					# make sure we have range
					start = 0
					end = len(text)

				# insert text
				self._entry_template.insert_text('[{0}{1}-{2}]'.format(type, start, end), position)

				# update parent list
				self._template = self._entry_template.get_text()
				self._update_parent_list()

		else:
			# list is empty, notify user
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_INFO,
									gtk.BUTTONS_OK,
									_(
										'Item list is empty. Unable to get '
										'item for range selection!'
									)
								)
			dialog.run()
			dialog.destroy()

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
