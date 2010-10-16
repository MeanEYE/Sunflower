#!/usr/bin/env python

import os
import gtk
import fnmatch

class InputDialog(gtk.Dialog):
	"""Simple input dialog

	This class can be extended with additional custom controls
	by accessing localy stored objects. Initially this dialog
	contains single label and text entry, along with two buttons.

	"""

	def __init__(self, application):
		gtk.Dialog.__init__(self, parent=application)

		self._application = application

		self.set_default_size(340, 10)
		self.set_resizable(True)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(application)

		self.vbox.set_spacing(0)

		vbox = gtk.VBox(False, 0)
		vbox.set_border_width(5)

		# create interface
		self._label = gtk.Label('Label')
		self._label.set_alignment(0, 0.5)

		self._entry = gtk.Entry()
		self._entry.connect('activate', self._confirm_entry)

		button_ok = gtk.Button(stock=gtk.STOCK_OK)
		button_ok.connect('clicked', self._confirm_entry)
		button_ok.set_can_default(True)

		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

		# pack interface
		vbox.pack_start(self._label, False, False, 0)
		vbox.pack_start(self._entry, False, False, 0)

		self.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)
		self.action_area.pack_end(button_ok, False, False, 0)
		self.set_default_response(gtk.RESPONSE_OK)

		self.vbox.pack_start(vbox, True, True, 0)
		self.show_all()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry.get_text() != '':
			self.response(gtk.RESPONSE_OK)

	def set_label(self, label_text):
		"""Provide an easy way to set label text"""
		self._label.set_text(label_text)
		
	def set_text(self, entry_text):
		"""Set main entry text"""
		self._entry.set_text(entry_text)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tupple with response code and
		input text.

		"""
		code = self.run()
		result = self._entry.get_text()

		self.destroy()

		return (code, result)


class CreateDialog(InputDialog):
	"""Generic create file/directory dialog"""

	def __init__(self, application):
		InputDialog.__init__(self, application)

		self._updating = False
		self._mode = 0644

		self.vbox.set_spacing(0)
		# create advanced options expander
		expander = gtk.Expander('Advanced options')
		expander.connect('activate', self._expander_event)
		expander.set_border_width(5)

		self._advanced = gtk.VBox(False, 5)
		self._advanced.set_border_width(5)

		table = gtk.Table(4, 4, False)

		# create widgets
		label = gtk.Label("User:")
		label.set_alignment(0, 0.5)
		table.attach(label, 0, 1, 0, 1)

		label = gtk.Label("Group:")
		label.set_alignment(0, 0.5)
		table.attach(label, 0, 1, 1, 2)

		label = gtk.Label("Others:")
		label.set_alignment(0, 0.5)
		table.attach(label, 0, 1, 2, 3)

		# owner checkboxes
		self._owner_read = gtk.CheckButton('Read')
		self._owner_read.connect('toggled', self._update_octal, (1 << 2) * 100)
		table.attach(self._owner_read, 1, 2, 0, 1)

		self._owner_write = gtk.CheckButton('Write')
		self._owner_write.connect('toggled', self._update_octal, (1 << 1) * 100)
		table.attach(self._owner_write, 2, 3, 0, 1)

		self._owner_execute = gtk.CheckButton('Execute')
		self._owner_execute.connect('toggled', self._update_octal, (1 << 0) * 100)
		table.attach(self._owner_execute, 3, 4, 0, 1)

		# group checkboxes
		self._group_read = gtk.CheckButton('Read')
		self._group_read.connect('toggled', self._update_octal, (1 << 2) * 10)
		table.attach(self._group_read, 1, 2, 1, 2)

		self._group_write = gtk.CheckButton('Write')
		self._group_write.connect('toggled', self._update_octal, (1 << 1) * 10)
		table.attach(self._group_write, 2, 3, 1, 2)

		self._group_execute = gtk.CheckButton('Execute')
		self._group_execute.connect('toggled', self._update_octal, (1 << 0) * 10)
		table.attach(self._group_execute, 3, 4, 1, 2)

		# others checkboxes
		self._others_read = gtk.CheckButton('Read')
		self._others_read.connect('toggled', self._update_octal, (1 << 2))
		table.attach(self._others_read, 1, 2, 2, 3)

		self._others_write = gtk.CheckButton('Write')
		self._others_write.connect('toggled', self._update_octal, (1 << 1))
		table.attach(self._others_write, 2, 3, 2, 3)

		self._others_execute = gtk.CheckButton('Execute')
		self._others_execute.connect('toggled', self._update_octal, (1 << 0))
		table.attach(self._others_execute, 3, 4, 2, 3)

		# octal representation
		label = gtk.Label("Octal:")
		label.set_alignment(0, 0.5)
		table.attach(label, 0, 1, 3, 4)

		self._octal_entry = gtk.Entry(4)
		self._octal_entry.set_width_chars(5)
		self._octal_entry.connect('activate', self._entry_activate)
		table.attach(self._octal_entry, 1, 2, 3, 4)
		table.set_row_spacing(2, 10)

		# pack interface
		self._advanced.pack_start(table, False, False, 0)
		expander.add(self._advanced)
		self.vbox.pack_start(expander, False, False, 0)

		# disable advanced options on windows
		sensitive = os.name not in ('nt',)
		expander.set_sensitive(sensitive)

		self.update_mode()
		expander.show_all()
		
	def _entry_activate(self, widget, data=None):
		"""Handle octal mode change"""
		self._mode = int(widget.get_text(), 8) 
		self.update_mode()

	def _update_octal(self, widget, data=None):
		"""Update octal entry box"""
		if self._updating: return

		data = int(str(data), 8)
		self._mode += (-1, 1)[widget.get_active()] * data
		
		self.update_mode()

	def _update_checkboxes(self, widget=None, data=None):
		"""Update checkboxes accordingly"""
		self._updating = True
		self._owner_read.set_active(self._mode & 0b100000000)
		self._owner_write.set_active(self._mode & 0b010000000)
		self._owner_execute.set_active(self._mode & 0b001000000)
		self._group_read.set_active(self._mode & 0b000100000)
		self._group_write.set_active(self._mode & 0b000010000)
		self._group_execute.set_active(self._mode & 0b000001000)
		self._others_read.set_active(self._mode & 0b000000100)
		self._others_write.set_active(self._mode & 0b000000010)
		self._others_execute.set_active(self._mode & 0b000000001)
		self._updating = False

	def _expander_event(self, widget, data=None):
		"""Return dialog size back to normal"""
		if widget.get_expanded():
			self.resize(340, 100)

	def get_mode(self):
		"""Returns default directory/file creation mode"""
		return self._mode
	
	def set_mode(self, mode):
		"""Set directory/file creation mode"""
		self._mode = mode
		self.update_mode()

	def update_mode(self):
		"""Update widgets"""
		self._octal_entry.set_text('{0}'.format(oct(self._mode)))
		self._update_checkboxes()


class FileCreateDialog(CreateDialog):
	
	def __init__(self, application):
		CreateDialog.__init__(self, application)

		self.set_title('Create empty file')
		self.set_label('Enter new file name:')
		
		
class DirectoryCreateDialog(CreateDialog):
	
	def __init__(self, application):
		CreateDialog.__init__(self, application)

		self.set_title('Create directory')
		self.set_label('Enter new directory name:')
		self.set_mode(0755)
		

class CopyDialog(gtk.Dialog):
	"""Dialog which will ask user for additional options before copying"""
	
	_title = "Copy item(s)"
	_operation_label = "Copy <b>{0}</b> item(s) to:"
	
	def __init__(self, application, provider, path):
		gtk.Dialog.__init__(self, parent=application)

		self._application = application
		self._provider = provider

		self.set_title(self._title)
		self.set_default_size(340, 10)
		self.set_resizable(True)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(application)

		self.vbox.set_spacing(0)
		
		# create additional UI
		vbox = gtk.VBox(False, 0)
		vbox.set_border_width(5)

		self.label_destination = gtk.Label()
		self.label_destination.set_alignment(0, 0.5)
		self.label_destination.set_use_markup(True)
		self._update_label()
		
		self.entry_destination = gtk.Entry()
		self.entry_destination.set_text(path)
		self.entry_destination.connect('activate', self._confirm_entry)
		
		# additional options
		advanced = gtk.Frame('<span size="small">Advanced options</span>')
		advanced.set_label_align(1, 0.5)
		label_advanced = advanced.get_label_widget()
		label_advanced.set_use_markup(True)

		vbox2 = gtk.VBox(False, 0)
		vbox2.set_border_width(5)
		
		label_type = gtk.Label("Only files of this type:")
		label_type.set_alignment(0, 0.5)
		
		self.entry_type = gtk.Entry()
		self.entry_type.set_text('*')
		self.entry_type.connect('activate', self._update_label)
		
		self.checkbox_owner = gtk.CheckButton('Set owner on destination')
		self.checkbox_mode = gtk.CheckButton('Set access mode on destination')
		
		self._create_buttons()
		
		# pack UI
		advanced.add(vbox2)
		
		vbox2.pack_start(label_type, False, False, 0)
		vbox2.pack_start(self.entry_type, False, False, 0)
		vbox2.pack_start(self.checkbox_owner, False, False, 0)
		vbox2.pack_start(self.checkbox_mode, False, False, 0)
		
		vbox.pack_start(self.label_destination, False, False, 0)
		vbox.pack_start(self.entry_destination, False, False, 0)
		vbox.pack_start(advanced, False, False, 5)
		
		self.vbox.pack_start(vbox, True, True, 0)

		self.set_default_response(gtk.RESPONSE_OK)
		self.show_all()
		
	def _create_buttons(self):
		"""Create action buttons"""
		button_cancel = gtk.Button('Cancel')
		button_copy = gtk.Button("Copy")
		button_copy.set_flags(gtk.CAN_DEFAULT)

		self.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)
		self.add_action_widget(button_copy, gtk.RESPONSE_OK)

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self.entry_destination.get_text() != '':
			self.response(gtk.RESPONSE_OK)
		
	def _get_item_count(self):
		"""Count number of items to copy"""
		list = self._provider.get_selection() 
		result = len(list)
		
		if hasattr(self, 'entry_type'):
			matches = fnmatch.filter(list, self.entry_type.get_text())
			result = len(matches)
				
		return result
	
	def _update_label(self, widget=None, data=None):
		"""Update label based on file type and selection"""
		self.label_destination.set_markup(self._operation_label.format(self._get_item_count()))

	def get_response(self):
		"""Return value and self-destruct

		This method returns tupple with response code and
		dictionary with other selected options.

		"""
		code = self.run()
		options = (
				self.entry_type.get_text(), 
				self.entry_destination.get_text(),
				self.checkbox_owner.get_active(),
				self.checkbox_mode.get_active()
				)

		self.destroy()

		return (code, options)
	

class MoveDialog(CopyDialog):
	"""Dialog which will ask user for additional options before moving"""
	
	_title = "Move item(s)"
	_operation_label = "Move <b>{0}</b> item(s) to:"
	
	def _create_buttons(self):
		"""Create action buttons"""
		button_cancel = gtk.Button('Cancel')
		button_move = gtk.Button("Move")
		button_move.set_flags(gtk.CAN_DEFAULT)

		self.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)
		self.add_action_widget(button_move, gtk.RESPONSE_OK)
		
		
class RenameDialog(InputDialog):
	"""Dialog used for renaming file/directory"""
	
	def __init__(self, application, selection):
		InputDialog.__init__(self, application)
		
		self.set_title('Rename file/directory')
		self.set_label('Enter a new name for this item:')
		self.set_text(selection)
		
		self._entry.select_region(0, len(os.path.splitext(selection)[0]))
				
		
class OverwriteDialog(gtk.Dialog):
	"""Dialog used for confirmation of file/directory overwrite"""
	
	def __init__(self, application):
		gtk.Dialog.__init__(self, parent=application)

		self._application = application

		self.set_default_size(400, 10)
		self.set_resizable(True)
		self.set_skip_taskbar_hint(True)
		self.set_modal(False)
		self.set_transient_for(application)

		self.vbox.set_spacing(0)

		hbox = gtk.HBox(False, 10)
		hbox.set_border_width(10)
		
		vbox = gtk.VBox(False, 10)
		vbox_icon = gtk.VBox(False, 0)
		
		# create interface
		icon = gtk.Image()
		icon.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
		
		self._label_title = gtk.Label()
		self._label_title.set_use_markup(True)
		self._label_title.set_alignment(0, 0.5)
		self._label_title.set_line_wrap(True)
		
		self._label_message = gtk.Label()
		self._label_message.set_alignment(0, 0.5)
		self._label_message.set_line_wrap(True)
		
		# inner hbox for original file
		hbox_original = gtk.HBox(False, 0)
		
		self._icon_original = gtk.Image()
		self._label_original = gtk.Label()
		self._label_original.set_use_markup(True)
		self._label_original.set_alignment(0, 0.5)
		
		# inner hbox for source file
		hbox_source = gtk.HBox(False, 0)
		
		self._icon_source = gtk.Image()
		self._label_source = gtk.Label()
		self._label_source.set_use_markup(True)
		self._label_source.set_alignment(0, 0.5)
		
		# rename expander
		expander = gtk.Expander(label='Select a new name for the destination')
		hbox_rename = gtk.HBox(False, 10)
		
		self._entry_rename = gtk.Entry()
		button_reset = gtk.Button('Reset')
		
		# apply to all checkbox
		self._apply_to_all = gtk.CheckButton('Apply this action to all files')
		
		# pack interface
		vbox_icon.pack_start(icon, False, False, 0)
		
		hbox_original.pack_start(self._icon_original, False, False, 10)
		hbox_original.pack_start(self._label_original, True, True, 0)
		
		hbox_source.pack_start(self._icon_source, False, False, 10)
		hbox_source.pack_start(self._label_source, True, True, 0)
		
		expander.add(hbox_rename)
		
		hbox_rename.pack_start(self._entry_rename, False, False, 0)
		hbox_rename.pack_start(button_reset, False, False, 0)
		
		vbox.pack_start(self._label_title, False, False, 0)
		vbox.pack_start(self._label_message, False, False, 0)
		vbox.pack_start(hbox_original, False, False, 0)
		vbox.pack_start(hbox_source, False, False, 0)
		vbox.pack_start(expander, False, False, 0)
		vbox.pack_start(self._apply_to_all, False, False, 0)
		
		hbox.pack_start(vbox_icon, False, False, 0)
		hbox.pack_start(vbox, True, True, 0)
		
		self.vbox.pack_start(hbox, True, True, 0)
		
		self._create_buttons()
		self.show_all()

	def _create_buttons(self):
		"""Create basic buttons"""
		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
		button_skip = gtk.Button(label="Skip")
		
		self.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)
		self.add_action_widget(button_skip, gtk.RESPONSE_NO)
		
	def set_title_element(self, element):
		"""Set title label with appropriate formatting"""
		pass
	
	def set_message_element(self, element):
		"""Set message element"""
		pass
	
	def set_original(self, provider, path):
		"""Set original element data"""
		icon = self._application.icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_DIALOG)
		self._icon_original.set_from_pixbuf(icon)
		
		self._label_original.set_markup(
									'<b>Original file</b>\n'
									'<i>Size:</i>\t\t{0}\n'
									'<i>Modified:</i>\t{1}'
								)
	
	def set_source(self, provider, path):
		"""Set source element data"""
		icon = self._application.icon_manager.get_icon_for_file(path, gtk.ICON_SIZE_DIALOG)
		self._icon_source.set_from_pixbuf(icon)

		self._label_source.set_markup(
									'<b>Replace with</b>\n'
									'<i>Size:</i>\t\t{0}\n'
									'<i>Modified:</i>\t{1}'
								)
	
		
class OverwriteFileDialog(OverwriteDialog):
	
	def __init__(self, application):
		OverwriteDialog.__init__(self, application)
		
		self.set_title('File conflict')
		
	def _create_buttons(self):
		"""Create dialog specific button"""
		button_replace = gtk.Button(label="Replace")
		button_replace.set_can_default(True)
		
		OverwriteDialog._create_buttons(self)
		self.add_action_widget(button_replace, gtk.RESPONSE_YES)
		
		self.set_default_response(gtk.RESPONSE_YES)
		
	def set_title_element(self, element):
		"""Set title label with appropriate formatting"""
		self._label_title.set_markup(
							'<span size="large" weight="bold">'
							'Replace file "{0}"?</span>'.format(element)
							)
		
	def set_message_element(self, element):
		"""Set message element"""
		self._label_message.set_text(
							'Another file with the same name already exists in'
							'"{0}". Replacing it will overwrite its content.'.format(element)
							)
