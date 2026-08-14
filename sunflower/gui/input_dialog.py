from __future__ import absolute_import

import os
import time
import locale
import fnmatch

from gi.repository import Gtk
from sunflower.plugin_base.provider import FileType, Support as ProviderSupport
from sunflower.common import get_user_directory, decode_file_name, UserDirectory
from sunflower.widgets.completion_entry import PathCompletionEntry
from sunflower.queue import OperationQueue


# constants
class OverwriteOption:
	RENAME = 0
	NEW_NAME = 1
	APPLY_TO_ALL = 2

class InputDialog:
	"""Simple input dialog

	This class can be extended with additional custom controls
	by accessing locally stored objects. Initially this dialog
	contains single label and text entry, along with two buttons.

	"""

	def __init__(self, application):
		self._dialog = Gtk.MessageDialog(transient_for=application)

		self._application = application

		self._dialog.set_default_size(400, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		# remove existing children
		self._container = self._dialog.get_message_area()
		if Gtk.get_major_version() == 3:
			self._container.foreach(lambda widget: self._container.remove(widget))

		else:
			child = self._container.get_first_child()
			while child is not None:
				next_child = child.get_next_sibling()
				self._container.remove(child)
				child = next_child

		# create interface
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		self._label = Gtk.Label(label='Label')
		self._label.set_xalign(0)
		self._label.set_yalign(0.5)

		self._entry = Gtk.Entry()
		self._entry.connect('activate', self._confirm_entry)

		self._button_positive = Gtk.Button.new_with_label(_('OK'))
		self._button_positive.connect('clicked', self._confirm_entry)
		self._button_positive.get_style_context().add_class('suggested-action')
		if Gtk.get_major_version() == 3:
			self._button_positive.set_can_default(True)

		self._button_negative = Gtk.Button.new_with_label(_('Cancel'))

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox.pack_start(self._label, False, False, 0)
			vbox.pack_start(self._entry, False, False, 0)

		else:
			vbox.append(self._label)
			vbox.append(self._entry)

		if Gtk.get_major_version() == 3:
			self._dialog.get_message_area().pack_start(vbox, False, False, 0)

		else:
			self._dialog.get_message_area().append(vbox)

		self._dialog.add_action_widget(self._button_negative, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(self._button_positive, Gtk.ResponseType.OK)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry.get_text() != '':
			self._dialog.response(Gtk.ResponseType.OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def set_label(self, label_text):
		"""Provide an easy way to set label text"""
		self._label.set_text(label_text)

	def set_text(self, entry_text):
		"""Set main entry text"""
		self._entry.set_text(entry_text)

	def set_password(self):
		"""Set field as password input"""
		self._entry.set_property('caps-lock-warning', True)
		self._entry.set_visibility(False)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = run_dialog(self._dialog)
		result = self._entry.get_text()

		self._dialog.destroy()

		return code, result


class LinkDialog(InputDialog):
	"""Input dialog for creating symbolic or hard links"""

	def __init__(self, application):
		InputDialog.__init__(self, application)

		self.set_title(_('Create link'))
		self.set_label(_('Enter new link name:'))

		self._container.set_spacing(5)

		# create user interface
		vbox_original_path = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		hbox_original_path = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

		label_original_path = Gtk.Label(label=_('Original path:'))
		label_original_path.set_xalign(0)
		label_original_path.set_yalign(0.5)
		self._entry_original_path = Gtk.Entry()

		# create checkbox
		self._checkbox_hard_link = Gtk.CheckButton.new_with_label(_('Create hard link'))

		# create browse button
		button_browse = Gtk.Button.new_with_label(_('Browse'))
		button_browse.connect('clicked', self._browse_original_path)

		# pack interface
		if Gtk.get_major_version() == 3:
			hbox_original_path.pack_start(self._entry_original_path, True, True, 0)
			hbox_original_path.pack_start(button_browse, False, False, 0)

			vbox_original_path.pack_start(label_original_path, False, False, 0)
			vbox_original_path.pack_start(hbox_original_path, False, False, 0)

			self._container.pack_start(vbox_original_path, False, False, 0)
			self._container.pack_start(self._checkbox_hard_link, False, False, 0)

		else:
			self._entry_original_path.set_hexpand(True)
			hbox_original_path.append(self._entry_original_path)
			hbox_original_path.append(button_browse)

			vbox_original_path.append(label_original_path)
			vbox_original_path.append(hbox_original_path)

			self._container.append(vbox_original_path)
			self._container.append(self._checkbox_hard_link)

		# show all widgets
		if Gtk.get_major_version() == 3:
			self._container.show_all()

		else:
			self._container.show()

	def _browse_original_path(self, widget, data=None):
		"""Show file selection dialog"""
		dialog = Gtk.FileChooserDialog(
							title=_('Select original path'),
							parent=self._application,
							action=Gtk.FileChooserAction.OPEN,
							buttons=(
								Gtk.STOCK_CANCEL,
								Gtk.ResponseType.REJECT,
								Gtk.STOCK_OK,
								Gtk.ResponseType.ACCEPT
							)
						)
		response = run_dialog(dialog)

		if response == Gtk.ResponseType.ACCEPT:
			self._entry_original_path.set_text(dialog.get_filename())

			# if link name is empty, add original path name
			if self._entry.get_text() == '':
				self._entry.set_text(decode_file_name(os.path.basename(dialog.get_filename())))

		dialog.destroy()

	def set_original_path(self, path):
		"""Set original path where link point to"""
		if path is not None:
			self._entry_original_path.set_text(path)

	def set_hard_link(self, hard_link=True):
		"""Set hard link option state"""
		if self._checkbox_hard_link.is_sensitive():
			self._checkbox_hard_link.set_active(hard_link)

	def set_hard_link_supported(self, supported):
		"""Set checkbox state for hard link"""
		self._checkbox_hard_link.set_sensitive(supported)

	def get_response(self):
		"""Return value and self-destruct"""
		code = run_dialog(self._dialog)
		original_path = self._entry_original_path.get_text()
		link_name = self._entry.get_text()
		hard_link = self._checkbox_hard_link.get_active()

		self._dialog.destroy()

		return code, original_path, link_name, hard_link


class CreateDialog(InputDialog):
	"""Generic create file/directory dialog"""

	def __init__(self, application):
		InputDialog.__init__(self, application)

		self._permission_updating = False
		self._mode = 0o644
		self._dialog_size = None

		# create advanced options expander
		advanced_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		advanced_box.set_margin_top(10)
		if Gtk.get_major_version() == 3:
			self._container.pack_start(advanced_box, True, True, 0)

		else:
			advanced_box.set_vexpand(True)
			self._container.append(advanced_box)

		label = Gtk.Label.new(_('<b>Advanced options:</b>'))
		label.set_use_markup(True)
		label.set_xalign(0)
		label.set_yalign(0.5)
		if Gtk.get_major_version() == 3:
			advanced_box.pack_start(label, False, False, 0)

		else:
			advanced_box.append(label)

		table = Gtk.Grid.new()
		if Gtk.get_major_version() == 3:
			advanced_box.pack_start(table, True, True, 0)

		else:
			table.set_vexpand(True)
			advanced_box.append(table)

		# create widgets
		label = Gtk.Label(label=_('User:'))
		label.set_xalign(0)
		label.set_yalign(0.5)
		table.attach(label, 0, 0, 1, 1)

		label = Gtk.Label(label=_('Group:'))
		label.set_xalign(0)
		label.set_yalign(0.5)
		table.attach(label, 0, 1, 1, 1)

		label = Gtk.Label(label=_('Others:'))
		label.set_xalign(0)
		label.set_yalign(0.5)
		table.attach(label, 0, 2, 1, 1)

		# owner checkboxes
		self._permission_owner_read = Gtk.CheckButton.new_with_label(_('Read'))
		self._permission_owner_read.connect('toggled', self._update_octal, (1 << 2) * 100)
		table.attach(self._permission_owner_read, 1, 0, 1, 1)

		self._permission_owner_write = Gtk.CheckButton.new_with_label(_('Write'))
		self._permission_owner_write.connect('toggled', self._update_octal, (1 << 1) * 100)
		table.attach(self._permission_owner_write, 2, 0, 1, 1)

		self._permission_owner_execute = Gtk.CheckButton.new_with_label(_('Execute'))
		self._permission_owner_execute.connect('toggled', self._update_octal, (1 << 0) * 100)
		table.attach(self._permission_owner_execute, 3, 0, 1, 1)

		# group checkboxes
		self._permission_group_read = Gtk.CheckButton.new_with_label(_('Read'))
		self._permission_group_read.connect('toggled', self._update_octal, (1 << 2) * 10)
		table.attach(self._permission_group_read, 1, 1, 1, 1)

		self._permission_group_write = Gtk.CheckButton.new_with_label(_('Write'))
		self._permission_group_write.connect('toggled', self._update_octal, (1 << 1) * 10)
		table.attach(self._permission_group_write, 2, 1, 1, 1)

		self._permission_group_execute = Gtk.CheckButton.new_with_label(_('Execute'))
		self._permission_group_execute.connect('toggled', self._update_octal, (1 << 0) * 10)
		table.attach(self._permission_group_execute, 3, 1, 1, 1)

		# others checkboxes
		self._permission_others_read = Gtk.CheckButton.new_with_label(_('Read'))
		self._permission_others_read.connect('toggled', self._update_octal, (1 << 2))
		table.attach(self._permission_others_read, 1, 2, 1, 1)

		self._permission_others_write = Gtk.CheckButton.new_with_label(_('Write'))
		self._permission_others_write.connect('toggled', self._update_octal, (1 << 1))
		table.attach(self._permission_others_write, 2, 2, 1, 1)

		self._permission_others_execute = Gtk.CheckButton.new_with_label(_('Execute'))
		self._permission_others_execute.connect('toggled', self._update_octal, (1 << 0))
		table.attach(self._permission_others_execute, 3, 2, 1, 1)

		# octal representation
		label = Gtk.Label(label=_('Octal:'))
		label.set_xalign(0)
		label.set_yalign(0.5)
		table.attach(label, 0, 3, 1, 1)

		self._permission_octal_entry = Gtk.Entry()
		self._permission_octal_entry.set_width_chars(5)
		self._permission_octal_entry.connect('activate', self._entry_activate)
		table.attach(self._permission_octal_entry, 1, 3, 1, 1)
		table.set_row_spacing(10)

		# create button for saving default configuration
		if Gtk.get_major_version() == 3:
			button_save = Gtk.Button.new_from_icon_name('document-save-symbolic', Gtk.IconSize.BUTTON)

		else:
			button_save = Gtk.Button.new_from_icon_name('document-save-symbolic')
		button_save.connect('clicked', self._save_configuration)
		button_save.set_tooltip_text(_('Save as default configuration'))
		button_save.show()
		button_save.set_halign(Gtk.Align.END)

		table.attach(button_save, 3, 3, 1, 1)

		self._label.set_text('Test')

		# pack interface
		if Gtk.get_major_version() == 3:
			self._container.show_all()

		else:
			self._container.show()

	def _save_configuration(self, widget=None, data=None):
		"""Save default configuration for create dialog"""
		pass

	def _entry_activate(self, widget, data=None):
		"""Handle octal mode change"""
		self._mode = int(widget.get_text(), 8)
		self.update_mode()

	def _update_octal(self, widget, data=None):
		"""Update octal entry box"""
		if self._permission_updating: return

		data = int(str(data), 8)
		self._mode += (-1, 1)[widget.get_active()] * data

		self.update_mode()

	def _update_checkboxes(self, widget=None, data=None):
		"""Update checkboxes accordingly"""
		self._permission_updating = True
		self._permission_owner_read.set_active(self._mode & 0b100000000)
		self._permission_owner_write.set_active(self._mode & 0b010000000)
		self._permission_owner_execute.set_active(self._mode & 0b001000000)
		self._permission_group_read.set_active(self._mode & 0b000100000)
		self._permission_group_write.set_active(self._mode & 0b000010000)
		self._permission_group_execute.set_active(self._mode & 0b000001000)
		self._permission_others_read.set_active(self._mode & 0b000000100)
		self._permission_others_write.set_active(self._mode & 0b000000010)
		self._permission_others_execute.set_active(self._mode & 0b000000001)
		self._permission_updating = False

	def _expander_event(self, widget, data=None):
		"""Return dialog size back to normal"""
		if widget.get_expanded():
			self._dialog.set_size_request(1, 1)
			self._dialog.resize(*self._dialog_size)

		else:
			self._dialog_size = self._dialog.get_size()
			self._dialog.set_size_request(-1, -1)

	def get_mode(self):
		"""Returns default directory/file creation mode"""
		return self._mode

	def set_mode(self, mode):
		"""Set directory/file creation mode"""
		self._mode = mode
		self.update_mode()

	def update_mode(self):
		"""Update widgets"""
		self._permission_octal_entry.set_text('{0}'.format(oct(self._mode)))
		self._update_checkboxes()


class PasswordDialog(InputDialog):
	"""Dialog used for safe entry of passwords. Contains two fields."""

	def __init__(self, application):
		InputDialog.__init__(self, application)

		# create user interface
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		self._label_description = Gtk.Label()
		self._label_description.set_xalign(0)
		self._label_description.set_yalign(0)
		if Gtk.get_major_version() == 3:
			self._label_description.set_line_wrap(True)

		else:
			self._label_description.set_wrap(True)
		if Gtk.get_major_version() == 3:
			self._label_description.connect('size-allocate', self._adjust_label)

		self._label.set_text(_('Password:'))

		label_confirm = Gtk.Label(label=_('Confirm:'))
		label_confirm.set_xalign(0)
		label_confirm.set_yalign(0.5)
		self._entry_confirm = Gtk.Entry()

		self._entry.set_property('caps-lock-warning', True)
		self._entry_confirm.set_property('caps-lock-warning', True)
		self._entry.set_visibility(False)
		self._entry_confirm.set_visibility(False)

		# configure interface
		self._container.set_spacing(5)

		# pack user interface
		if Gtk.get_major_version() == 3:
			vbox.pack_start(label_confirm, False, False, 0)
			vbox.pack_start(self._entry_confirm, False, False, 0)

			self._container.pack_start(vbox, False, False, 0)
			self._container.pack_start(self._label_description, False, False, 0)

		else:
			vbox.append(label_confirm)
			vbox.append(self._entry_confirm)

			self._container.append(vbox)
			self._container.append(self._label_description)

		self._container.reorder_child(self._label_description, 0)

		# show all elements
		if Gtk.get_major_version() == 3:
			vbox.show_all()

		else:
			vbox.show()
		self._label_description.show()

	def _adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)

	def set_label(self, text):
		"""Set label text"""
		self._label_description.set_text(text)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code password
		and confirmation string.

		"""
		code = run_dialog(self._dialog)
		password = self._entry.get_text()
		confirmation = self._entry_confirm.get_text()

		self._dialog.destroy()

		return code, password, confirmation


class FileCreateDialog(CreateDialog):
	"""Dialog providing input of details for creating new file."""

	def __init__(self, application):
		CreateDialog.__init__(self, application)

		self.set_title(_('Create empty file'))
		self.set_label(_('Enter new file name:'))

		# create option to open file in editor
		self._checkbox_edit_after = Gtk.CheckButton.new_with_label(_('Open file in editor'))

		# create template list
		vbox_templates = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		label_templates = Gtk.Label.new(_('Template:'))
		label_templates.set_xalign(0)
		label_templates.set_yalign(0.5)

		self._templates = Gtk.ListStore(str, str, str)

		cell_icon = Gtk.CellRendererPixbuf()
		cell_name = Gtk.CellRendererText()

		# create template combobox
		self._template_list = Gtk.ComboBox.new_with_model(self._templates)
		self._template_list.set_row_separator_func(self._row_is_separator)
		self._template_list.connect('changed', self._template_changed)
		self._template_list.pack_start(cell_icon, False)
		self._template_list.pack_start(cell_name, True)

		self._template_list.add_attribute(cell_icon, 'icon-name', 2)
		self._template_list.add_attribute(cell_name, 'text', 0)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_templates.pack_start(label_templates, False, False, 0)
			vbox_templates.pack_start(self._template_list, False, False, 0)

			self._container.pack_start(self._checkbox_edit_after, False, False, 0)
			self._container.pack_start(vbox_templates, False, False, 0)

		else:
			vbox_templates.append(label_templates)
			vbox_templates.append(self._template_list)

			self._container.append(self._checkbox_edit_after)
			self._container.append(vbox_templates)

		self._container.reorder_child(self._checkbox_edit_after, 1)
		self._container.reorder_child(vbox_templates, 1)

		# populate template list
		self._populate_templates()

		# set options to previously stored values
		section = self._application.options.section('create_dialog')

		self.set_mode(section.get('file_mode'))
		self._checkbox_edit_after.set_active(section.get('edit_file'))

		# show all widgets
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _save_configuration(self, widget=None, data=None):
		"""Save default configuration for create dialog"""
		section = self._application.options.section('create_dialog')

		section.set('file_mode', self._mode)
		section.set('edit_file', self._checkbox_edit_after.get_active())

	def _populate_templates(self):
		"""Populate templates list"""
		self._templates.clear()

		# add items from templates directory
		directory = get_user_directory(UserDirectory.TEMPLATES)
		file_list = []

		if directory is not None:
			file_list = [file_ for file_ in os.listdir(directory) if file_[0] != '.']  # skip hidden files

		# add empty file
		self._templates.append((_('Empty File'), '', 'text-x-generic-template'))
		if len(file_list) > 0:
			self._templates.append(('', '', ''))  # separator

		for file_ in file_list:
			name = os.path.splitext(file_)[0]
			full_path = os.path.join(os.path.expanduser('~'), 'Templates', file_)
			icon_name = self._application.icon_manager.get_icon_for_file(full_path)

			self._templates.append((name, full_path, icon_name))

		# select default item
		self._template_list.set_active(0)

	def _row_is_separator(self, model, row, data=None):
		"""Determine if row being drawn is a separator"""
		return model.get_value(row, 0) == ''

	def _template_changed(self, widget, data=None):
		"""Handle changing template"""
		file_name = os.path.splitext(self._entry.get_text())
		active_item = self._template_list.get_active()

		# change extension only if specific template is selected
		if active_item > 0:
			extension = os.path.splitext(self._templates[active_item][1])[1]
			self._entry.set_text('{0}{1}'.format(file_name[0], extension))

	def get_edit_file(self):
		"""Get state of 'edit after creating' checkbox"""
		return self._checkbox_edit_after.get_active()

	def get_template_file(self):
		"""Return full path to template file

		In case when 'Empty File' is selected, return None

		"""
		result = None
		active_item = self._template_list.get_active()

		if active_item > 0:
			result = self._templates[active_item][1]

		return result


class DirectoryCreateDialog(CreateDialog):
	"""Simple dialog used for creating directories."""

	def __init__(self, application):
		CreateDialog.__init__(self, application)

		self.set_title(_('Create directory'))
		self.set_label(_('Enter new directory name:'))
		self.set_mode(self._application.options.section('create_dialog').get('directory_mode'))

	def _save_configuration(self, widget=None, data=None):
		"""Save default configuration for create dialog"""
		section = self._application.options.section('create_dialog')
		section.set('directory_mode', self._mode)


class DeleteDialog:
	"""Confirmation dialog for item removal with operation queue selection."""

	def __init__(self, application, message):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)

		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)
		self._dialog.set_default_size(-1, 0)

		# create user interface for operation queue
		label_message = Gtk.Label.new(message)
		label_message.set_xalign(0)
		label_message.set_yalign(0)
		label_message.set_use_markup(True)

		cell_name = Gtk.CellRendererText()
		self.combobox_queue = Gtk.ComboBox(model=OperationQueue.get_model())
		self.combobox_queue.pack_start(cell_name, True)
		self.combobox_queue.add_attribute(cell_name, 'text', OperationQueue.COLUMN_TEXT)
		self.combobox_queue.set_active(0)
		self.combobox_queue.set_row_separator_func(OperationQueue.handle_separator_check)
		self.combobox_queue.connect('changed', OperationQueue.handle_queue_select, self)

		# create controls
		button_yes = Gtk.Button.new_with_label(_('Yes'))
		if Gtk.get_major_version() == 3:
			button_yes.set_can_default(True)
		button_no = Gtk.Button.new_with_label(_('No'))

		if Gtk.get_major_version() == 3:
			button_queue = Gtk.Button.new_from_icon_name('go-bottom', Gtk.IconSize.BUTTON)

		else:
			button_queue = Gtk.Button.new_from_icon_name('go-bottom')
		button_queue.set_always_show_image(True)
		button_queue.set_label('None')

		content_area = self._dialog.get_content_area()
		set_border_width(content_area, 10)
		if Gtk.get_major_version() == 3:
			content_area.pack_start(label_message, True, True, 0)

		else:
			label_message.set_vexpand(True)
			content_area.append(label_message)

		self._dialog.add_action_widget(button_yes, Gtk.ResponseType.YES)
		self._dialog.add_action_widget(button_no, Gtk.ResponseType.CANCEL)
		self._dialog.set_default_response(Gtk.ResponseType.YES)
		self._dialog.get_header_bar().pack_end(button_queue)
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def get_response(self):
		"""Show dialog and get response code."""
		code = run_dialog(self._dialog)
		selected_iter = self.combobox_queue.get_active_iter()
		queue_name = OperationQueue.get_name_from_iter(selected_iter)

		self._dialog.destroy()

		return code, queue_name


class CopyDialog:
	"""Dialog which will ask user for additional options before copying"""

	def __init__(self, application, source_provider, destination_provider, path):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)

		self._application = application
		self._source_provider = source_provider
		self._destination_provider = destination_provider

		self._dialog_size = None
		self._dialog.set_default_size(500, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		# create additional components
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		set_border_width(vbox, 5)

		self.label_destination = Gtk.Label()
		self.label_destination.set_xalign(0)
		self.label_destination.set_yalign(0.5)
		self.label_destination.set_use_markup(True)

		self.entry_destination = Gtk.Entry()
		self.entry_destination.set_text(path)
		self.entry_destination.set_editable(False)
		self.entry_destination.connect('activate', self._confirm_entry)

		# additional options
		hbox_additional = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 10)
		separator_file_type = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
		vbox_type = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_queue = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_type = Gtk.Label(label=_('Only files of this type:'))
		label_type.set_xalign(0)
		label_type.set_yalign(0.5)

		self.entry_type = Gtk.Entry()
		self.entry_type.set_text('*')
		self.entry_type.connect('changed', self._update_label)

		label_queue = Gtk.Label(label=_('Operation queue:'))
		label_queue.set_xalign(0)
		label_queue.set_yalign(0.5)

		cell_name = Gtk.CellRendererText()

		self.combobox_queue = Gtk.ComboBox(model=OperationQueue.get_model())
		self.combobox_queue.pack_start(cell_name, True)
		self.combobox_queue.add_attribute(cell_name, 'text', OperationQueue.COLUMN_TEXT)
		self.combobox_queue.set_active(0)
		self.combobox_queue.set_row_separator_func(OperationQueue.handle_separator_check)
		self.combobox_queue.connect('changed', OperationQueue.handle_queue_select, self._dialog)
		self.combobox_queue.set_size_request(140, -1)

		# detailed item list
		separator_details = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
		list_container = Gtk.ScrolledWindow()
		list_container.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		if Gtk.get_major_version() == 3:
			list_container.set_shadow_type(Gtk.ShadowType.IN)

		else:
			list_container.set_has_frame(True)

		expand_details = Gtk.Expander()
		expand_details.set_label(_('Affected item list'))
		expand_details.connect('activate', self._handle_expand)

		self._affected = Gtk.ListStore(str, str)
		affected_list = Gtk.TreeView(model=self._affected)
		affected_list.set_size_request(-1, 200)
		affected_list.set_headers_visible(False)
		affected_list.set_search_column(1)
		affected_list.set_enable_search(True)

		cell_icon = Gtk.CellRendererPixbuf()
		cell_name = Gtk.CellRendererText()

		column_name = Gtk.TreeViewColumn()
		column_name.pack_start(cell_icon, False)
		column_name.pack_start(cell_name, True)
		column_name.add_attribute(cell_icon, 'icon-name', 0)
		column_name.add_attribute(cell_name, 'text', 1)
		column_name.set_expand(True)

		affected_list.append_column(column_name)

		# create operation options
		self.checkbox_owner = Gtk.CheckButton.new_with_label(_('Set owner on destination'))
		self.checkbox_mode = Gtk.CheckButton.new_with_label(_('Set access mode on destination'))
		self.checkbox_timestamp = Gtk.CheckButton.new_with_label(_('Set date and time on destination'))
		self.checkbox_silent = Gtk.CheckButton.new_with_label(_('Silent mode'))

		vbox_silent = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		vbox_silent.set_sensitive(False)

		self.checkbox_merge = Gtk.CheckButton.new_with_label(_('Merge directories'))
		self.checkbox_overwrite = Gtk.CheckButton.new_with_label(_('Overwrite files'))

		self.checkbox_silent.connect('toggled', self._toggled_silent_mode, vbox_silent)
		self.checkbox_silent.set_tooltip_text(_(
										'Silent mode will enable operation to finish '
										'without disturbing you. If any errors occur, '
										'they will be presented to you after completion.'
									))

		self.checkbox_symlink = Gtk.CheckButton.new_with_label(_('Follow symlinks'))

		self._create_buttons()

		# pack user interface
		if Gtk.get_major_version() == 3:
			list_container.add(affected_list)

		else:
			list_container.set_child(affected_list)
		if Gtk.get_major_version() == 3:
			expand_details.add(list_container)

		else:
			expand_details.set_child(list_container)

		if Gtk.get_major_version() == 3:
			vbox_silent.pack_start(self.checkbox_merge, False, False, 0)
			vbox_silent.pack_start(self.checkbox_overwrite, False, False, 0)

			vbox_type.pack_start(label_type, False, False, 0)
			vbox_type.pack_start(self.entry_type, False, False, 0)

			vbox_queue.pack_start(label_queue, False, False, 0)
			vbox_queue.pack_start(self.combobox_queue, False, False, 0)

			hbox_additional.pack_start(vbox_type, True, True, 0)
			hbox_additional.pack_start(vbox_queue, True, True, 0)

			vbox.pack_start(self.label_destination, False, False, 0)
			vbox.pack_start(self.entry_destination, False, False, 0)
			vbox.pack_start(separator_file_type, False, False, 5)
			vbox.pack_start(hbox_additional, False, False, 0)
			vbox.pack_start(expand_details, False, False, 0)
			vbox.pack_start(separator_details, False, False, 5)
			vbox.pack_start(self.checkbox_owner, False, False, 0)
			vbox.pack_start(self.checkbox_mode, False, False, 0)
			vbox.pack_start(self.checkbox_timestamp, False, False, 0)
			vbox.pack_start(self.checkbox_silent, False, False, 0)
			vbox.pack_start(vbox_silent, False, False, 0)
			vbox.pack_start(self.checkbox_symlink, False, False, 0)

		else:
			vbox_silent.append(self.checkbox_merge)
			vbox_silent.append(self.checkbox_overwrite)

			vbox_type.append(label_type)
			vbox_type.append(self.entry_type)

			vbox_queue.append(label_queue)
			vbox_queue.append(self.combobox_queue)

			vbox_type.set_hexpand(True)
			hbox_additional.append(vbox_type)
			vbox_queue.set_hexpand(True)
			hbox_additional.append(vbox_queue)

			vbox.append(self.label_destination)
			vbox.append(self.entry_destination)
			set_border_width(separator_file_type, 5)
			vbox.append(separator_file_type)
			vbox.append(hbox_additional)
			vbox.append(expand_details)
			set_border_width(separator_details, 5)
			vbox.append(separator_details)
			vbox.append(self.checkbox_owner)
			vbox.append(self.checkbox_mode)
			vbox.append(self.checkbox_timestamp)
			vbox.append(self.checkbox_silent)
			vbox.append(vbox_silent)
			vbox.append(self.checkbox_symlink)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(vbox, False, False, 0)

		else:
			self._dialog.get_content_area().append(vbox)

		# prepare dialog
		self._update_label()
		self._load_configuration()

		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# show all widgets
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _load_configuration(self):
		"""Load options from config file"""
		options = self._application.options.section('operations')

		# get options supported by providers
		source_support = self._source_provider.get_support()
		source_set_owner = ProviderSupport.SET_OWNER in source_support
		source_set_mode = ProviderSupport.SET_ACCESS in source_support
		source_set_timestamp = ProviderSupport.SET_TIMESTAMP in source_support
		source_symlink_support = ProviderSupport.SYMBOLIC_LINK in source_support

		if self._destination_provider is not None:
			destination_support = self._destination_provider.get_support()
			destination_set_owner = ProviderSupport.SET_OWNER in destination_support
			destination_set_mode = ProviderSupport.SET_ACCESS in destination_support
			destination_set_timestamp = ProviderSupport.SET_TIMESTAMP in destination_support
			destination_symlink_support = ProviderSupport.SYMBOLIC_LINK in source_support

		else:
			destination_set_owner = False
			destination_set_mode = False
			destination_set_timestamp = False
			destination_symlink_support = False

		provider_set_owner = source_set_owner and destination_set_owner
		provider_set_mode = source_set_mode and destination_set_mode
		provider_set_timestamp = source_set_timestamp and destination_set_timestamp
		symlinks_supported = source_symlink_support and destination_symlink_support

		# disable checkboxes that are not supported by provider
		if not provider_set_owner:
			self.checkbox_owner.set_sensitive(False)
			self.checkbox_owner.set_tooltip_text(_('Not supported by file system provider'))

		if not provider_set_mode:
			self.checkbox_mode.set_sensitive(False)
			self.checkbox_mode.set_tooltip_text(_('Not supported by file system provider'))

		if not provider_set_timestamp:
			self.checkbox_timestamp.set_sensitive(False)
			self.checkbox_timestamp.set_tooltip_text(_('Not supported by file system provider'))

		if not symlinks_supported:
			self.checkbox_symlink.set_sensitive(False)
			self.checkbox_symlink.set_tooltip_text(_('Not supported by file system provider'))

		# set checkbox states
		self.checkbox_owner.set_active(options.get('set_owner') and provider_set_owner)
		self.checkbox_mode.set_active(options.get('set_mode') and provider_set_mode)
		self.checkbox_timestamp.set_active(options.get('set_timestamp') and provider_set_timestamp)
		self.checkbox_silent.set_active(options.get('silent'))
		self.checkbox_merge.set_active(options.get('merge_in_silent'))
		self.checkbox_overwrite.set_active(options.get('overwrite_in_silent'))
		self.checkbox_symlink.set_active(options.get('follow_symlink'))

	def _save_configuration(self, widget=None, data=None):
		"""Save default dialog configuration"""
		options = self._application.options.section('operations')

		# get options supported by providers
		source_support = self._source_provider.get_support()
		source_set_owner = ProviderSupport.SET_OWNER in source_support
		source_set_mode = ProviderSupport.SET_ACCESS in source_support
		source_set_timestamp = ProviderSupport.SET_TIMESTAMP in source_support
		source_symlink = ProviderSupport.SYMBOLIC_LINK in source_support

		if self._destination_provider is not None:
			destination_support = self._destination_provider.get_support()
			destination_set_owner = ProviderSupport.SET_OWNER in destination_support
			destination_set_mode = ProviderSupport.SET_ACCESS in destination_support
			destination_set_timestamp = ProviderSupport.SET_TIMESTAMP in destination_support
			destination_symlink = ProviderSupport.SYMBOLIC_LINK in source_support

		else:
			destination_set_owner = False
			destination_set_mode = False
			destination_set_timestamp = False
			destination_symlink = False

		provider_set_owner = source_set_owner and destination_set_owner
		provider_set_mode = source_set_mode and destination_set_mode
		provider_set_timestamp = source_set_timestamp and destination_set_timestamp
		provider_symlink = source_symlink and destination_symlink

		# only save options supported by provider
		if provider_set_owner:
			options.set('set_owner', self.checkbox_owner.get_active())

		if provider_set_mode:
			options.set('set_mode', self.checkbox_mode.get_active())

		if provider_set_timestamp:
			options.set('set_timestamp', self.checkbox_timestamp.get_active())

		if provider_symlink:
			options.set('follow_symlink', self.checkbox_symlink.get_active())

		options.set('silent', self.checkbox_silent.get_active())
		options.set('merge_in_silent', self.checkbox_merge.get_active())
		options.set('overwrite_in_silent', self.checkbox_overwrite.get_active())

		# show message letting user know
		if not (provider_set_owner and provider_set_mode and provider_set_timestamp and provider_symlink):
			dialog = Gtk.MessageDialog(
									transient_for=self._dialog,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.INFO,
									buttons=Gtk.ButtonsType.OK,
									text=_(
										'Only options supported by file '
										'system providers were saved.'
									)
								)
			run_dialog(dialog)
			dialog.destroy()

	def _toggled_silent_mode(self, widget, container):
		"""Set container sensitivity based on widget status"""
		container.set_sensitive(widget.get_active())

	def _handle_expand(self, widget, data=None):
		"""Handle expanding and collapsing affected list."""
		if widget.get_expanded():
			self._dialog.set_size_request(1, 1)
			self._dialog.resize(*self._dialog_size)

		else:
			self._dialog_size = self._dialog.get_size()
			self._dialog.set_size_request(-1, -1)

	def _get_text_variables(self, count):
		"""Get text variables for update"""
		title = ngettext(
					'Copy item',
					'Copy items',
					count
				)
		label = ngettext(
					'Copy <b>{0}</b> item to:',
					'Copy <b>{0}</b> items to:',
					count
				)

		return title, label

	def _create_buttons(self):
		"""Create action buttons"""
		button_cancel = Gtk.Button.new_with_label(_('Cancel'))
		button_copy = Gtk.Button.new_with_label(_('Copy'))
		if Gtk.get_major_version() == 3:
			button_copy.set_can_default(True)

		image_save = Gtk.Image()
		if Gtk.get_major_version() == 3:
			image_save.set_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.BUTTON)

		else:
			image_save.set_from_icon_name('document-save-symbolic')
		button_save = Gtk.Button()
		if Gtk.get_major_version() == 3:
			button_save.set_image(image_save)

		else:
			button_save.set_child(image_save)
		button_save.connect('clicked', self._save_configuration)
		button_save.set_tooltip_text(_('Save as default configuration'))
		button_save.set_halign(1)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_copy, Gtk.ResponseType.OK)
		self._dialog.get_header_bar().pack_end(button_save)

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self.entry_destination.get_text() != '':
			self._dialog.response(Gtk.ResponseType.OK)

	def _update_label(self, widget=None, data=None):
		"""Update label based on file type and selection"""
		icon_manager = self._application.icon_manager
		source_provider = self._source_provider

		# get affected items
		pattern = self.entry_type.get_text()
		affected_items = [item for item in source_provider.get_selection()
						  if source_provider.is_dir(item) or fnmatch.fnmatch(item, pattern)]
		item_count = len(affected_items)

		# change title and label
		title, label = self._get_text_variables(item_count)

		self.set_title(title)
		self.label_destination.set_markup(label.format(item_count))

		# populate list
		self._affected.clear()
		for item in affected_items:
			if source_provider.is_dir(item):
				icon = icon_manager.get_icon_for_directory(item)
			else:
				icon = icon_manager.get_icon_for_file(item)

			self._affected.append((icon, decode_file_name(os.path.basename(item))))

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		dictionary with other selected options.

		"""
		code = run_dialog(self._dialog)
		options = (
				self.entry_type.get_text(),
				self.entry_destination.get_text(),
				self.checkbox_owner.get_active(),
				self.checkbox_mode.get_active(),
				self.checkbox_timestamp.get_active(),
				self.checkbox_silent.get_active(),
				self.checkbox_merge.get_active(),
				self.checkbox_overwrite.get_active(),
				self.checkbox_symlink.get_active()
			)
		selected_iter = self.combobox_queue.get_active_iter()
		queue_name = OperationQueue.get_name_from_iter(selected_iter)

		self._dialog.destroy()

		return code, options, queue_name


class MoveDialog(CopyDialog):
	"""Dialog which will ask user for additional options before moving"""

	def _get_text_variables(self, count):
		"""Get text variables for update"""
		title = ngettext(
					'Move item',
					'Move items',
					count
				)
		label = ngettext(
					'Move <b>{0}</b> item to:',
					'Move <b>{0}</b> items to:',
					count
				)

		return title, label

	def _create_buttons(self):
		"""Create action buttons"""
		button_cancel = Gtk.Button.new_with_label(_('Cancel'))
		button_move = Gtk.Button.new_with_label(_('Move'))
		if Gtk.get_major_version() == 3:
			button_move.set_can_default(True)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_move, Gtk.ResponseType.OK)


class RenameDialog(InputDialog):
	"""Dialog used for renaming file/directory"""

	def __init__(self, application, selection, is_dir):
		InputDialog.__init__(self, application)

		self.set_title(_('Rename file/directory'))
		self.set_label(_('Enter a new name for this item:'))
		self.set_text(selection)

		if is_dir:
			self._entry.select_region(0, len(selection))

		else:
			self._entry.select_region(0, len(os.path.splitext(selection)[0]))


class OverwriteDialog:
	"""Dialog used for confirmation of file/directory overwrite"""

	def __init__(self, application, parent):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)

		self._application = application
		self._rename_value = ''
		self._time_format = application.options.section('item_list').get('time_format')

		self._dialog.set_default_size(500, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_urgency_hint(True)

		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 10)
		set_border_width(hbox, 10)

		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
		vbox_icon = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# create interface
		icon = Gtk.Image()
		if Gtk.get_major_version() == 3:
			icon.set_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.DIALOG)

		else:
			icon.set_from_icon_name('dialog-warning')

		self._label_title = Gtk.Label()
		self._label_title.set_use_markup(True)
		self._label_title.set_xalign(0)
		self._label_title.set_yalign(0.5)
		if Gtk.get_major_version() == 3:
			self._label_title.set_line_wrap(True)

		else:
			self._label_title.set_wrap(True)

		self._label_message = Gtk.Label()
		self._label_message.set_xalign(0)
		self._label_message.set_yalign(0.5)
		if Gtk.get_major_version() == 3:
			self._label_message.set_line_wrap(True)

		else:
			self._label_message.set_wrap(True)

		# inner hbox for original file
		hbox_original = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

		self._icon_original = Gtk.Image()
		self._label_original = Gtk.Label()
		self._label_original.set_use_markup(True)
		self._label_original.set_xalign(0)
		self._label_original.set_yalign(0.5)

		# inner hbox for source file
		hbox_source = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

		self._icon_source = Gtk.Image()
		self._label_source = Gtk.Label()
		self._label_source.set_use_markup(True)
		self._label_source.set_xalign(0)
		self._label_source.set_yalign(0.5)

		# rename expander
		self._expander_rename = Gtk.Expander(label=_('Select a new name for the destination'))
		self._expander_rename.connect('activate', self._rename_toggled)
		hbox_rename = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 10)

		self._entry_rename = Gtk.Entry()
		button_reset = Gtk.Button.new_with_label(_('Reset'))
		button_reset.connect('clicked', self._reset_rename_field)

		# apply to all check box
		self._checkbox_apply_to_all = Gtk.CheckButton.new_with_label(_('Apply this action to all files'))
		self._checkbox_apply_to_all.connect('toggled', self._apply_to_all_toggled)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_icon.pack_start(icon, False, False, 0)

			hbox_original.pack_start(self._icon_original, False, False, 10)
			hbox_original.pack_start(self._label_original, True, True, 0)

			hbox_source.pack_start(self._icon_source, False, False, 10)
			hbox_source.pack_start(self._label_source, True, True, 0)

		else:
			vbox_icon.append(icon)

			set_border_width(self._icon_original, 10)
			hbox_original.append(self._icon_original)
			self._label_original.set_hexpand(True)
			hbox_original.append(self._label_original)

			set_border_width(self._icon_source, 10)
			hbox_source.append(self._icon_source)
			self._label_source.set_hexpand(True)
			hbox_source.append(self._label_source)

		if Gtk.get_major_version() == 3:
			self._expander_rename.add(hbox_rename)

		else:
			self._expander_rename.set_child(hbox_rename)

		if Gtk.get_major_version() == 3:
			hbox_rename.pack_start(self._entry_rename, False, False, 0)
			hbox_rename.pack_start(button_reset, False, False, 0)

			vbox.pack_start(self._label_title, False, False, 0)
			vbox.pack_start(self._label_message, False, False, 0)
			vbox.pack_start(hbox_original, False, False, 0)
			vbox.pack_start(hbox_source, False, False, 0)
			vbox.pack_start(self._expander_rename, False, False, 0)
			vbox.pack_start(self._checkbox_apply_to_all, False, False, 0)

			hbox.pack_start(vbox_icon, False, False, 0)
			hbox.pack_start(vbox, True, True, 0)

		else:
			hbox_rename.append(self._entry_rename)
			hbox_rename.append(button_reset)

			vbox.append(self._label_title)
			vbox.append(self._label_message)
			vbox.append(hbox_original)
			vbox.append(hbox_source)
			vbox.append(self._expander_rename)
			vbox.append(self._checkbox_apply_to_all)

			hbox.append(vbox_icon)
			vbox.set_hexpand(True)
			hbox.append(vbox)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(hbox, True, True, 0)

		else:
			hbox.set_vexpand(True)
			self._dialog.get_content_area().append(hbox)

		self._create_buttons()
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _create_buttons(self):
		"""Create basic buttons"""
		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))
		button_skip = Gtk.Button(label=_('Skip'))

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_skip, Gtk.ResponseType.NO)

	def _apply_to_all_toggled(self, widget, data=None):
		"""Event called upon clicking on "apply to all" check box"""
		checked = widget.get_active()
		self._expander_rename.set_sensitive(not checked)

	def _rename_toggled(self, widget, data=None):
		"""Event called upon activating expander"""
		expanded = widget.get_expanded()
		self._checkbox_apply_to_all.set_sensitive(expanded)

	def _reset_rename_field(self, widget, data=None):
		"""Reset rename field to predefined value"""
		self._entry_rename.set_text(self._rename_value)

	def _get_data(self, provider, path, relative_to=None):
		"""Return information for specified path using provider"""
		full_path = os.path.join(provider.get_path(), path)
		item_stat = provider.get_stat(path, relative_to=relative_to)

		if item_stat.type is FileType.DIRECTORY:
			size = len(provider.list_dir(path, relative_to=relative_to))
			icon = self._application.icon_manager.get_icon_for_directory(full_path)

		else:
			size = item_stat.size
			icon = self._application.icon_manager.get_icon_for_file(full_path)

		str_size = locale.format_string('%d', size, True)
		str_date = time.strftime(self._time_format, time.localtime(item_stat.time_modify))

		return str_size, str_date, icon

	def set_title_element(self, element):
		"""Set title label with appropriate formatting"""
		pass

	def set_message_element(self, element):
		"""Set message element"""
		pass

	def set_original(self, provider, path, relative_to=None):
		"""Set original element data"""
		data = self._get_data(provider, path, relative_to)

		if Gtk.get_major_version() == 3:
			self._icon_original.set_from_icon_name(data[2], Gtk.IconSize.DIALOG)

		else:
			self._icon_original.set_from_icon_name(data[2])
		self._label_original.set_markup(
									'<b>{2}</b>\n'
									'<i>{3}</i>\t\t{0}\n'
									'<i>{4}</i>\t{1}'.format(
																data[0],
																data[1],
																_('Original'),
																_('Size:'),
																_('Modified:')
															)
								)

	def set_source(self, provider, path, relative_to=None):
		"""Set source element data"""
		data = self._get_data(provider, path, relative_to)

		if Gtk.get_major_version() == 3:
			self._icon_source.set_from_icon_name(data[2], Gtk.IconSize.DIALOG)

		else:
			self._icon_source.set_from_icon_name(data[2])
		self._label_source.set_markup(
									'<b>{2}</b>\n'
									'<i>{3}</i>\t\t{0}\n'
									'<i>{4}</i>\t{1}'.format(
																data[0],
																data[1],
																_('Replace with'),
																_('Size:'),
																_('Modified:')
															)
								)

	def set_rename_value(self, name):
		"""Set rename default rename value"""
		self._rename_value = name
		self._entry_rename.set_text(name)

	def get_response(self):
		"""Return value and self-destroy

		This method returns tuple with response code and
		dictionary with other selected options.

		"""
		code = run_dialog(self._dialog)
		options = (
				self._expander_rename.get_expanded(),
				self._entry_rename.get_text(),
				self._checkbox_apply_to_all.get_active()
				)

		self._dialog.destroy()

		return code, options


