class ToolbarFactory:
	"""This factory provides methods used to create and configure widgets located
	on toolbar in main program window."""

	def __init__(self, application):
		self._application = application

	def get_types(self):
		"""Return dictionary of widget types this factory can create.

		Result needs to be dictionary with widget type as key and touple
		containing icon name and description as value.
		Type is used to provide factory with configuration for specified item
		while description is user friendly representation of widget.

		result = {
			'bookmark_button': (
						_('Bookmark button'),
						icon_name
					),
		}

		"""
		pass

	def create_widget(self, name, widget_type, transient_window=None):
		"""Show dialog for creating a new widget. This method returns
		dictionary with widget specific configuration or None in case
		user canceled.

		result = {
			'some_key': 'value to be stored',
		}

		"""
		pass

	def configure_widget(self, name, widget_type, config):
		"""Present blocking configuration dialog for specified widget type.

		Returns new config if changes were made otherwise None

		"""
		pass

	def get_widget(self, name, widget_type, config):
		"""Return newly created widget based on type and configuration."""
		pass
