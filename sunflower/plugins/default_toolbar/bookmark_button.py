import os

from gi.repository import Gtk, GObject

from sunflower.plugins.default_toolbar import ToolbarButton


class Button(ToolbarButton):
	"""Bookmark toolbar button"""

	def __init__(self, application, name, config):
		GObject.GObject.__init__(self)

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


class ConfigurationDialog(Gtk.Dialog):
	"""Configuration dialog for bookmark button"""

	def __init__(self, application, name, config=None):
		Gtk.Dialog.__init__(
			self,
			parent=application,
			use_header_bar=True,
		)

		self._application = application

		# configure dialog
		self.set_title(_('Configure bookmark button'))
		self.set_default_size(450, 10)
		self.set_resizable(True)
		self.set_modal(True)
		self.set_transient_for(application)

		self.get_content_area().set_spacing(0)

		# interface container
		vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
		set_border_width(vbox, 5)

		# create interface
		vbox_path = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

		label_path = Gtk.Label(label=_('Path:'))
		label_path.set_xalign(0)
		label_path.set_yalign(0.5)

		self._entry_path = Gtk.Entry()
		self._checkbox_show_label = Gtk.CheckButton.new_with_label(_('Show label'))

		# load default values
		if config is not None:
			self._entry_path.set_text(config['path'])
			self._checkbox_show_label.set_active(config['show_label'] == True)

		# create controls
		button_save = Gtk.Button.new_with_label(_('Save'))
		if Gtk.get_major_version() == 3:
			button_save.set_can_default(True)
		button_cancel = Gtk.Button.new_with_label(_('Cancel'))

		self.add_action_widget(button_cancel, Gtk.ResponseType.CANCEL)
		self.add_action_widget(button_save, Gtk.ResponseType.ACCEPT)

		self.set_default_response(Gtk.ResponseType.ACCEPT)

		# pack interface
		if Gtk.get_major_version() == 3:
			vbox_path.pack_start(label_path, False, False, 0)
			vbox_path.pack_start(self._entry_path, False, False, 0)

			vbox.pack_start(vbox_path, False, False, 0)
			vbox.pack_start(self._checkbox_show_label, False, False, 0)

			self.vbox.pack_start(vbox, False, False, 0)

			self.show_all()

		else:
			vbox_path.append(label_path)
			vbox_path.append(self._entry_path)

			vbox.append(vbox_path)
			vbox.append(self._checkbox_show_label)

			self.get_content_area().append(vbox)

			self.show()

	def get_response(self):
		"""Return dialog response and self-destruct"""
		config = None

		# show dialog
		code = run_dialog(self)

		if code == Gtk.ResponseType.ACCEPT:
			config = {
			    'path': self._entry_path.get_text(),
			    'show_label': self._checkbox_show_label.get_active()
			    }

		self.destroy()

		return config