class OverwriteFileDialog(OverwriteDialog):

	def __init__(self, application, parent):
		OverwriteDialog.__init__(self, application, parent)

		self._dialog.set_title(_('File conflict'))
		self._entry_rename.connect('changed', self._rename_button)

	def _create_buttons(self):
		"""Create dialog specific button"""
		self._button_replace = Gtk.Button(label=_('Replace'))
		if Gtk.get_major_version() == 3:
			self._button_replace.set_can_default(True)

		OverwriteDialog._create_buttons(self)
		self._dialog.add_action_widget(self._button_replace, Gtk.ResponseType.YES)

		self._dialog.set_default_response(Gtk.ResponseType.YES)

	def _rename_button(self, entry):
		if entry.get_text() == self._rename_value:
			self._button_replace.set_label(_('Replace'))

		else:
			self._button_replace.set_label(_('Copy'))

	def set_title_element(self, element):
		"""Set title label with appropriate formatting"""
		message = _('Replace file "{0}"?').format(element.replace('&', '&amp;'))
		self._label_title.set_markup('<span size="large" weight="bold">{0}</span>'.format(message))

	def set_message_element(self, element):
		"""Set message element"""
		message = _(
				'Another file with the same name already exists in '
				'"{0}". Replacing it will overwrite its content.'
			)

		self._label_message.set_text(message.format(element))


