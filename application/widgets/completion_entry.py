import os
import re
import gtk


class PathCompletionEntry(gtk.Entry):
	number_split = re.compile('([0-9]+)')

	def __init__(self, application):
		gtk.Entry.__init__(self)

		# store application locally for later use
		self._application = application
		self._network_path_completion = self._application.options.get('network_path_completion')

		# create suggestion list
		self._store = gtk.ListStore(str)
		self._store.set_sort_column_id(0, gtk.SORT_ASCENDING)
		self._store.set_sort_func(0, self._sort_list)

		# create entry field with completion
		self._completion = gtk.EntryCompletion()
		self._completion.set_model(self._store)
		self._completion.set_text_column(0)
		self._completion.set_inline_completion(True)
		self._completion.set_inline_selection(True)

		# configure entry
		self.set_completion(self._completion)

		# TODO: Add delayed populate to avoid spamming
		self.connect('changed', self._populate_list)

	def _populate_list(self, widget, data=None):
		"""Populate a list of file names from entered path."""
		self._store.clear()
		original_path = widget.get_text()
		directory = os.path.dirname(original_path)

		# separate protocol from path
		if '://' not in original_path:
			scheme = 'file'

		else:
			scheme = original_path.split('://', 1)[1]

		# get associated provider
		Provider = self._application.get_provider_by_protocol(scheme)
		can_lookup = Provider.is_local or self._network_path_completion

		if Provider is not None and can_lookup:
			provider = Provider(self._application)

			# make sure path exists
			if not provider.exists(directory):
				return

			# populate list
			item_list = provider.list_dir(directory)
			item_list = filter(lambda path: provider.is_dir(path, relative_to=directory), item_list)
			map(lambda path: self._store.append((os.path.join(directory, path),)), item_list)

	def _sort_list(self, item_list, iter1, iter2, data=None):
		"""Compare two items for sorting process."""
		value1 = item_list.get_value(iter1, 0)
		value2 = item_list.get_value(iter2, 0)

		value1 = value1.lower()
		value1 = [int(part) if part.isdigit() else part for part in self.number_split.split(value1)]

		if value2 is not None:
			value2 = value2.lower()
			value2 = [int(part) if part.isdigit() else part for part in self.number_split.split(value2)]

		return cmp(value1, value2)
