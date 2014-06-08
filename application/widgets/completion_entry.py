import os
import gtk

class PathCompletionEntry(gtk.Entry):
	"""Entry with path completion"""

	def __init__(self, application):
		gtk.Entry.__init__(self)
		self._application = application
		entry_completion = gtk.EntryCompletion()
		self.set_completion(entry_completion)
		liststore = gtk.ListStore(str, str)
		entry_completion.set_model(liststore)
		entry_completion.set_match_func(self._match_completion)
		cell = gtk.CellRendererText()
		entry_completion.pack_start(cell)
		entry_completion.add_attribute(cell, 'text', 1)
		entry_completion.connect('match-selected', self._completion_selected)
		self.connect('changed', self._fill_completion_list, entry_completion)

	def _fill_completion_list(self, entry, entry_completion):
		"""Populate a list of file names from entered path"""
		model = entry_completion.get_model()
		model.clear()
		path = entry.get_text()
		dirname = os.path.dirname(path)

		if '://' not in path:
			scheme = 'file'

		else:
			data = path.split('://', 1)
			scheme = data[0]

		ProviderClass = self._application.get_provider_by_protocol(scheme)

		if ProviderClass is not None:
			provider = ProviderClass(self._application)
			if provider.exists(dirname):
				for item in provider.list_dir(dirname):
					if provider.is_dir(item, relative_to=dirname):
						model.append([os.path.join(dirname, item), item])

	def _match_completion(self, completion, key, iter):
		"""Match function for EntryCompletion"""
		model = completion.get_model()
		dir = model.get_value(iter, 0)
		return True if dir and dir.startswith(key) else False

	def _completion_selected(self, completion, model, iter):
		"""Paste selected path to entry"""
		self.set_text(model[iter][0])
		self.set_position(-1)
		return True
