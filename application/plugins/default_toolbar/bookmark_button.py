import os
import gtk


class Button(gtk.ToolButton):
	"""Bookmark toolbar button"""

	def __init__(self, application, name, config):
		gtk.ToolButton.__init__(self)

		self._name = name
		self._config = config
		self._application = application
		self._path = None

		# configure button
		self._set_label()
		self._set_icon()

		# show label if specified
		if 'show_label' in self._config:
			important = self._config['show_label'] in ('True', True)
			self.set_is_important(important)

		if 'path' in self._config:
			self._path = os.path.expanduser(self._config['path'])

		# connect signals
		self.connect('clicked', self._clicked)

	def _set_label(self):
		"""Set button label"""
		self.set_label(self._name)
		self.set_tooltip_text(self._name)

	def _set_icon(self):
		"""Set button icon"""
		icon_name = self._application.icon_manager.get_icon_for_directory(self._path)
		self.set_icon_name(icon_name)

	def _clicked(self, widget, data=None):
		"""Handle click"""
		active_object = self._application.get_active_object()

		if hasattr(active_object, 'change_path'):
			active_object.change_path(self._path)


class ConfigurationDialog(gtk.Dialog):
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
			self._checkbox_show_label.set_active(config['show_label'] == True)

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
