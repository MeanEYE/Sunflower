import gobject

from Queue import Queue, Empty as QueueEmptyException
from threading import Event


class MonitorError(Exception): pass


class MonitorSignals:
	CHANGED = 0  # file changed
	CHANGES_DONE = 1  # a hint that this was probably the last change in a set
	DELETED = 2  # file was deleted
	CREATED = 3  # file was created
	ATTRIBUTE_CHANGED = 4  # attribute was changed
	PRE_UNMOUNT = 5  # location will soon be unmounted
	UNMOUNTED = 6  # location was unmounted
	MOVED = 7  # file was moved


class Monitor(gobject.GObject):
	"""File system monitor base class.

	Monitors are used to watch over a specific path on file system
	specific to provider that created the monitor. They are created and
	destroyed automatically on each path change and mainly used by file
	lists but could have other usages.

	"""

	__gtype_name__ = 'Sunflower_Monitor'	
	__gsignals__ = {
				'changed': (gobject.SIGNAL_RUN_LAST, None, (int, str, str)),
			}
	
	def __init__(self, provider, path):
		gobject.GObject.__init__(self)

		self._path = path
		self._provider = provider
		self._monitor = None
		self._paused = Event()
		
		# clear initial value
		self._paused.clear()

	def _emit_signal(self, signal, path, other_path):
		"""Notify connected objects that monitored path was changed.

		Use other_path in cases where it seems logical, like moving files.
		Otherwise None should be used instead. Paths needs to be relative to
		path specified in constructor.
		
		"""
		if not self._paused.is_set():
			self.emit('changed', signal, path, other_path)

	def is_queue_based(self):
		"""Is monitor queue based"""
		return False

	def pause(self):
		"""Pause monitoring"""
		self._paused.set()

	def resume(self):
		"""Resume monitoring"""
		self._paused.clear()

	def cancel(self):
		"""Cancel monitoring"""
		pass

	def get_queue(self):
		"""Return monitor queue"""
		return None


class ManualMonitor(Monitor):
	"""Fallback monitor class.

	This monitor is designed to periodically emit signals by reading
	events from its queue. This class was designed to provide monitor-like
	functionality to providers which don't support file system notifications,
	for example remote mounts and archives. Events queue is populated by
	the operation threads themselves.

	"""

	TIMEOUT = 1000

	def __init__(self, provider, path):
		Monitor.__init__(self, provider, path)

		self._queue = Queue()
		self._start_interval()

	def _start_interval(self):
		"""Start periodical event emission"""
		gobject.timeout_add(self.TIMEOUT, self._handle_interval)

	def _handle_interval(self):
		"""Handle notification interval"""
		events = []

		# get all events from the queue
		while True:
			try:
				# try to get another event
				events.append(self._queue.get(False))

			except QueueEmptyException:
				# no more events in the queue
				break

		# emit events from a set
		for event in set(events):
			self._emit_signal(*event)

		# if paused break inteval cycle
		return not self._paused.isSet()

	def is_queue_based(self):
		"""Is monitor queue based"""
		return True

	def resume(self):
		"""Resume monitoring"""
		Monitor.resume(self)
		self._start_interval()

	def cancel(self):
		"""Cancel monitoring"""
		self.pause()

	def get_queue(self):
		"""Return queue object"""
		return self._queue
