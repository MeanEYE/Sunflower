from __future__ import absolute_import

from gi.repository import Gtk, Gdk, GObject, Pango
from sunflower import common


class OperationDialog:
	"""Base class for operations dialog such as Copy/Move/Delete. Do *NOT* change this class
	as it might affect other dialogs and produce unpredictable behavior."""

	MAX_SPEED_POINTS = 20  # how many points to aggregate

	def __init__(self, application, thread):
		self._paused = False
		self._application = application
		self._thread = thread
		self._size_format = '{0} / {1}'
		self._count_format = '{0} / {1}'
		self._has_source_destination = False
		self._has_current_file = False
		self._has_details = False
		self._size_format_type = self._application.options.get('size_format')

		self._total_size = 0
		self._total_count = 0
		self._current_size = 0
		self._current_count = 0

		# aggregate speeds to provide accurate time prediction
		self._speeds = []
		self._total_checkpoint = 0

		# set window properties
		self._container = Gtk.Popover.new()
		self._container.set_size_request(500, -1)

		# connect signals
		self._container.connect('destroy', self._destroy)
		self._container.connect('delete-event', self._cancel_click)

		# create indicator button
		self._indicator = Gtk.MenuButton.new()
		self._indicator.set_popover(self._container)
		self._indicator.get_style_context().add_class('flat')

		# create interface
		self._vbox = Gtk.VBox(False, 5)

		# operation items
		self._operation_label = Gtk.Label.new()
		self._operation_label.set_alignment(0, 0.5)
		self._operation_progress = Gtk.ProgressBar()
		self._operation_image = Gtk.Image.new()
		self._set_operation_image()

		self._indicator.set_image(self._operation_image)

		vbox_operation = Gtk.VBox(False, 0)
		vbox_operation.pack_start(self._operation_label, False, False, 0)
		vbox_operation.pack_start(self._operation_progress, False, False, 0)

		self._application.add_operation(self._indicator)

		# pack interface
		self._container.add(self._vbox)

	def _add_source_destination(self):
		"""Add source and destination labels to the GUI"""
		self._has_source_destination = True
		table = Gtk.Table(2, 2, False)
		table.set_border_width(7)
		table.set_col_spacing(0, 10)
		table.set_row_spacing(0, 2)

		self._label_source = Gtk.Label(label=_('Source:'))
		self._label_destination = Gtk.Label(label=_('Destination:'))

		self._value_source = Gtk.Label.new()
		self._value_destination = Gtk.Label.new()

		# pack interface
		table.attach(self._label_source, 0, 1, 0, 1, Gtk.AttachOptions.FILL)
		table.attach(self._label_destination, 0, 1, 1, 2, Gtk.AttachOptions.FILL)

		table.attach(self._value_source, 1, 2, 0, 1)
		table.attach(self._value_destination, 1, 2, 1, 2)

		self._vbox.pack_start(table, False, False, 0)

		# configure components
		self._label_source.set_alignment(0, 0.5)
		self._label_destination.set_alignment(0, 0.5)

		self._value_source.set_alignment(0, 0.5)
		self._value_destination.set_alignment(0, 0.5)
		self._value_source.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
		self._value_destination.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

	def _add_current_file(self):
		"""Add 'current file' progress to the GUI"""
		self._has_current_file = True
		table = Gtk.Table.new(2, 2, False)
		table.set_border_width(7)
		table.set_row_spacing(0, 2)
		table.set_col_spacing(0, 10)

		self._label_status = Gtk.Label(label='Current status...')
		self._label_current_file = Gtk.Label.new()
		self._pb_current_file = Gtk.ProgressBar.new()
		self._pb_current_file.set_pulse_step(0.005)

		# pack interface
		table.attach(self._label_status, 0, 1, 0, 1, Gtk.AttachOptions.FILL)
		table.attach(self._label_current_file, 1, 2, 0, 1)
		table.attach(self._pb_current_file, 0, 2, 1, 2)

		if self._has_source_destination:
			separator = Gtk.HSeparator.new()
			self._vbox.pack_start(separator, False, False, 0)
		self._vbox.pack_start(table, False, False, 0)

		# configure components
		self._label_status.set_alignment(0, 0.5)
		self._label_current_file.set_alignment(1, 0.5)
		self._label_current_file.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

	def _add_details(self):
		"""Add ETA to the dialog"""
		self._has_details = True
		table = Gtk.Table.new(2, 6, False)
		table.set_border_width(7)

		self._label_eta = Gtk.Label.new(_('ETA:'))
		self._label_speed = Gtk.Label.new(_('Speed:'))
		self._label_total_size = Gtk.Label.new(_('Total size:'))
		self._label_total_count = Gtk.Label.new(_('Total count:'))

		self._value_eta = Gtk.Label.new()
		self._value_speed = Gtk.Label.new()
		self._value_total_size = Gtk.Label.new()
		self._value_total_count = Gtk.Label.new()

		self._pb_total_size = Gtk.ProgressBar.new()
		self._pb_total_count = Gtk.ProgressBar.new()

		# pack interface
		table.attach(self._label_eta, 0, 1, 0, 1, Gtk.AttachOptions.FILL)
		table.attach(self._label_speed, 0, 1, 1, 2, Gtk.AttachOptions.FILL)
		table.attach(self._label_total_size, 0, 1, 2, 3, Gtk.AttachOptions.FILL)
		table.attach(self._label_total_count, 0, 1, 4, 5, Gtk.AttachOptions.FILL)

		table.attach(self._value_eta, 1, 2, 0, 1)
		table.attach(self._value_speed, 1, 2, 1, 2)
		table.attach(self._value_total_size, 1, 2, 2, 3)
		table.attach(self._pb_total_size, 0, 2, 3, 4)
		table.attach(self._value_total_count, 1, 2, 4, 5)
		table.attach(self._pb_total_count, 0, 2, 5, 6)

		separator = Gtk.HSeparator()
		self._vbox.pack_start(separator, False, False, 0)
		self._vbox.pack_start(table, False, False, 0)

		# configure components
		self._label_eta.set_alignment(0, 0.5)
		self._label_speed.set_alignment(0, 0.5)
		self._label_total_size.set_alignment(0, 0.5)
		self._label_total_count.set_alignment(0, 0.5)

		self._value_eta.set_alignment(0, 0.5)
		self._value_speed.set_alignment(0, 0.5)
		self._value_total_size.set_alignment(0, 0.5)
		self._value_total_count.set_alignment(0, 0.5)

		table.set_row_spacing(0, 2)
		table.set_row_spacing(1, 10)
		table.set_row_spacing(2, 2)
		table.set_row_spacing(3, 10)
		table.set_row_spacing(4, 2)
		table.set_col_spacing(0, 10)

		# add periodical updates for dialog
		GObject.timeout_add(1000, self._update_speed)

	def _add_buttons(self):
		"""Add button bar"""
		hbox = Gtk.HBox(False, 5)
		hbox.set_border_width(7)

		self._button_cancel = Gtk.Button(_('Cancel'))

		image_pause = Gtk.Image.new()
		image_pause.set_from_icon_name('media-playback-pause-symbolic', Gtk.IconSize.BUTTON)

		self._button_pause = Gtk.Button()
		self._button_pause.add(image_pause)
		self._button_pause.set_tooltip_text(_('Pause'))

		self._button_pause.connect('clicked', self._pause_click)
		self._button_cancel.connect('clicked', self._cancel_click)

		# pack interface
		hbox.pack_start(self._button_pause, False, False, 0)
		hbox.pack_end(self._button_cancel, False, False, 0)

		separator = Gtk.HSeparator()
		self._vbox.pack_end(hbox, False, False, 0)
		self._vbox.pack_end(separator, False, False, 0)

	def _confirm_cancel(self, message):
		"""Create confirmation dialog with specified message and return result"""
		dialog = Gtk.MessageDialog(
						self._application,
						Gtk.DialogFlags.DESTROY_WITH_PARENT,
						Gtk.MessageType.QUESTION,
						Gtk.ButtonsType.YES_NO,
						message
					)
		dialog.set_default_response(Gtk.ResponseType.YES)
		result = dialog.run()
		dialog.destroy()

		return result == Gtk.ResponseType.YES

	def _pause_click(self, widget, data=None):
		"""Lock threading object"""
		self._paused = not self._paused
		image = self._button_pause.get_child()

		if self._paused:
			# thread is active, pause it
			self._set_operation_image('media-playback-pause-symbolic')
			image.set_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.BUTTON)
			self._button_pause.set_tooltip_text(_('Resume'))
			self._thread.pause()

		else:
			# thread is paused, resume it
			self._set_operation_image()
			image.set_from_icon_name('media-playback-pause-symbolic', Gtk.IconSize.BUTTON)
			self._button_pause.set_tooltip_text(_('Pause'))
			self._thread.resume()

	def _cancel_click(self, widget, data=None):
		"""Handle cancel button click event"""
		if self._confirm_cancel(_('Are you sure about canceling current operation?')):
			self._thread.cancel()

		# TODO: Add 5-10 seconds timeout before forced cancel occurs.

		return True  # handle delete-event properly

	def _update_total_count(self):
		"""Update progress bar and labels for total count"""
		self._value_total_count.set_label(self._count_format.format(self._current_count, self._total_count))
		self.set_total_count_fraction(float(self._current_count) / self._total_count)

	def _update_total_size(self):
		"""Update progress bar and labels for total size"""
		# update label
		formatted_size = self._size_format.format(
				common.format_size(self._current_size, self._size_format_type),
				common.format_size(self._total_size, self._size_format_type)
				)
		self._value_total_size.set_label(formatted_size)

		if self._total_size > 0:
			self.set_total_size_fraction(float(self._current_size) / self._total_size)
		else:
			self.set_total_size_fraction(1)

	def _update_speed(self):
		"""Aggregate speed and update ETA label.

		This method is automatically called by the GObject timeout.
		Don't call this method automatically!

		"""
		if self._paused:
			return True  # don't update speed when paused

		speed = self._current_size - self._total_checkpoint  # get current speed
		self._total_checkpoint = self._current_size

		# update aggregates speeds list
		if len(self._speeds) > self.MAX_SPEED_POINTS:
			self._speeds.pop(0)

		self._speeds.append(speed)

		# calculate average speed
		average = sum(self._speeds) / len(self._speeds)

		# update labels
		if average > 0:
			# calculate time based on average speed
			remainder = (self._total_size - self._current_size) / average
			hours, remainder = divmod(remainder, 3600)
			minutes, seconds = divmod(remainder, 60)

			seconds = int(seconds)
			time_text = '{0} {1}'.format(seconds, ngettext('second', 'seconds', seconds))

			if minutes > 0:
				minutes = int(minutes)
				time_text = '{0} {1}, {2}'.format(minutes, ngettext('minute', 'minutes', minutes), time_text)

			if hours > 0:
				hours = int(hours)
				time_text = '{0} {1}, {2}'.format(hours, ngettext('hour', 'hours', hours), time_text)

		else:
			# we don't have average speed yet
			time_text = _('unknown')

		average_text = common.format_size(average, self._size_format_type)
		speed_text = '{0}/s'.format(average_text)

		self._value_eta.set_text(time_text)
		self._value_speed.set_text(speed_text)

		# make sure we keep updating
		return True

	def _destroy(self, widget, data=None):
		"""Remove operation menu item on dialog destroy."""
		self._application.remove_operation(self._indicator)

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		if icon_name is not None:
			self._operation_image.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)

	def is_active(self):
		"""Return true if window is active"""
		return self._application.is_active()

	def destroy(self):
		"""Close window"""
		self._container.destroy()

	def get_window(self):
		"""Return container window"""
		return self._container

	def set_status(self, status):
		"""Set current status"""
		self._label_status.set_label(status)
		self._operation_label.set_text(status)

	def set_current_file(self, path):
		"""Set current file name"""
		self._label_current_file.set_text(common.decode_file_name(path))

	def set_current_file_fraction(self, fraction):
		"""Set current file progress bar position"""
		self._pb_current_file.set_fraction(fraction)

		if not self._has_details:
			self._operation_progress.set_fraction(fraction)

	def set_current_count(self, count):
		"""Set current count value"""
		self._current_count = count
		self._update_total_count()

	def set_source(self, source):
		"""Set the content of source label"""
		self._value_source.set_label(source)

	def set_destination(self, destination):
		"""Set the content of destination label"""
		self._value_destination.set_label(destination)

	def set_eta(self, eta):
		"""Set the content of ETA label"""
		self._value_eta.set_label(eta)

	def set_speed(self, speed):
		"""Set the content of speed label"""
		self._value_speed.set_label(speed)

	def set_total_size(self, size):
		"""Set total size label"""
		self._value_total_size.set_label(size)

	def set_total_size_fraction(self, fraction):
		"""Set total size progress bar position"""
		self._pb_total_size.set_fraction(fraction)
		self._operation_progress.set_fraction(fraction)

	def set_total_count(self, count):
		"""Set total count label"""
		self._total_count = count
		self._update_total_count()

	def set_total_count_fraction(self, fraction):
		"""Set total size progress bar position"""
		self._pb_total_count.set_fraction(fraction)

	def increment_total_size(self, value):
		"""Increment total file size"""
		self._total_size += value
		self._update_total_size()

	def increment_current_size(self, value):
		"""Increment current summed file size"""
		self._current_size += value
		self._update_total_size()

	def increment_total_count(self, value):
		"""Increment total file count by value"""
		self._total_count += value
		self._update_total_count()

	def increment_current_count(self, value):
		"""Increment current file count by value"""
		self._current_count += value
		self._update_total_count()

	def pulse(self):
		"""Pulse current progress bar"""
		self._pb_current_file.pulse()