class OverwriteDirectoryDialog(OverwriteDialog):

	def __init__(self, application, parent):
		OverwriteDialog.__init__(self, application, parent)

		self._entry_rename.set_sensitive(False)
		self._dialog.set_title(_('Directory conflict'))

	def _create_buttons(self):
		"""Create dialog specific button"""
		button_merge = Gtk.Button(label=_('Merge'))
		if Gtk.get_major_version() == 3:
			button_merge.set_can_default(True)

		OverwriteDialog._create_buttons(self)
		self._dialog.add_action_widget(button_merge, Gtk.ResponseType.YES)

		self._dialog.set_default_response(Gtk.ResponseType.YES)

	def set_title_element(self, element):
		"""Set title label with appropriate formatting"""
		message = _('Merge directory "{0}"?').format(element)
		self._label_title.set_markup('<span size="large" weight="bold">{0}</span>'.format(message))

	def set_message_element(self, element):
		"""Set message element"""
		message = _(
				'Directory with the same name already exists in '
				'"{0}". Merging will ask for confirmation before '
				'replacing any files in the directory that conflict '
				'with the files being copied.'
			)

		self._label_message.set_text(message.format(element))


class AddBookmarkDialog:
	"""This dialog enables user to change data before adding new bookmark"""

	def __init__(self, application, path):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)

		self._application = application

		# configure dialog
		self._dialog.set_title(_('Add bookmark'))
		self._dialog.set_default_size(450, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		# create component container
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(vbox, 5)

		# bookmark name
		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_xalign(0)
		label_name.set_yalign(0.5)
		self._entry_name = Gtk.Entry()
		self._entry_name.connect('activate', self._confirm_entry)
		self._entry_name.set_tooltip_text(_(
					'Underscore in the label text indicates the next character '
					'should be underlined and used for the mnemonic accelerator '
					'key if it is the first character so marked.'
				))

		vbox_name = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# bookmark path
		label_path = Gtk.Label(label=_('Location:'))
		label_path.set_xalign(0)
		label_path.set_yalign(0.5)
		self._entry_path = Gtk.Entry()
		self._entry_path.set_text(path)
		self._entry_path.set_editable(False)

		vbox_path = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# controls
		if Gtk.get_major_version() == 3:
			button_ok = Gtk.Button(stock=Gtk.STOCK_OK)

		else:
			button_ok = Gtk.Button.new_with_label(_('OK'))
		button_ok.connect('clicked', self._confirm_entry)
		if Gtk.get_major_version() == 3:
			button_ok.set_can_default(True)

		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_ok, Gtk.ResponseType.OK)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_name.pack_start(label_name, False, False, 0)
			vbox_name.pack_start(self._entry_name, False, False, 0)

			vbox_path.pack_start(label_path, False, False, 0)
			vbox_path.pack_start(self._entry_path, False, False, 0)

			vbox.pack_start(vbox_name, False, False, 0)
			vbox.pack_start(vbox_path, False, False, 0)

		else:
			vbox_name.append(label_name)
			vbox_name.append(self._entry_name)

			vbox_path.append(label_path)
			vbox_path.append(self._entry_path)

			vbox.append(vbox_name)
			vbox.append(vbox_path)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(vbox, False, False, 0)

		else:
			self._dialog.get_content_area().append(vbox)

		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry_name.get_text() != '':
			self._dialog.response(Gtk.ResponseType.OK)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = run_dialog(self._dialog)

		name = self._entry_name.get_text()
		path = self._entry_path.get_text()

		self._dialog.destroy()

		return code, name, path


