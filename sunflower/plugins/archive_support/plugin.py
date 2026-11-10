from __future__ import absolute_import

import os

from gi.repository import Gtk

from .zip_provider import ZipProvider
from sunflower.gui.input_dialog import InputDialog
from sunflower.plugin_base.item_list import ItemList
from sunflower.plugin_base.monitor import MonitorSignals
from sunflower.plugin_base.provider import Mode as FileMode

# archive with no files in it consists only of the record ending list of files
EMPTY_ARCHIVE = b'PK\x05\x06' + b'\x00' * 18


def create_archive(application, name=None):
	"""Create empty archive in directory shown by the active list.

	User is asked for the name unless one is specified.

	"""
	active_object = application.get_active_object()

	if not isinstance(active_object, ItemList):
		return False

	if name is None:
		dialog = InputDialog(application)
		dialog.set_title(_('Create archive'))
		dialog.set_label(_('Enter name for the new archive:'))
		dialog.set_text(_('archive') + '.zip')
		response = dialog.get_response()

		if response[0] != Gtk.ResponseType.OK:
			return False

		name = response[1]

	if not name.lower().endswith('.zip'):
		name += '.zip'

	provider = active_object.get_provider()
	path = active_object.path

	try:
		if provider.exists(name, relative_to=path):
			raise OSError(_('Item with the same name already exists: {0}').format(name))

		# set this item to be focused on add
		active_object._item_to_focus = name

		# create archive through provider so it works wherever list is
		archive = provider.get_file_handle(name, FileMode.WRITE, relative_to=path)

		if archive is None:
			raise OSError(_('Files can not be created in this location.'))

		archive.write(EMPTY_ARCHIVE)
		archive.close()

		# push monitor event queue
		event_queue = active_object.get_monitor_queue()
		if event_queue is not None:
			event_queue.put((MonitorSignals.CREATED, name, None), False)

	except Exception as error:
		# error creating, report to user
		dialog = Gtk.MessageDialog(
								transient_for=application,
								destroy_with_parent=True,
								message_type=Gtk.MessageType.ERROR,
								buttons=Gtk.ButtonsType.OK,
								text=_(
									"There was an error creating archive. "
									"Make sure you have enough permissions."
								) + "\n\n{0}".format(error)
							)
		run_dialog(dialog)
		dialog.destroy()

		return False

	return True


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_provider(ZipProvider)

	# add option for creating archives next to files and directories
	application.register_new_item(
			'archive',
			_('Create _archive'),
			lambda action, parameter: create_archive(application)
		)
