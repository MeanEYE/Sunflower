import os
import gio

from monitor import Monitor, MonitorSignals, MonitorError


class LocalMonitor(Monitor):
	"""Local file monitor based on GIO"""

	# signals translation table
	_signal_table = {
			gio.FILE_MONITOR_EVENT_CHANGED: MonitorSignals.CHANGED,
			gio.FILE_MONITOR_EVENT_CHANGES_DONE_HINT: MonitorSignals.CHANGES_DONE,
			gio.FILE_MONITOR_EVENT_DELETED: MonitorSignals.DELETED,
			gio.FILE_MONITOR_EVENT_CREATED: MonitorSignals.CREATED,
			gio.FILE_MONITOR_EVENT_ATTRIBUTE_CHANGED: MonitorSignals.ATTRIBUTE_CHANGED,
			gio.FILE_MONITOR_EVENT_PRE_UNMOUNT: MonitorSignals.PRE_UNMOUNT,
			gio.FILE_MONITOR_EVENT_UNMOUNTED: MonitorSignals.UNMOUNTED,
			gio.FILE_MONITOR_EVENT_MOVED: MonitorSignals.MOVED,
		}

	def __init__(self, provider, path):
		Monitor.__init__(self, provider)

		if os.path.exists(self._path):
			# create file/directory monitor
			if os.path.is_dir(self._path):
				self._monitor = gio.File(path).monitor_directory()

			else:
				self._monitor = gio.File(path).monitor_file()

		else:
			# invalid path, raise exception
			raise MonitorError('Unable to create monito. Invalid path!')

	def _changed(self, monitor, path, other_path, event_type):
		"""Handle GIO signal"""
		signal = self._signal_table[event_type]
		self._emit_signal(signal, path, other_path)

	def cancel(self):
		"""Cancel monitoring"""
		if self._monitor is not None:
			self._monitor.cancel()