class OperationError:
	"""Dialog used to ask user about error occurred during certain operation."""
	RESPONSE_CANCEL = 0
	RESPONSE_RETRY = 1
	RESPONSE_SKIP = 2
	RESPONSE_SKIP_ALL = 3

	def __init__(self, application):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)
		self._application = application

		# configure dialog
		self._dialog.set_title(_('Operation error'))
		self._dialog.set_default_size(450, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		# create component container
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 10)
		set_border_width(hbox, 5)

		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
		vbox_icon = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		# create interface
		icon = Gtk.Image()
		if Gtk.get_major_version() == 3:
			icon.set_from_stock(Gtk.STOCK_DIALOG_ERROR, Gtk.IconSize.DIALOG)

		else:
			icon.set_from_icon_name('dialog-error')

		self._label_message = Gtk.Label()
		self._label_message.set_xalign(0)
		self._label_message.set_yalign(0)
		self._label_message.set_use_markup(True)
		if Gtk.get_major_version() == 3:
			self._label_message.set_line_wrap(True)

		else:
			self._label_message.set_wrap(True)
		self._label_message.set_size_request(340, -1)
		self._label_message.set_selectable(True)

		self._label_error = Gtk.Label()
		self._label_error.set_xalign(0)
		self._label_error.set_yalign(0)
		if Gtk.get_major_version() == 3:
			self._label_error.set_line_wrap(True)

		else:
			self._label_error.set_wrap(True)
		self._label_error.set_size_request(340, -1)
		self._label_error.set_selectable(True)

		# create controls
		button_cancel = Gtk.Button(label=_('Cancel'))
		button_skip = Gtk.Button(label=_('Skip'))
		button_skip_all = Gtk.Button(label=_('Skip all'))
		button_retry = Gtk.Button(label=_('Retry'))

		self._dialog.add_action_widget(button_cancel, self.RESPONSE_CANCEL)
		self._dialog.add_action_widget(button_skip, self.RESPONSE_SKIP)
		self._dialog.add_action_widget(button_skip_all, self.RESPONSE_SKIP_ALL)
		self._dialog.add_action_widget(button_retry, self.RESPONSE_RETRY)

		if Gtk.get_major_version() == 3:
			button_skip.set_can_default(True)
		self._dialog.set_default_response(self.RESPONSE_SKIP)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_icon.pack_start(icon, False, False, 0)

			vbox.pack_start(self._label_message, False, False, 0)
			vbox.pack_start(self._label_error, False, False, 0)

			hbox.pack_start(vbox_icon, False, False, 0)
			hbox.pack_start(vbox, True, True, 0)

		else:
			vbox_icon.append(icon)

			vbox.append(self._label_message)
			vbox.append(self._label_error)

			hbox.append(vbox_icon)
			vbox.set_hexpand(True)
			hbox.append(vbox)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(hbox, False, False, 0)

		else:
			self._dialog.get_content_area().append(hbox)

		# show all components
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def set_message(self, message):
		"""Set dialog message"""
		self._label_message.set_markup(message)

	def set_error(self, error):
		"""Set error text"""
		self._label_error.set_markup(error)

	def get_response(self):
		"""Return dialog response and self-destruct"""
		code = run_dialog(self._dialog)
		self._dialog.destroy()

		return code


