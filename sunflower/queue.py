from __future__ import absolute_import

from threading import Lock
from queue import Queue, Empty


class OperationQueue:
	"""Fixed set of operation queues.

	Operations added to the same queue run one after another. Each queue
	is identified by a number and has a color used to mark its operations
	in the interface. `None` stands for no queue at all.

	"""
	QUEUES = (1, 2, 3)
	COLORS = {  # red, green and blue components
			1: (0.208, 0.518, 0.894),  # blue
			2: (0.878, 0.106, 0.141),  # red
			3: (0.180, 0.761, 0.494)  # green
		}

	_queue_list = {queue: Queue() for queue in QUEUES}
	_active_list = {queue: False for queue in QUEUES}
	_lock = Lock()

	@classmethod
	def add(cls, queue, event):
		"""Add operation to queue."""
		start = False

		with cls._lock:
			cls._queue_list[queue].put(event, False)

			# start operation immediately if queue is idle
			if not cls._active_list[queue]:
				cls._active_list[queue] = True
				start = True

		if start:
			cls.start_next(queue)

	@classmethod
	def start_next(cls, queue):
		"""Start next operation in specified queue."""
		if queue not in cls._queue_list:
			return

		with cls._lock:
			# get operation event and set it
			try:
				event = cls._queue_list[queue].get(False)

			except Empty:
				# last operation finished, mark as inactive
				cls._active_list[queue] = False

			else:
				event.set()

	@classmethod
	def get_color(cls, queue):
		"""Return color components for specified queue."""
		return cls.COLORS.get(queue)
