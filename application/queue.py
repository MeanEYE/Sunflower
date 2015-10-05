import gtk

from Queue import Queue


class OperationQueue:
	"""Generic, multi-name, queueing support class."""

	_queue_list = {}
	_list_store = None

	COLUMN_TEXT = 0
	COLUMN_TYPE = 1

	TYPE_QUEUE = 0
	TYPE_NONE = 1
	TYPE_NEW = 2
	TYPE_SEPARATOR = 3

	def __init__(self):
		pass

	@classmethod
	def __update_list(cls):
		"""Update list store to contain all the queues."""
		cls._list_store.clear()

		# add no queue option
		cls._list_store.append((_('None'), cls.TYPE_NONE))

		# create default queue
		default_name = _('Default')
		if default_name not in cls._queue_list:
			cls._queue_list[default_name] = Queue()

		# add queues
		for name in cls._queue_list.keys():
			cls._list_store.append((name, cls.TYPE_QUEUE))

		# add option for new queue
		cls._list_store.append((None, cls.TYPE_SEPARATOR))
		cls._list_store.append((_('New queue'), cls.TYPE_NEW))

	@classmethod
	def add(cls, name, operation):
		"""Add operation to queue."""
		# make sure queue exists
		if name not in cls._queue_list:
			cls._queue_list[name] = Queue()
			cls.__update_list()

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

		# get operation and call it
		operation = cls._queue_list.get(False)
		if hasattr(operation, 'resume'):
			operation.resume()

	@classmethod
	def get_list(cls):
		"""Return list of available queues."""
		return cls._queue_list.keys()

	@classmethod
	def get_model(cls):
		"""Return model to be used with different widgets."""
		if cls._list_store is None:
			cls._list_store = gtk.ListStore(str, int)
			cls.__update_list()

		return cls._list_store

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

		if response[0] != gtk.RESPONSE_OK:
			return False

		# make sure queue doesn't already exist
		if response[1] in cls._queue_list:
			dialog = gtk.MessageDialog(
									dialog,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_ERROR,
									gtk.BUTTONS_OK,
									_('Operation queue with specified name already exists.')
								)
			dialog.run()
			dialog.destroy()
			return False

		# select newly added queue
		cls._queue_list[response[1]] = Queue()
		cls.__update_list()

		queue_index = 0
		for index, row in enumerate(cls._list_store):
			if row[0] == response[1]:
				queue_index = index
				break

		widget.set_active(queue_index)

		return True