class CreateToolbarWidgetDialog:
	"""Create widget persistent dialog."""

	def __init__(self, application):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)
		self._application = application

		# configure dialog
		self._dialog.set_title(_('Add toolbar widget'))
		self._dialog.set_default_size(450, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		# create component container
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(vbox, 5)

		# create interface
		vbox_name = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_name = Gtk.Label(label=_('Name:'))
		label_name.set_xalign(0)
		label_name.set_yalign(0.5)

		self._entry_name = Gtk.Entry()
		self._entry_name.set_max_width_chars(30)

		vbox_type = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_type = Gtk.Label(label=_('Type:'))
		label_type.set_xalign(0)
		label_type.set_yalign(0.5)

		cell_renderer_icon = Gtk.CellRendererPixbuf()
		cell_renderer_text = Gtk.CellRendererText()
		cell_renderer_text.set_property('xalign', 0)
		self._type_list = Gtk.ListStore(str, str, str)

		self._combobox_type = Gtk.ComboBox.new_with_model(self._type_list)
		self._combobox_type.pack_start(cell_renderer_icon, False)
		self._combobox_type.pack_start(cell_renderer_text, True)
		self._combobox_type.add_attribute(cell_renderer_icon, 'icon-name', 2)
		self._combobox_type.add_attribute(cell_renderer_text, 'text', 1)

		# create controls
		if Gtk.get_major_version() == 3:
			button_add = Gtk.Button(stock=Gtk.STOCK_ADD)

		else:
			button_add = Gtk.Button.new_with_label(_('Add'))
		if Gtk.get_major_version() == 3:
			button_add.set_can_default(True)
		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_add, Gtk.ResponseType.ACCEPT)

		self._dialog.set_default_response(Gtk.ResponseType.ACCEPT)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_name.pack_start(label_name, False, False, 0)
			vbox_name.pack_start(self._entry_name, False, False, 0)

			vbox_type.pack_start(label_type, False, False, 0)
			vbox_type.pack_start(self._combobox_type, False, False, 0)

			vbox.pack_start(vbox_name, False, False, 0)
			vbox.pack_start(vbox_type, False, False, 0)

		else:
			vbox_name.append(label_name)
			vbox_name.append(self._entry_name)

			vbox_type.append(label_type)
			vbox_type.append(self._combobox_type)

			vbox.append(vbox_name)
			vbox.append(vbox_type)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(vbox, False, False, 0)

		else:
			self._dialog.get_content_area().append(vbox)

		# show all widgets
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def update_type_list(self, widgets):
		"""Update type list store"""
		self._type_list.clear()

		for key in widgets.keys():
			# get data
			data = widgets[key]

			# extract data from tuple
			text = data[0]
			icon = data[1]

			# add new item to the list
			self._type_list.append((key, text, icon))

	def get_response(self):
		"""Return dialog response and self-destruct"""
		name = None
		widget_type = None

		# clear text entry before showing
		self._entry_name.set_text('')

		# show dialog
		code = run_dialog(self._dialog)

		# get name and type
		if code == Gtk.ResponseType.ACCEPT and len(self._type_list) > 0:
			name = self._entry_name.get_text()
			widget_type = self._type_list[self._combobox_type.get_active()][0]

		self._dialog.destroy()

		return code, name, widget_type

	def set_transient_for(self, window):
		"""Set dialog window transistency"""
		self._dialog.set_transient_for(window)


