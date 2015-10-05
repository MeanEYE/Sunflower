from Queue import Queue


class OperationQueue:
	"""Generic, multi-name, queueing support class."""

	_queue_list = {}

	def __init__(self):
		pass

	@classmethod
	def add(cls, name, operation):
		"""Add operation to queue."""
		# make sure queue exists
		if name not in cls._queue_list:
			cls._queue_list[name] = Queue()

		# add operation to specified queue
		self._queue_list[name].put(operation, False)

		# pause operation so we can resume later
		if hasattr(operation, 'pause'):
			operation.pause()

	@classmethod
	def start_next(cls, name):
		"""Start next operation in specified queueself."""
		if name not in cls._queue_list:
			return

		# get operaiton and call it
		operation = cls._queue_list.get(False)
		if hasattr(operation, 'resume'):
			operation.resume()

	@classmethod
	def get_list(cls):
		"""Return list of available queues."""
		return cls._queue_list.keys()
