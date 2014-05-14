import os
import gio

from plugin_base.monitor import Monitor, MonitorSignals, MonitorError


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
		}

	# old versions of GIO don't support this signal
	if cmp(gio.pygio_version, (2, 20, 0)) == 1:
		_signal_table[gio.FILE_MONITOR_EVENT_MOVED] = MonitorSignals.MOVED


	def __init__(self, provider, path):
		Monitor.__init__(self, provider, path)

		if os.path.exists(self._path):
			try: 
				# create file/directory monitor
				if os.path.isdir(self._path):
					self._monitor = gio.File(path).monitor_directory()

				else:
					self._monitor = gio.File(path).monitor_file()

			except gio.Error:
				raise MonitorError('Error creating monitor')

			else:
				# connect signal
				self._monitor.connect('changed', self._changed)

		else:
			# invalid path, raise exception
			raise MonitorError('Unable to create monitor. Invalid path!')

	def _changed(self, monitor, path, other_path, event_type):
		"""Handle GIO signal"""
		signal = self._signal_table[event_type]
		if path is not None:
			path = path.get_basename()

		if other_path is not None:
			other_path = other_path.get_basename()

		self._emit_signal(signal, path, other_path)

	def cancel(self):
		"""Cancel monitoring"""
		if self._monitor is not None:
			self._monitor.cancel()

	def is_manual(self):
		"""Check if monitor solely relies on queues"""
		return False