class InputRangeDialog(InputDialog):
	"""Dialog used for getting selection range"""

	def __init__(self, application, text):
		InputDialog.__init__(self, application)

		# set labels
		self.set_title(_('Select range'))
		self.set_label(_('Select part of the text:'))

		# configure entry
		self._entry.set_editable(False)
		self._entry.set_text(text)

	def get_response(self):
		"""Return selection selection_range and self-destruct"""
		code = run_dialog(self._dialog)
		selection_range = self._entry.get_selection_bounds()

		self._dialog.destroy()

		return code, selection_range


class ApplicationInputDialog(InputDialog):
	"""Input dialog for associations manager. Offers two fields
	for entry: application name and command."""

	def __init__(self, application):
		InputDialog.__init__(self, application)

		# configure existing components
		self.set_title(_('Add application'))
		self.set_label(_('Application name:'))

		# create additional components
		vbox_command = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		hbox_command = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)

		label_command = Gtk.Label(label='Command:')
		label_command.set_xalign(0)
		label_command.set_yalign(0.5)

		button_select = Gtk.Button()
		button_select.set_label(_('Select'))
		button_select.connect('clicked', self.__select_application)

		self._entry_command = Gtk.Entry()

		# pack interface
		if Gtk.get_major_version() == 3:
			hbox_command.pack_start(self._entry_command, True, True, 0)
			hbox_command.pack_start(button_select, False, False, 0)

			vbox_command.pack_start(label_command, False, False, 0)
			vbox_command.pack_start(hbox_command, False, False, 0)

			self._container.pack_start(vbox_command, False, False, 0)

		else:
			self._entry_command.set_hexpand(True)
			hbox_command.append(self._entry_command)
			hbox_command.append(button_select)

			vbox_command.append(label_command)
			vbox_command.append(hbox_command)

			self._container.append(vbox_command)
		self._container.set_spacing(5)

		# show components
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def __select_application(self, widget, data=None):
		"""Select application using ApplicationSelectDialog"""
		dialog = ApplicationSelectDialog(self._application)
		response = dialog.get_response()

		if response[0] == Gtk.ResponseType.OK:
			self._entry_command.set_text(response[2])

	def get_response(self):
		"""Get response from dialog"""
		code = run_dialog(self._dialog)

		name = self._entry.get_text()
		command = self._entry_command.get_text()

		self._dialog.destroy()

		return code, name, command


