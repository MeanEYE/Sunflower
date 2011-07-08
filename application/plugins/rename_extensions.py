from plugin_base.rename_extension import RenameExtension


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_rename_extension('default', DefaultRename)
	

class DefaultRename(RenameExtension):
	"""Default rename extension support"""
	
	def __init__(self, parent):
		super(DefaultRename, self).__init__(parent)

		# default option needs to be active by default		
		self._checkbox_active.set_active(True)
		
	def get_title(self):
		"""Return extension title"""
		return _('Basic')
	
	def get_new_name(self, file_name, old_name):
		"""Get modified name"""
		return old_name