class CopyDialog(OperationDialog):
	"""Dialog used to display progress for copying files"""

	def __init__(self, application, thread):
		OperationDialog.__init__(self, application, thread)

		# create additional controls
		self._add_source_destination()
		self._add_current_file()
		self._add_details()
		self._add_buttons()

		# show all elements
		self._container.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		OperationDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_icon_name('edit-copy-symbolic', Gtk.IconSize.BUTTON)


class MoveDialog(CopyDialog):
	"""Dialog used to display progress for moving files"""

	def __init__(self, application, thread):
		CopyDialog.__init__(self, application, thread)

		# show all elements
		self._container.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		CopyDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_icon_name('edit-cut-symbolic', Gtk.IconSize.BUTTON)


class DeleteDialog(OperationDialog):
	"""Dialog displayed during delete procedure"""

	def __init__(self, application, thread):
		OperationDialog.__init__(self, application, thread)

		# create additional controls
		self._add_current_file()
		self._add_buttons()

		# configure layout
		self.set_status(_('Removing items...'))
		self.set_current_file('')

		# show all elements
		self._container.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		OperationDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_icon_name('edit-delete-symbolic', Gtk.IconSize.BUTTON)


class RenameDialog(OperationDialog):
	"""Dialog displayed during rename procedure"""

	def __init__(self, application, thread):
		OperationDialog.__init__(self, application, thread)

		# create additional controls
		self._add_current_file()
		self._add_buttons()

		# configure layout
		self.set_status(_('Renaming items...'))
		self.set_current_file('')

		# show all elements
		self._container.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		OperationDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_icon_name('edit-find-replace', Gtk.IconSize.MENU)