class ApplicationSelectDialog:
	"""Provides user with a list of installed applications and option to enter command"""

	help_url = 'https://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#exec-variables'

	def __init__(self, application, path=None):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)

		self._application = application
		self.path = path

		# configure dialog
		self._dialog.set_title(_('Open With'))
		self._dialog.set_default_size(500, 400)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(self._container, 5)

		# create interface
		vbox_list = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_open_with = Gtk.Label()
		label_open_with.set_use_markup(True)
		label_open_with.set_xalign(0)
		label_open_with.set_yalign(0.5)
		if path is None:
			label_open_with.set_label(_('Select application:'))

		else:
			decoded_path = decode_file_name(os.path.basename(path))
			label_open_with.set_label(_('Open <i>{0}</i> with:').format(decoded_path))

		# create application list
		list_container = Gtk.ScrolledWindow()
		list_container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		if Gtk.get_major_version() == 3:
			list_container.set_shadow_type(Gtk.ShadowType.IN)

		else:
			list_container.set_has_frame(True)

		self._store = Gtk.ListStore(str, str, str, str, str)
		self._list = Gtk.TreeView(model=self._store)

		cell_icon = Gtk.CellRendererPixbuf()
		cell_name = Gtk.CellRendererText()
		cell_generic = Gtk.CellRendererText()

		column_application = Gtk.TreeViewColumn()
		column_application.pack_start(cell_icon, False)
		column_application.pack_start(cell_name, True)
		column_application.add_attribute(cell_icon, 'icon-name', 0)
		column_application.add_attribute(cell_name, 'text', 1)
		column_application.set_expand(True)

		column_generic = Gtk.TreeViewColumn()
		column_generic.pack_start(cell_generic, True)
		column_generic.add_attribute(cell_generic, 'markup', 4)

		self._list.append_column(column_application)
		self._list.append_column(column_generic)
		self._list.set_headers_visible(False)
		self._list.set_search_column(1)
		self._list.set_enable_search(True)
		self._list.connect('cursor-changed', self.__handle_cursor_change)
		self._list.connect('row-activated', self.__handle_row_activated)

		self._store.set_sort_column_id(1, Gtk.SortType.ASCENDING)

		# create custom command entry
		self._expander_custom = Gtk.Expander(label=_('Use a custom command'))
		hbox_custom = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 7)
		self._entry_custom = Gtk.Entry()

		# pack interface
		if Gtk.get_major_version() == 3:
			list_container.add(self._list)

		else:
			list_container.set_child(self._list)
		if Gtk.get_major_version() == 3:
			vbox_list.pack_start(label_open_with, False, False, 0)
			vbox_list.pack_start(list_container, True, True, 0)

			hbox_custom.pack_start(self._entry_custom, True, True, 0)

		else:
			vbox_list.append(label_open_with)
			list_container.set_vexpand(True)
			vbox_list.append(list_container)

			self._entry_custom.set_hexpand(True)
			hbox_custom.append(self._entry_custom)
		if Gtk.get_major_version() == 3:
			self._expander_custom.add(hbox_custom)

		else:
			self._expander_custom.set_child(hbox_custom)

		if Gtk.get_major_version() == 3:
			self._container.pack_start(vbox_list, True, True, 0)
			self._container.pack_start(self._expander_custom, False, False, 0)

		else:
			vbox_list.set_vexpand(True)
			self._container.append(vbox_list)
			self._container.append(self._expander_custom)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(self._container, True, True, 0)

		else:
			self._container.set_vexpand(True)
			self._dialog.get_content_area().append(self._container)

		# create controls
		if Gtk.get_major_version() == 3:
			button_help = Gtk.Button(stock=Gtk.STOCK_HELP)

		else:
			button_help = Gtk.Button.new_with_label(_('Help'))
		button_help.connect('clicked', self._application.goto_web, self.help_url)

		if path is not None:
			if Gtk.get_major_version() == 3:
				button_ok = Gtk.Button(stock=Gtk.STOCK_OPEN)

			else:
				button_ok = Gtk.Button.new_with_label(_('Open'))

		else:
			if Gtk.get_major_version() == 3:
				button_ok = Gtk.Button(stock=Gtk.STOCK_OK)

			else:
				button_ok = Gtk.Button.new_with_label(_('OK'))

		if Gtk.get_major_version() == 3:
			button_ok.set_can_default(True)
		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		if Gtk.get_major_version() == 3:
			self._dialog.action_area.pack_start(button_help, False, False, 0)

		else:
			self._dialog.action_area.append(button_help)
		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_ok, Gtk.ResponseType.OK)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		# populate content
		self._load_applications()

		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def __handle_cursor_change(self, widget, data=None):
		"""Handle setting or changing list cursor"""
		selection = widget.get_selection()
		item_store, selected_iter = selection.get_selected()

		if selected_iter is not None:
			command = item_store.get_value(selected_iter, 3)
			self._entry_custom.set_text(command)

	def __handle_row_activated(self, path=None, view_column=None, data=None):
		"""Handle choosing application by presing 'Enter'"""
		self._dialog.response(Gtk.ResponseType.OK)

	def _load_applications(self):
		"""Populate application list from config files"""
		application_list = self._application.associations_manager.get_all()

		for application in application_list:
			if application.command_line is not None \
			and '%' in application.command_line:
				self._store.append((
							application.icon,
							application.name,
							application.id,
							application.command_line,
							'<small>{0}</small>'.format(application.description)
						))

	def get_response(self):
		"""Get response and destroy dialog"""
		code = run_dialog(self._dialog)
		is_custom = self._expander_custom.get_expanded()
		command = self._entry_custom.get_text()

		self._dialog.destroy()

		return code, is_custom, command


