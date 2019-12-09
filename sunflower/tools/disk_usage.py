from __future__ import absolute_import

import os

from threading import Thread, Event, Lock
from sunflower.plugin_base.monitor import MonitorSignals


class DiskUsage:
	"""Dedicated object for counting disk usage for specified directories."""

	def __init__(self, application):
		self._stop_events = {}
		self._sizes = {}
		self._counts = {}
		self._lock = Lock()

	def __update_totals(self, parent_id, path, total_count, total_size):
		"""Update global dictionaries with new statistics."""
		key = (parent_id, path)

		self._lock.acquire()
		self._sizes[key] = total_size
		self._counts[key] = total_count
		self._lock.release()

	def __calculate_usage(self, parent_id, monitor_queue, provider, path, stop_event):
		"""Threaded method used for calculating disk usage."""
		total_count = 0
		total_size = 0
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
				self.__update_totals(parent_id, path, total_count, total_size)
				monitor_queue.put((MonitorSignals.DIRECTORY_SIZE_CHANGED, path, None), False)
				stop_event.set()
				continue

			# get list of items in specified directory
			try:
				item_list = provider.list_dir(scan_path, relative_to=path)

			except OSError:
				# silently ignore errors
				continue

			else:
				relative_path = os.path.join(path, scan_path)

			for item in item_list:
				if provider.is_dir(item, relative_to=relative_path) \
				and not provider.is_link(item, relative_to=relative_path):
					# queue up new directory to check
					scan_list.append(os.path.join(scan_path, item))

				else:
					# update total statistics
					stat = provider.get_stat(item, relative_to=relative_path, extended=False, follow=False)
					total_count += 1
					total_size += stat.size

				# update monitor only once in a while
				if total_count % 50 == 0:
					self.__update_totals(parent_id, path, total_count, total_size)
					monitor_queue.put((MonitorSignals.DIRECTORY_SIZE_CHANGED, path, None), False)

		# notify monitor we are done
		monitor_queue.put((MonitorSignals.DIRECTORY_SIZE_STOPPED, path, None), False)

	def get(self, parent_object, path):
		"""Get statistics for specified path."""
		key = (id(parent_object), path)
		result = (0, 0)

		if key in self._sizes:
			result = (
					self._counts[key],
					self._sizes[key]
				)

		return result

	def calculate(self, parent_object, monitor_queue, provider, path):
		"""Calculate disk usage for specified path."""
		key = (id(parent_object), path)

		# if for some strange reason calculation is requested again
		if key in self._stop_events:
			return False

		# store event to allow stopping thread early
		stop_event = Event()
		self._stop_events[key] = stop_event

		# start calculation in new thread
		Thread(target=self.__calculate_usage, args=(key[0], monitor_queue, provider, path, stop_event)).start()

		return True

	def cancel(self, parent_object, path):
		"""Cancel disk usage calculation for specified path requested by parent_object."""
		key = (id(parent_object), path)

		if key in self._stop_events:
			# stop calculation thread
			self._stop_events[key].set()

			# remove data
			del self._stop_events[key]
			del self._sizes[key]
			del self._counts[key]

	def cancel_all(self):
		"""Cancel all calculation threads."""
		# stop all calculation threads
		for stop_event in self._stop_events.values():
			stop_event.set()

		# clear lists
		self._stop_events = {}
		self._sizes = {}
		self._counts = {}

	def cancel_all_for_object(self, parent_object):
		"""Cancel all calculation threads for specified parent object."""
		parent_id = id(parent_object)

		for key in list(self._stop_events):
			if key[0] != parent_id:
				continue

			# stop calculation thread
			self._stop_events[key].set()

			# remove data
			del self._stop_events[key]
			del self._sizes[key]
			del self._counts[key]

	def cancel_all_for_path(self, parent_path):
		"""Cancel all threads calculating disk usage for child paths."""
		for key in self._stop_events.keys():
			if not key[1].startswith(parent_path):
				# stop calculation thread
				self._stop_events[key].set()

				# remove data
				del self._stop_events[key]
				del self._sizes[key]
				del self._counts[key]
