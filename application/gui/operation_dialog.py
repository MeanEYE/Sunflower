import gtk
import pango
import gobject
import common


class OperationDialog:
	"""Dialog for operations

	Base class for operations dialog such as
	Copy/Move/Delete. Do *NOT* change this class
	as it might affect other dialogs and produce
	unpredictable behavior.

	"""

	MAX_SPEED_POINTS = 20  # how many points to aggregate

	def __init__(self, application, thread):
		self._window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)

		self._paused = False
		self._application = application
		self._thread = thread
		self._size_format = '{0} / {1}'
		self._count_format = '{0} / {1}'
		self._has_source_destination = False
		self._has_current_file = False
		self._has_details = False
		self._size_format_type = self._application.options.get('size_format')
		self._hide_on_minimize = application.options.section('operations').get('hide_on_minimize')

		self._total_size = 0L
		self._total_count = 0L
		self._current_size = 0L
		self._current_count = 0L

		# aggregate speeds to provide accurate time prediction
		self._speeds = []
		self._total_checkpoint = 0

		# set window properties
		self._window.set_title('Operation Dialog')
		self._window.set_default_size(500, 10)
		self._window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self._window.set_resizable(True)
		self._window.set_skip_taskbar_hint(False)
		self._window.set_transient_for(application)
		self._window.set_wmclass('Sunflower', 'Sunflower')

		# connect signals
		self._window.connect('destroy', self._destroy)
		self._window.connect('delete-event', self._cancel_click)
		self._window.connect('window-state-event', self._window_state)

		# set icon
		self._application.icon_manager.set_window_icon(self._window)

		# create interface
		self._vbox = gtk.VBox(False, 5)

		# operation items
		self._operation_label = gtk.Label()
		self._operation_label.set_alignment(0, 0.5)
		self._operation_progress = gtk.ProgressBar()
		self._operation_image = gtk.Image()
		self._set_operation_image()

		vbox_operation = gtk.VBox(False, 0)
		vbox_operation.pack_start(self._operation_label, False, False, 0)
		vbox_operation.pack_start(self._operation_progress, False, False, 0)

		self._operation_item = self._application.add_operation(
															vbox_operation,
															self._operation_click
														)
		self._operation_item.set_image(self._operation_image)
		self._operation_item.show_all()

		# pack interface
		self._window.add(self._vbox)

	def _add_source_destination(self):
		"""Add source and destination labels to the GUI"""
		self._has_source_destination = True
		table = gtk.Table(2, 2, False)
		table.set_border_width(7)
		table.set_col_spacing(0, 10)
		table.set_row_spacing(0, 2)

		self._label_source = gtk.Label(_('Source:'))
		self._label_destination = gtk.Label(_('Destination:'))

		self._value_source = gtk.Label()
		self._value_destination = gtk.Label()

		# pack interface
		table.attach(self._label_source, 0, 1, 0, 1, gtk.FILL)
		table.attach(self._label_destination, 0, 1, 1, 2, gtk.FILL)

		table.attach(self._value_source, 1, 2, 0, 1)
		table.attach(self._value_destination, 1, 2, 1, 2)

		self._vbox.pack_start(table, False, False, 0)

		# configure components
		self._label_source.set_alignment(0, 0.5)
		self._label_destination.set_alignment(0, 0.5)

		self._value_source.set_alignment(0, 0.5)
		self._value_destination.set_alignment(0, 0.5)
		self._value_source.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
		self._value_destination.set_ellipsize(pango.ELLIPSIZE_MIDDLE)

	def _add_current_file(self):
		"""Add 'current file' progress to the GUI"""
		self._has_current_file = True
		table = gtk.Table(2, 2, False)
		table.set_border_width(7)
		table.set_row_spacing(0, 2)
		table.set_col_spacing(0, 10)

		self._label_status = gtk.Label('Current status...')
		self._label_current_file = gtk.Label()
		self._pb_current_file = gtk.ProgressBar()
		self._pb_current_file.set_pulse_step(0.005)

		# pack interface
		table.attach(self._label_status, 0, 1, 0, 1, gtk.FILL)
		table.attach(self._label_current_file, 1, 2, 0, 1)
		table.attach(self._pb_current_file, 0, 2, 1, 2)

		if self._has_source_destination:
			separator = gtk.HSeparator()
			self._vbox.pack_start(separator, False, False, 0)
		self._vbox.pack_start(table, False, False, 0)

		# configure components
		self._label_status.set_alignment(0, 0.5)
		self._label_current_file.set_alignment(1, 0.5)
		self._label_current_file.set_ellipsize(pango.ELLIPSIZE_MIDDLE)

	def _add_details(self):
		"""Add ETA to the dialog"""
		self._has_details = True
		table = gtk.Table(2, 6, False)
		table.set_border_width(7)

		self._label_eta = gtk.Label(_('ETA:'))
		self._label_speed = gtk.Label(_('Speed:'))
		self._label_total_size = gtk.Label(_('Total size:'))
		self._label_total_count = gtk.Label(_('Total count:'))

		self._value_eta = gtk.Label()
		self._value_speed = gtk.Label()
		self._value_total_size = gtk.Label()
		self._value_total_count = gtk.Label()

		self._pb_total_size = gtk.ProgressBar()
		self._pb_total_count = gtk.ProgressBar()

		# pack interface
		table.attach(self._label_eta, 0, 1, 0, 1, gtk.FILL)
		table.attach(self._label_speed, 0, 1, 1, 2, gtk.FILL)
		table.attach(self._label_total_size, 0, 1, 2, 3, gtk.FILL)
		table.attach(self._label_total_count, 0, 1, 4, 5, gtk.FILL)

		table.attach(self._value_eta, 1, 2, 0, 1)
		table.attach(self._value_speed, 1, 2, 1, 2)
		table.attach(self._value_total_size, 1, 2, 2, 3)
		table.attach(self._pb_total_size, 0, 2, 3, 4)
		table.attach(self._value_total_count, 1, 2, 4, 5)
		table.attach(self._pb_total_count, 0, 2, 5, 6)

		separator = gtk.HSeparator()
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
		gobject.timeout_add(1000, self._update_speed)

	def _add_buttons(self):
		"""Add button bar"""
		hbox = gtk.HBox(False, 5)
		hbox.set_border_width(7)

		self._button_minimize = gtk.Button(_('Minimize'))
		self._button_cancel = gtk.Button(_('Cancel'))

		image_pause = gtk.Image()
		image_pause.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)

		self._button_pause = gtk.Button()
		self._button_pause.add(image_pause)
		self._button_pause.set_tooltip_text(_('Pause'))

		self._button_minimize.connect('clicked', self._minimize_click)
		self._button_pause.connect('clicked', self._pause_click)
		self._button_cancel.connect('clicked', self._cancel_click)

		# pack interface
		hbox.pack_start(self._button_minimize, False, False, 0)
		hbox.pack_start(self._button_pause, False, False, 0)
		hbox.pack_end(self._button_cancel, False, False, 0)

		separator = gtk.HSeparator()
		self._vbox.pack_end(hbox, False, False, 0)
		self._vbox.pack_end(separator, False, False, 0)

	def _confirm_cancel(self, message):
		"""Create confirmation dialog with specified message and return result"""
		dialog = gtk.MessageDialog(
						self._window,
						gtk.DIALOG_DESTROY_WITH_PARENT,
						gtk.MESSAGE_QUESTION,
						gtk.BUTTONS_YES_NO,
						message
					)
		dialog.set_default_response(gtk.RESPONSE_YES)
		result = dialog.run()
		dialog.destroy()

		return result == gtk.RESPONSE_YES

	def _minimize_click(self, widget, data=None):
		"""Handle minimize click"""
		self._window.iconify()

		# support for compositing window managers
		if self._hide_on_minimize:
			self._application.operation_menu_changed()
			self._window.hide()

	def _pause_click(self, widget, data=None):
		"""Lock threading object"""
		self._paused = not self._paused
		image = self._button_pause.get_child()

		if self._paused:
			# thread is active, pause it
			self._set_operation_image(gtk.STOCK_MEDIA_PAUSE)
			image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
			self._button_pause.set_tooltip_text(_('Resume'))
			self._thread.pause()

		else:
			# thread is paused, resume it
			self._set_operation_image()
			image.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
			self._button_pause.set_tooltip_text(_('Pause'))
			self._thread.resume()

	def _cancel_click(self, widget, data=None):
		"""Handle cancel button click event"""
		if self._confirm_cancel(_('Are you sure about canceling current operation?')):
			self._thread.cancel()

		# TODO: Add 5-10 seconds timeout before forced cancel occurs.

		return True  # handle delete-event properly

	def _operation_click(self, widget, data=None):
		"""Handle operation menu item click"""
		self._window.deiconify()

		# support for compositing window managers
		if self._hide_on_minimize:
			self._application.operation_menu_changed()
			self._window.present()

	def _update_total_count(self):
		"""Update progress bar and labels for total count"""
		self._value_total_count.set_label(self._count_format.format(
															self._current_count,
															self._total_count
															))
		self.set_total_count_fraction(float(self._current_count) / self._total_count)

	def _update_total_size(self):
		"""Update progress bar and labels for total size"""
		# update label
		formated_size = self._size_format.format(
											common.format_size(self._current_size, self._size_format_type),
											common.format_size(self._total_size, self._size_format_type)
										)
		self._value_total_size.set_label(formated_size)

		if self._total_size > 0:
			self.set_total_size_fraction(float(self._current_size) / self._total_size)

		else:
			self.set_total_size_fraction(1)

	def _update_speed(self):
		"""Aggregate speed and update ETA label

		This method is automatically called by the gobject timeout.
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

			time_text = '{0} {1}'.format(
									seconds,
									ngettext('second', 'seconds', seconds)
								)

			if minutes > 0:
				time_text = '{0} {1}, {2}'.format(
									minutes,
									ngettext('minute', 'minutes', minutes),
									time_text
								)

			if hours > 0:
				time_text = '{0} {1}, {2}'.format(
									hours,
									ngettext('hour', 'hours', hours),
									time_text
								)

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
		"""Remove operation menu item on dialog destroy"""
		self._application.remove_operation(self._operation_item)

	def _window_state(self, widget, event, data=None):
		"""Handle change of window state"""
		if event.new_window_state == gtk.gdk.WINDOW_STATE_ICONIFIED:
			# window was iconified, show operations menu item
			self._application.operation_menu_changed()

		elif event.new_window_state == 0:
			# normal window state or window was restored
			self._application.operation_menu_changed()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		if icon_name is not None:
			self._operation_image.set_from_icon_name(icon_name, gtk.ICON_SIZE_MENU)

	def is_active(self):
		"""Return true if window is active"""
		return self._window.is_active()

	def destroy(self):
		"""Close window"""
		self._window.destroy()

	def get_window(self):
		"""Return container window"""
		return self._window

	def set_title(self, title_text):
		"""Set window title"""
		self._window.set_title(title_text)

	def set_status(self, status):
		"""Set current status"""
		self._label_status.set_label(status)
		self._operation_label.set_text(status)

	def set_current_file(self, path):
		"""Set current file name"""
		self._label_current_file.set_label(path)

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

		# configure layout
		self.set_title(_('Copy Selection'))

		# show all elements
		self._window.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		OperationDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)


class MoveDialog(CopyDialog):
	"""Dialog used to display progress for moving files"""

	def __init__(self, application, thread):
		CopyDialog.__init__(self, application, thread)

		# configure layout
		self.set_title(_('Move Selection'))

		# show all elements
		self._window.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		CopyDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_stock(gtk.STOCK_CUT, gtk.ICON_SIZE_MENU)


class DeleteDialog(OperationDialog):
	"""Dialog displayed during delete procedure"""

	def __init__(self, application, thread):
		OperationDialog.__init__(self, application, thread)

		# create additional controls
		self._add_current_file()
		self._add_buttons()

		# configure layout
		self.set_title(_('Delete Selection'))
		self.set_status(_('Removing items...'))
		self.set_current_file('')

		# show all elements
		self._window.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		OperationDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU)


class RenameDialog(OperationDialog):
	"""Dialog displayed during rename procedure"""

	def __init__(self, application, thread):
		OperationDialog.__init__(self, application, thread)

		# create additional controls
		self._add_current_file()
		self._add_buttons()

		# configure layout
		self.set_title(_('Rename Items'))
		self.set_status(_('Renaming items...'))
		self.set_current_file('')

		# show all elements
		self._window.show_all()

	def _set_operation_image(self, icon_name=None):
		"""Set default or specified operation image"""
		OperationDialog._set_operation_image(self, icon_name)

		# set default icon
		if icon_name is None:
			self._operation_image.set_from_icon_name('edit-find-replace', gtk.ICON_SIZE_MENU)
