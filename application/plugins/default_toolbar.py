import os
import gtk

from plugin_base.toolbar_factory import ToolbarFactory


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_toolbar_factory(DefaultToolbar)


class DefaultToolbar(ToolbarFactory):
	"""Default toolbar factory implementation for Sunflower."""

	def __init__(self, application):
		ToolbarFactory.__init__(self, application)

		self._widgets = {
		        'bookmark_button': {
		            'description': _('Bookmark button'),
		            'dialog': BookmarkButton_Dialog,
		            'class': BookmarkButton,
		        },
		        'separator': {
		            'description': _('Separator'),
		            'dialog': None,
		            'class': Separator,
		        },
		    }

	def get_types(self):
		"""Return supported widget types"""
		list_ = []

		for key, data in self._widgets.items():
			list_.append((key, data['description']))

		list_.sort()

		return dict(list_)

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
		                            _("This widget type has no configuration dialog.")
		                        )
			dialog.run()
			dialog.destroy()

		return result

	def get_widget(self, name, widget_type, config):
		"""Return newly created widget based on type and configuration."""
		result = None

		if self._widgets.has_key(widget_type) \
		and self._widgets[widget_type]['class'] is not None:
			# create widget
			WidgetClass = self._widgets[widget_type]['class']
			result = WidgetClass(self._application, name, config)

		return result


class BookmarkButton(gtk.ToolButton):
	"""Bookmark toolbar button"""

	def __init__(self, application, name, config):
		gtk.ToolButton.__init__(self)

		self._path = os.path.expanduser(config['path'])
		self._application = application

		# configure button
		self.set_label(name)
		self.set_icon_name('folder')
		self.set_tooltip_text(name)

		# show label if specified
		self.set_is_important(config['show_label'] == 'True')

		self.connect('clicked', self._clicked)

	def _clicked(self, widget, data=None):
		"""Handle click"""
		active_object = self._application._get_active_object()

		if hasattr(active_object, 'change_path'):
			active_object.change_path(self._path)


class BookmarkButton_Dialog(gtk.Dialog):
	"""Configuration dialog for bookmark button"""

	def __init__(self, application, name, config=None):
		gtk.Dialog.__init__(self, parent=application)

		self._application = application

		# configure dialog
		self.set_title(_('Configure bookmark button'))
		self.set_default_size(340, 10)
		self.set_resizable(True)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(application)

		self.vbox.set_spacing(0)

		# interface container
		vbox = gtk.VBox(False, 5)
		vbox.set_border_width(5)

		# create interface
		vbox_name = gtk.VBox(False, 0)

		label_name = gtk.Label(_('Name:'))
		label_name.set_alignment(0, 0.5)

		entry_name = gtk.Entry()
		entry_name.set_editable(False)
		entry_name.set_sensitive(False)
		entry_name.set_text(name)

		vbox_path = gtk.VBox(False, 0)

		label_path = gtk.Label(_('Path:'))
		label_path.set_alignment(0, 0.5)

		self._entry_path = gtk.Entry()
		self._checkbox_show_label = gtk.CheckButton(_('Show label'))

		# load default values
		if config is not None:
			self._entry_path.set_text(config['path'])
			self._checkbox_show_label.set_active(config['show_label'] == 'True')

		# create controls
		button_save = gtk.Button(stock=gtk.STOCK_SAVE)
		button_save.set_can_default(True)
		button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

		self.add_action_widget(button_cancel, gtk.RESPONSE_CANCEL)
		self.add_action_widget(button_save, gtk.RESPONSE_ACCEPT)

		self.set_default_response(gtk.RESPONSE_ACCEPT)

		# pack interface
		vbox_name.pack_start(label_name, False, False, 0)
		vbox_name.pack_start(entry_name, False, False, 0)

		vbox_path.pack_start(label_path, False, False, 0)
		vbox_path.pack_start(self._entry_path, False, False, 0)

		vbox.pack_start(vbox_name, False, False, 0)
		vbox.pack_start(vbox_path, False, False, 0)
		vbox.pack_start(self._checkbox_show_label, False, False, 0)

		self.vbox.pack_start(vbox, False, False, 0)

		self.show_all()

	def get_response(self):
		"""Return dialog response and self-destruct"""
		config = None

		# show dialog
		code = self.run()

		if code == gtk.RESPONSE_ACCEPT:
			config = {
			    'path': self._entry_path.get_text(),
			    'show_label': self._checkbox_show_label.get_active()
			    }

		self.destroy()

		return config


class Separator(gtk.SeparatorToolItem):
	"""Toolbar separator widget"""

	def __init__(self, application, name, config):
		gtk.SeparatorToolItem.__init__(self)
