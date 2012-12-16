import gtk


class ColumnExtension:
	"""Class used for extending item lists. 
	
	Object of this class is created for every tab individually 
	and for this reason class parameters are higly discouraged 
	unless you know what you are doing.

	"""
	
	def __init__(self, parent, store):
		self._parent = parent
		self._store = store
		self._column = None

	def _create_column(self):
		"""Create column"""
		pass

	def get_column(self):
		"""Get column object to be added to the list"""
		pass
