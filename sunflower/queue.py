from gi.repository import Gtk

from threading import Lock
from queue import Queue, Empty


class OperationQueue:
	"""Generic, multi-name, operation queueing support class."""
	_queue_list = {}
	_active_list = {}
	_list_store = None
	_lock = Lock()

	COLUMN_TEXT = 0
	COLUMN_TYPE = 1

	TYPE_QUEUE = 0
	TYPE_NONE = 1
	TYPE_NEW = 2
	TYPE_SEPARATOR = 3

	@classmethod
	def __update_list(cls):
		"""Update list store to contain all the queues."""
		# clear options
		cls._list_store.clear()

		# add no queue option
		cls._list_store.append((_('None'), cls.TYPE_NONE))

		# create default queue
		default_name = _('Default')
		if default_name not in cls._queue_list:
			cls._lock.acquire()
			cls._queue_list[default_name] = Queue()
			cls._active_list[default_name] = False
			cls._lock.release()

		# add queues
		for name in cls._queue_list.keys():
			cls._list_store.append((name, cls.TYPE_QUEUE))

		# add option for new queue
		cls._list_store.append((None, cls.TYPE_SEPARATOR))
		cls._list_store.append((_('New queue'), cls.TYPE_NEW))

	@classmethod
	def add(cls, name, event):
		"""Add operation to queue."""
		# make sure queue exists
		if name not in cls._queue_list:
			cls._lock.acquire()
			cls._queue_list[name] = Queue()
			cls._active_list[name] = False
			cls._lock.release()
			cls.__update_list()

		# add operation to specified queue
		cls._queue_list[name].put(event, False)

		# start operation immediately if queue is empty
		if not cls._active_list[name]:
			cls._lock.acquire()
			cls._active_list[name] = True
			cls._lock.release()
			cls.start_next(name)

	@classmethod
	def start_next(cls, name):
		"""Start next operation in specified queue."""
		if name not in cls._queue_list:
			return

		# get operation event and clear it
		try:
			event = cls._queue_list[name].get(False)

		except Empty:
			# last operation finished, mark as inactive
			cls._lock.acquire()
			cls._active_list[name] = False
			cls._lock.release()

		else:
			event.set()

	@classmethod
	def get_list(cls):
		"""Return list of available queues."""
		return cls._queue_list.keys()

	@classmethod
	def get_model(cls):
		"""Return model to be used with different widgets."""
		if cls._list_store is None:
			cls._list_store = Gtk.ListStore(str, int)
			cls.__update_list()

		return cls._list_store

	@classmethod
	def get_name_from_iter(cls, selected_iter):
		"""Get queue name from specified iter."""
		result = None

		if selected_iter is not None:
			selection_type = cls._list_store.get_value(selected_iter, cls.COLUMN_TYPE)

			if selection_type is cls.TYPE_QUEUE:
				result = cls._list_store.get_value(selected_iter, cls.COLUMN_TEXT)

		return result

	@classmethod
	def handle_separator_check(cls, model, current_iter, data=None):
		"""Test if specified iter is a separator."""
		return model.get_value(current_iter, cls.COLUMN_TYPE) == cls.TYPE_SEPARATOR

	@classmethod
	def handle_queue_select(cls, widget, dialog):
		"""Handle changing operation queue or adding a new one."""
		selected_iter = widget.get_active_iter()
		if selected_iter is None:
			return False

		model = widget.get_model()
		option_type = model.get_value(selected_iter, cls.COLUMN_TYPE)

		# we handle only new option selection
		if option_type != cls.TYPE_NEW:
			return False

		# import locally to avoid circular imports
		from gui.input_dialog import InputDialog

		# create dialog
		dialog = InputDialog(dialog)
		dialog.set_title(_('New operation queue'))
		dialog.set_label(_('Enter name for new operation queue:'))

		# get response from the user
		response = dialog.get_response()

		if response[0] != Gtk.ResponseType.OK:
			widget.set_active(0)
			return False

		# make sure queue doesn't already exist
		if response[1] in cls._queue_list:
			dialog = Gtk.MessageDialog(
									dialog,
									Gtk.DialogFlags.DESTROY_WITH_PARENT,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.OK,
									_('Operation queue with specified name already exists.')
								)
			dialog.run()
			dialog.destroy()
			return False

		# select newly added queue
		cls._lock.acquire()
		cls._queue_list[response[1]] = Queue()
		cls._active_list[response[1]] = False
		cls._lock.release()
		cls.__update_list()

		queue_index = 0
		for index, row in enumerate(cls._list_store):
			if row[0] == response[1]:
				queue_index = index
				break

		widget.set_active(queue_index)

		return True