class PathInputDialog():
	"""Input Dialog with path completion entry"""
	def __init__(self, application):
		self._dialog = Gtk.Dialog(parent=application, use_header_bar=True)

		self._application = application

		self._dialog.set_default_size(450, 10)
		self._dialog.set_resizable(True)
		self._dialog.set_modal(True)
		self._dialog.set_transient_for(application)

		self._container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		set_border_width(self._container, 5)

		# create interface
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		self._label = Gtk.Label(label='Label')
		self._label.set_xalign(0)
		self._label.set_yalign(0.5)

		self._entry = PathCompletionEntry(application)
		self._entry.connect('activate', self._confirm_entry)

		if Gtk.get_major_version() == 3:
			button_ok = Gtk.Button(stock=Gtk.STOCK_OK)

		else:
			button_ok = Gtk.Button.new_with_label(_('OK'))
		button_ok.connect('clicked', self._confirm_entry)
		if Gtk.get_major_version() == 3:
			button_ok.set_can_default(True)

		if Gtk.get_major_version() == 3:
			button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)

		else:
			button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox.pack_start(self._label, False, False, 0)
			vbox.pack_start(self._entry, False, False, 0)

			self._container.pack_start(vbox, False, False, 0)

		else:
			vbox.append(self._label)
			vbox.append(self._entry)

			self._container.append(vbox)

		self._dialog.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self._dialog.add_action_widget(button_ok, Gtk.ResponseType.OK)
		self._dialog.set_default_response(Gtk.ResponseType.OK)

		if Gtk.get_major_version() == 3:
			self._dialog.get_content_area().pack_start(self._container, True, True, 0)

		else:
			self._container.set_vexpand(True)
			self._dialog.get_content_area().append(self._container)
		if Gtk.get_major_version() == 3:
			self._dialog.show_all()

		else:
			self._dialog.show()

	def _confirm_entry(self, widget, data=None):
		"""Enable user to confirm by pressing Enter"""
		if self._entry.get_text() != '':
			self._dialog.response(Gtk.ResponseType.OK)

	def set_title(self, title_text):
		"""Set dialog title"""
		self._dialog.set_title(title_text)

	def set_label(self, label_text):
		"""Provide an easy way to set label text"""
		self._label.set_text(label_text)

	def set_text(self, entry_text):
		"""Set main entry text"""
		if not entry_text.endswith(os.path.sep):
			entry_text = entry_text + os.path.sep

		self._entry.set_text(entry_text)
		self._entry.set_position(-1)

	def get_response(self):
		"""Return value and self-destruct

		This method returns tuple with response code and
		input text.

		"""
		code = run_dialog(self._dialog)
		result = self._entry.get_text()

		self._dialog.destroy()

		return code, result
