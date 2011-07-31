from plugin_base.find_extension import FindExtension


def register_plugin(application):
	"""register plugin classes with application"""
	application.register_find_extension('default', DefaultFindFiles)


class DefaultFindFiles(FindExtension):
	"""Default extension for find files tool"""

	def __init__(self, parent):
		FindExtension.__init__(self, parent)
	
		# enabled by default
		self._checkbox_active.set_active(True)

	def get_title(self):
		"""Return i18n title for extension"""
		return _('Basic')

	def is_file_ok(self, path):
		"""Check is specified path fits the cirteria"""
		return True
