import gtk

from plugin_base.toolbar_factory import ToolbarFactory

# import controls
from bookmark_button import Button as BookmarkButton, ConfigurationDialog as BookmarkButton_Dialog
from bookmarks_button import Button as BookmarksButton
from home_directory_button import Button as HomeDirectoryButton
from parent_directory_button import Button as ParentDirectoryButton
from separator import Separator


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_toolbar_factory(DefaultToolbar)


class DefaultToolbar(ToolbarFactory):
	"""Default toolbar factory implementation for Sunflower."""

	def __init__(self, application):
		ToolbarFactory.__init__(self, application)

		self._widgets = {
		        'parent_directory_button': {
		            'description': _('Parent directory button'),
		            'icon': gtk.STOCK_GO_UP,
		            'dialog': None,
		            'class': ParentDirectoryButton,
		        },
		        'home_directory_button': {
		            'description': _('Home directory button'),
		            'icon': 'user-home',
		            'dialog': None,
		            'class': HomeDirectoryButton,
		        },
		        'bookmark_button': {
		            'description': _('Bookmark button'),
		            'icon': 'folder',
		            'dialog': BookmarkButton_Dialog,
		            'class': BookmarkButton,
		        },
		        'bookmarks_button': {
		            'description': _('Bookmarks menu'),
		            'icon': 'go-jump',
		            'dialog': None,
		            'class': BookmarksButton,
		        },
		        'separator': {
		            'description': _('Separator'),
		            'icon': '',
		            'dialog': None,
		            'class': Separator,
		        },
		    }

	def get_types(self):
		"""Return supported widget types"""
		widget_list = []

		for key, data in self._widgets.items():
			widget_list.append((key, (data['description'], data['icon'])))

		widget_list.sort()

		return dict(widget_list)

	def create_widget(self, name, widget_type, transient_window=None):
		"""Show widget creation dialog"""
		config = {}
		DialogClass = self._widgets[widget_type]['dialog']

		if DialogClass is not None:
			# create configuration dialog
			dialog = DialogClass(self._application, name)

			# set transistent window
			if transient_window is not None:
				dialog.set_transient_for(transient_window)

			# get config
			config = dialog.get_response()

		return config

	def configure_widget(self, name, widget_type, config):
		"""Configure specified widget"""
		result = None
		DialogClass = self._widgets[widget_type]['dialog']

		if DialogClass is not None:
			# create configuration dialog
			dialog = DialogClass(self._application, name, config)

			# show dialog and get use input
			result = dialog.get_response()

		else:
			# there is no configuration dialog for this widget type
			dialog = gtk.MessageDialog(
		                            self._application,
		                            gtk.DIALOG_DESTROY_WITH_PARENT,
		                            gtk.MESSAGE_INFO,
		                            gtk.BUTTONS_OK,
		                            _("This widget has no configuration dialog.")
		                        )
			dialog.run()
			dialog.destroy()

		return result

	def get_widget(self, name, widget_type, config):
		"""Return newly created widget based on type and configuration."""
		result = None

		if widget_type in self._widgets \
		and self._widgets[widget_type]['class'] is not None:
			# create widget
			WidgetClass = self._widgets[widget_type]['class']
			result = WidgetClass(self._application, name, config)

		return result
