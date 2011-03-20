class ToolbarFactory:
	"""This factory provides methods used to create and configure widgets located
	on toolbar in main program window."""

	def __init__(self, application):
		self._application = application

	def get_types(self):
		"""Return dictionary of widget types this factory can create.

		Result needs to be dictionary with widget type and description.
		Type is used to provide factory with configuration for specified item
		while description is user friendly representation of widget.

		result = {
			'bookmark_button': _('Bookmark button')
		}

		"""
		pass

	def create_widget(self, widget_type):
		"""Show dialog for creating a new widget. This method returns
		dictionary with widget specific configuration"""
		pass

	def configure_widget(self, widget_type, config):
		"""Present blockinig configuration dialog for specified widget type."""
		pass

	def get_widget(self, widget_type, config):
		"""Return newly created widget based on type and configuration."""
		pass
