from __future__ import absolute_import

import re
import os

from gi.repository import Gtk, Gdk
from sunflower.plugin_base.rename_extension import RenameExtension
from sunflower.gui.input_dialog import InputRangeDialog
from sunflower.tools.advanced_rename import Column as RenameColumn


class DefaultRename(RenameExtension):
	"""Default rename extension support"""

	def __init__(self, parent):
		RenameExtension.__init__(self, parent)

		# default option needs to be active by default
		self._checkbox_active.set_active(True)

		# create expressions
		self._regexp_name = re.compile(r'\[(N|E|C)([\d][^-]*)?-?([\d][^\]]*)?\]', re.I | re.U)

		self._template = '[N][E]'
		self._counter = 0
		self._counter_start = 0
		self._counter_step = 1
		self._counter_digits = 1

		# create user interface
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 15)

		vbox_left = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		vbox_right = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)

		# help
		label_help = Gtk.Label()
		label_help.set_xalign(0)
		label_help.set_yalign(0)
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
		vbox_template = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		hbox_template = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 2)

		label_template = Gtk.Label(label=_('Template:'))
		label_template.set_xalign(0)
		label_template.set_yalign(0.5)

		self._entry_template = Gtk.Entry()
		self._entry_template.set_text(self._template)
		self._entry_template.connect('changed', self.__template_changed)

		# style = Gtk.RcStyle()
		# style.xthickness = 0
		# style.ythickness = 0

		image_add = Gtk.Image()
		if Gtk.get_major_version() == 3:
			image_add.set_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON)

		else:
			image_add.set_from_icon_name('list-add-symbolic')
		button_add = Gtk.Button()
		if Gtk.get_major_version() == 3:
			button_add.set_image(image_add)

		else:
			button_add.set_child(image_add)
		# button_add.modify_style(style)
		button_add.connect('clicked', self.__button_add_clicked)

		# create popup menu
		if Gtk.get_major_version() == 3:
			self._add_menu = Gtk.Menu()

			item_add_name = Gtk.MenuItem(label=_('Name'))
			item_add_name.connect('activate', self.__add_to_template, 'N')

			item_add_name_part = Gtk.MenuItem(label=_('Part of name'))
			item_add_name_part.connect('activate', self.__add_range_to_template, 'N')

			item_separator1 = Gtk.SeparatorMenuItem()

			item_add_extension = Gtk.MenuItem(label=_('Extension'))
			item_add_extension.connect('activate', self.__add_to_template, 'E')

			item_add_extension_part = Gtk.MenuItem(label=_('Part of extension'))
			item_add_extension_part.connect('activate', self.__add_range_to_template, 'E')

			item_separator2 = Gtk.SeparatorMenuItem()

			item_add_counter = Gtk.MenuItem(label=_('Counter'))
			item_add_counter.connect('activate', self.__add_to_template, 'C')

			self._add_menu.append(item_add_name)
			self._add_menu.append(item_add_name_part)
			self._add_menu.append(item_separator1)
			self._add_menu.append(item_add_extension)
			self._add_menu.append(item_add_extension_part)
			self._add_menu.append(item_separator2)
			self._add_menu.append(item_add_counter)

			self._add_menu.show_all()

		else:
			# GTK 4 removed menus, a popover with buttons offers same options
			menu_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

			for label, callback, data in (
						(_('Name'), self.__add_to_template, 'N'),
						(_('Part of name'), self.__add_range_to_template, 'N'),
						(None, None, None),
						(_('Extension'), self.__add_to_template, 'E'),
						(_('Part of extension'), self.__add_range_to_template, 'E'),
						(None, None, None),
						(_('Counter'), self.__add_to_template, 'C'),
					):
				if label is None:
					menu_box.append(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL))
					continue

				button = Gtk.Button.new_with_label(label)
				button.get_style_context().add_class('flat')
				button.get_child().set_xalign(0)
				button.connect('clicked', self.__handle_popover_option, callback, data)
				menu_box.append(button)

			self._add_menu = Gtk.Popover.new()
			self._add_menu.set_child(menu_box)

		# counter
		frame_counter = Gtk.Frame(label=_('Counter'))

		table_counter = Gtk.Grid.new()
		set_border_width(table_counter, 5)
		table_counter.set_column_spacing(5)

		label_start = Gtk.Label(label=_('Start:'))
		label_start.set_xalign(0)
		label_start.set_yalign(0.5)

		adjustment = Gtk.Adjustment.new(0, 0, 10**10, 1, 10, 0)
		self._entry_start = Gtk.SpinButton.new(adjustment, 0, 0)
		self._entry_start.connect('value-changed', self.__counter_changed)

		label_step = Gtk.Label(label=_('Step:'))
		label_step.set_xalign(0)
		label_step.set_yalign(0.5)

		adjustment = Gtk.Adjustment.new(1, 1, 10**10, 1, 10, 0)
		self._entry_step = Gtk.SpinButton.new(adjustment, 0, 0)
		self._entry_step.connect('value-changed', self.__counter_changed)

		label_digits = Gtk.Label(label=_('Digits:'))
		label_digits.set_xalign(0)
		label_digits.set_yalign(0.5)

		adjustment = Gtk.Adjustment.new(1, 1, 20, 1, 5, 0)
		self._entry_digits = Gtk.SpinButton.new(adjustment, 0, 0)
		self._entry_digits.connect('value-changed', self.__counter_changed)

		# repack 'active' check box
		self.vbox.remove(self._checkbox_active)
		if Gtk.get_major_version() == 3:
			vbox_left.pack_start(self._checkbox_active, False, False, 0)

		else:
			vbox_left.append(self._checkbox_active)

		# pack interface
		table_counter.attach(label_start, 0, 0, 1, 1)
		self._entry_start.set_hexpand(True)
		table_counter.attach(self._entry_start, 0, 1, 1, 1)
		table_counter.attach(label_step, 1, 0, 1, 1)
		self._entry_step.set_hexpand(True)
		table_counter.attach(self._entry_step, 1, 1, 1, 1)
		table_counter.attach(label_digits, 2, 0, 1, 1)
		self._entry_digits.set_hexpand(True)
		table_counter.attach(self._entry_digits, 2, 1, 1, 1)

		if Gtk.get_major_version() == 3:
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

		else:
			frame_counter.set_child(table_counter)

			self._entry_template.set_hexpand(True)
			hbox_template.append(self._entry_template)
			hbox_template.append(button_add)

			vbox_template.append(label_template)
			vbox_template.append(hbox_template)

			vbox_left.append(vbox_template)
			vbox_left.append(frame_counter)

			label_help.set_vexpand(True)
			vbox_right.append(label_help)

			vbox_left.set_hexpand(True)
			hbox.append(vbox_left)
			vbox_right.set_hexpand(True)
			hbox.append(vbox_right)

			hbox.set_vexpand(True)
			self.vbox.append(hbox)

			self.vbox.show()

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
		if Gtk.get_major_version() == 3:
			self._add_menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

		else:
			if self._add_menu.get_parent() is not widget:
				if self._add_menu.get_parent() is not None:
					self._add_menu.unparent()
				self._add_menu.set_parent(widget)
			self._add_menu.popup()

	def __handle_popover_option(self, widget, callback, data):
		"""Close popover and run selected option. (GTK 4)"""
		self._add_menu.popdown()
		callback(widget, data)

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

			if code == Gtk.ResponseType.OK:
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
			dialog = Gtk.MessageDialog(
									transient_for=self._parent,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.INFO,
									buttons=Gtk.ButtonsType.OK,
									text=_(
										'Item list is empty. Unable to get '
										'item for range selection!'
									)
								)
			run_dialog(dialog)
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
