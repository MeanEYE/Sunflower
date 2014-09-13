import os

from gi.repository import Gio
from plugin_base.monitor import Monitor, MonitorSignals, MonitorError


class LocalMonitor(Monitor):
	"""Local file monitor based on GIO"""

	# signals translation table
	_signal_table = {
			Gio.FileMonitorEvent.CHANGED: MonitorSignals.CHANGED,
			Gio.FileMonitorEvent.CHANGES_DONE_HINT: MonitorSignals.CHANGES_DONE,
			Gio.FileMonitorEvent.DELETED: MonitorSignals.DELETED,
			Gio.FileMonitorEvent.CREATED: MonitorSignals.CREATED,
			Gio.FileMonitorEvent.ATTRIBUTE_CHANGED: MonitorSignals.ATTRIBUTE_CHANGED,
			Gio.FileMonitorEvent.PRE_UNMOUNT: MonitorSignals.PRE_UNMOUNT,
			Gio.FileMonitorEvent.UNMOUNTED: MonitorSignals.UNMOUNTED,
		}

	# old versions of GIO don't support this signal
	if cmp(Gio.pygio_version, (2, 20, 0)) == 1:
		_signal_table[Gio.FileMonitorEvent.MOVED] = MonitorSignals.MOVED


	def __init__(self, provider, path):
		Monitor.__init__(self, provider, path)

		if os.path.exists(self._path):
			try:
				# create file/directory monitor
				if os.path.isdir(self._path):
					self._monitor = Gio.File(path).monitor_directory()

				else:
					self._monitor = Gio.File(path).monitor_file()

			except Gio.Error:
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
