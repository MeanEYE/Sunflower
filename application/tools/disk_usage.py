import os

from threading import Thread, Event, Lock
from plugin_base.monitor import MonitorSignals


class DiskUsage:
	"""Dedicated object for counting disk usage for specified directories."""

	def __init__(self, application):
		self._stop_events = {}
		self._sizes = {}
		self._counts = {}
		self._lock = Lock()

	def __update_totals(self, path, total_count, total_size):
		"""Update global dictionaries with new statistics."""
		self._lock.acquire()
		self._sizes[path] = total_size
		self._counts[path] = total_count
		self._lock.release()

	def __calculate_usage(self, monitor_queue, provider, path, stop_event):
		"""Threaded method used for calculating disk usage."""
		total_count = 0L
		total_size = 0L
		scan_list = []

		# add initial path for scanning
		scan_list.append(path)

		# loop through all paths and calculate
		while not stop_event.is_set():
			# get path for scanning
			try:
				scan_path = scan_list.pop(0)

			except IndexError:
				# no more directories to traverse
				self.__update_totals(path, total_count, total_size)
				monitor_queue.put((MonitorSignals.DIRECTORY_SIZE_CHANGED, path, None), False)
				stop_event.set()
				continue

			# get list of items in specified directory
			item_list = provider.list_dir(scan_path, relative_to=path)
			relative_path = os.path.join(path, scan_path)

			for item in item_list:
				if provider.is_dir(item, relative_to=relative_path):
					# queue up new directory to check
					scan_list.append(os.path.join(scan_path, item))

				else:
					# update total statistics
					stat = provider.get_stat(item, relative_to=relative_path, extended=False, follow=False)
					total_count += 1
					total_size += stat.size

				# update monitor only once in a while
				if total_count % 50 == 0:
					self.__update_totals(path, total_count, total_size)
					monitor_queue.put((MonitorSignals.DIRECTORY_SIZE_CHANGED, path, None), False)

	def get(self, path):
		"""Get statistics for specified path."""
		result = (0, 0)

		if path in self._sizes:
			result = (
					self._counts[path],
					self._sizes[path]
				)

		return result

	def calculate(self, monitor_queue, provider, path):
		"""Calculate disk usage for specified path."""
		if path in self._stop_events:
			return

		# store event to allow stopping thread early
		stop_event = Event()
		self._stop_events[path] = stop_event

		# start calculation in new thread
		Thread(target=self.__calculate_usage, args=(monitor_queue, provider, path, stop_event)).start()

	def cancel(self, path):
		"""Cancel disk usage calculation for specified path."""
		if path in self._stop_events:
			self._stop_events[path].set()
			del self._stop_events[path]
			del self._sizes[path]
			del self._counts[path]

	def cancel_all(self, parent_path):
		"""Cancel all threads calculating disk usage for child paths."""
		for path, stop_event in self._stop_events.items():
			if path.startswith(parent_path):
				stop_event.set()
				del self._stop_events[path]
				del self._sizes[path]
				del self._counts[path]
