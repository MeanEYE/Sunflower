from __future__ import absolute_import

from gi.repository import Gtk, Gdk, GObject
from sunflower.gui.preferences.display import DisplayOptions
from sunflower.gui.preferences.operation import OperationOptions
from sunflower.gui.preferences.item_list import ItemListOptions
from sunflower.gui.preferences.terminal import TerminalOptions
from sunflower.gui.preferences.view_and_edit import ViewEditOptions
from sunflower.gui.preferences.toolbar import ToolbarOptions
from sunflower.gui.preferences.bookmarks import BookmarksOptions
from sunflower.gui.preferences.commands import CommandsOptions
from sunflower.gui.preferences.plugins import PluginsOptions
from sunflower.gui.preferences.accelerators import AcceleratorOptions
from sunflower.gui.preferences.associations import AssociationsOptions


class Column:
	NAME = 0
	WIDGET = 1


class PreferencesWindow(Gtk.Window):
	"""Container class for options editors"""

	def __init__(self, parent):
		Gtk.Window.__init__(self)

		self._parent = parent

		# configure window
		self.set_title(_('Preferences'))
		self.set_default_size(750, 500)
		self.set_modal(True)
		self.set_transient_for(parent)

		if Gtk.get_major_version() == 3:
			self.connect('delete_event', self._hide)
			self.connect('key-press-event', self._handle_key_press)

		else:
			event_controller = Gtk.EventControllerKey.new()
			event_controller.connect('key-pressed', self._handle_key_pressed)

			self.connect('close-request', self._hide)
			self.add_controller(event_controller)

		# create user interface
		header_bar = Gtk.HeaderBar.new()

		if Gtk.get_major_version() == 3:
			header_bar.set_show_close_button(True)
			header_bar.set_title(_('Preferences'))

		else:
			# GTK 4 header bar shows window title on its own
			header_bar.set_show_title_buttons(True)

		self.set_titlebar(header_bar)

		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

		# create tab stack and switcher
		self._tabs = Gtk.Stack.new()

		self._labels = Gtk.StackSidebar.new()
		self._labels.set_stack(self._tabs)
		self._labels.set_size_request(150, -1)

		DisplayOptions(self, parent)
		OperationOptions(self, parent)
		ItemListOptions(self, parent)
		TerminalOptions(self, parent)
		ViewEditOptions(self, parent)
		ToolbarOptions(self, parent)
		BookmarksOptions(self, parent)
		CommandsOptions(self, parent)
		PluginsOptions(self, parent)
		AcceleratorOptions(self, parent)
		AssociationsOptions(self, parent)

		# create buttons
		self._button_save = Gtk.Button.new_with_label(_('Save'))
		self._button_save.connect('clicked', self._save_options)
		self._button_save.get_style_context().add_class('suggested-action')

		self._button_revert = Gtk.Button.new_with_label(_('Revert'))
		self._button_revert.connect('clicked', self._load_options)

		# restart label
		self._label_restart = Gtk.Label(label='<i>{0}</i>'.format(_('Program restart required!')))
		self._label_restart.set_use_markup(True)
		self._label_restart.set_xalign(0.5)
		self._label_restart.set_yalign(0.5)

		if Gtk.get_major_version() == 3:
			self._label_restart.set_property('no-show-all', True)

		else:
			# GTK 4 has no show-all so hiding the label is enough
			self._label_restart.hide()

		# pack buttons
		if Gtk.get_major_version() == 3:
			hbox.pack_start(self._labels, False, False, 0)
			hbox.pack_start(self._tabs, True, True, 0)

		else:
			hbox.append(self._labels)
			self._tabs.set_hexpand(True)
			hbox.append(self._tabs)

		header_bar.pack_start(self._label_restart)
		header_bar.pack_end(self._button_save)
		header_bar.pack_end(self._button_revert)

		if Gtk.get_major_version() == 3:
			self.add(hbox)

		else:
			self.set_child(hbox)

	def show(self, widget, tab_name=None):
		"""Show dialog, focusing requested page, and reload options."""
		self._load_options()

		if Gtk.get_major_version() == 3:
			self.show_all()

		else:
			self.present()

		if tab_name:
			self._tabs.set_visible_child_name(tab_name)
		return True

	def _get_pages(self):
		"""Return list of option pages regardless of the toolkit version"""
		if Gtk.get_major_version() == 3:
			return self._tabs.get_children()

		return [page.get_child() for page in self._tabs.get_pages()]

	def _hide(self, widget=None, data=None):
		"""Hide dialog"""
		should_close = True

		# GTK 4 dialogs are asynchronous, window is closed from response handler
		if Gtk.get_major_version() != 3:
			if self._button_save.get_sensitive():
				self._show_unsaved_changes_dialog()

			else:
				self.hide()

			return True

		if self._button_save.get_sensitive():
			dialog = Gtk.MessageDialog(
			                    transient_for=self,
			                    destroy_with_parent=True,
			                    message_type=Gtk.MessageType.QUESTION,
			                    buttons=Gtk.ButtonsType.NONE,
			                    text=_("There are unsaved changes.\nDo you want to save them?")
			                )
			dialog.add_buttons(
						Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
						Gtk.STOCK_NO, Gtk.ResponseType.NO,
						Gtk.STOCK_YES, Gtk.ResponseType.YES,
					)
			dialog.set_default_response(Gtk.ResponseType.YES)
			result = run_dialog(dialog)
			dialog.destroy()

			if result == Gtk.ResponseType.YES:
				self._save_options()

			elif result == Gtk.ResponseType.CANCEL:
				should_close = False

		if should_close:
			self.hide()

		return True  # avoid destroying components

	def _show_unsaved_changes_dialog(self):
		"""Ask user what to do with unsaved changes (GTK 4)"""
		dialog = Gtk.MessageDialog(
							transient_for=self,
							modal=True,
							message_type=Gtk.MessageType.QUESTION,
							buttons=Gtk.ButtonsType.NONE,
							text=_("There are unsaved changes.\nDo you want to save them?")
						)
		dialog.add_buttons(
					_('Cancel'), Gtk.ResponseType.CANCEL,
					_('No'), Gtk.ResponseType.NO,
					_('Yes'), Gtk.ResponseType.YES,
				)
		dialog.set_default_response(Gtk.ResponseType.YES)
		dialog.connect('response', self._handle_unsaved_changes_response)
		dialog.present()

	def _handle_unsaved_changes_response(self, dialog, response):
		"""Handle response from unsaved changes dialog (GTK 4)"""
		dialog.destroy()

		if response == Gtk.ResponseType.YES:
			self._save_options()
			self.hide()

		elif response == Gtk.ResponseType.NO:
			self.hide()

	def _load_options(self, widget=None, data=None):
		"""Change interface to present current state of configuration"""
		# call all tabs to load their options
		pages = filter(lambda page: hasattr(page, '_load_options'), self._get_pages())
		list(map(lambda page: page._load_options(), pages))

		# disable save button and hide label
		self._button_save.set_sensitive(False)
		self._button_revert.set_sensitive(False)
		self._label_restart.hide()

	def _save_options(self, widget=None, data=None):
		"""Save options"""
		# call all tabs to save their options
		pages = filter(lambda page: hasattr(page, '_save_options'), self._get_pages())
		list(map(lambda page: page._save_options(), pages))

		# disable save button
		self._button_save.set_sensitive(False)
		self._button_revert.set_sensitive(False)

		# call main window to propagate new settings
		self._parent.apply_settings()

		# write changes to configuration file
		self._parent.save_config()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys (GTK 3)"""
		if event.keyval == Gdk.KEY_Escape:
			self._hide()

	def _handle_key_pressed(self, controller, keyval, keycode, state):
		"""Handle pressing keys (GTK 4)"""
		if keyval == Gdk.KEY_Escape:
			self._hide()
			return True

		return False

	def enable_save(self, widget=None, show_restart=None):
		"""Enable save button"""
		self._button_save.set_sensitive(True)
		self._button_revert.set_sensitive(True)

		# show label with message
		if show_restart is not None and show_restart:
			self._label_restart.show()

	def add_tab(self, name, label, tab):
		"""Add new tab to preferences window

		If you are using SettingsPage class there's no need to call this
		method manually, class constructor will do it automatically for you!

		"""
		self._tabs.add_titled(tab, name, label)
