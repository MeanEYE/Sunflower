import gtk

from widgets.settings_page import SettingsPage


class OperationOptions(SettingsPage):
	"""Operation options extension class"""
	
	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'operation', _('Operation'))

		# create frames
		frame_general = gtk.Frame(_('General'))
		vbox_general = gtk.VBox(False, 0)
		vbox_general.set_border_width(5)

		frame_mounts = gtk.Frame(_('Mounts'))
		vbox_mounts = gtk.VBox(False, 0)
		vbox_mounts.set_border_width(5)

		# create components
		self._checkbox_trash_files = gtk.CheckButton(_('Delete items to trash can'))
		self._checkbox_reserve_size = gtk.CheckButton(_('Reserve free space on copy/move'))
		self._checkbox_automount_on_start = gtk.CheckButton(_('Automount drives on start up'))
		self._checkbox_automount_on_insert = gtk.CheckButton(_('Automount removable drives when inserted'))

		self._checkbox_trash_files.connect('toggled', self._parent.enable_save)
		self._checkbox_reserve_size.connect('toggled', self._parent.enable_save)
		self._checkbox_automount_on_start.connect('toggled', self._parent.enable_save)
		self._checkbox_automount_on_insert.connect('toggled', self._parent.enable_save)

		# pack user interface
		vbox_general.pack_start(self._checkbox_trash_files, False, False, 0)
		vbox_general.pack_start(self._checkbox_reserve_size, False, False, 0)

		vbox_mounts.pack_start(self._checkbox_automount_on_start, False, False, 0)
		vbox_mounts.pack_start(self._checkbox_automount_on_insert, False, False, 0)

		frame_general.add(vbox_general)
		frame_mounts.add(vbox_mounts)

		self.pack_start(frame_general, False, False, 0)
		self.pack_start(frame_mounts, False, False, 0)

	def _load_options(self):
		"""Load item list options"""
		options = self._application.options
		section = options.section('operations')

		# load options
		self._checkbox_trash_files.set_active(section.get('trash_files'))
		self._checkbox_reserve_size.set_active(section.get('reserve_size'))
		self._checkbox_automount_on_start.set_active(section.get('automount_start'))
		self._checkbox_automount_on_insert.set_active(section.get('automount_insert'))

	def _save_options(self):
		"""Save item list options"""
		options = self._application.options
		section = options.section('operations')

		# save settings
		section.set('trash_files', self._checkbox_trash_files.get_active())
		section.set('reserve_size', self._checkbox_reserve_size.get_active())
		section.set('automount_start', self._checkbox_automount_on_start.get_active())
		section.set('automount_insert', self._checkbox_automount_on_insert.get_active())
