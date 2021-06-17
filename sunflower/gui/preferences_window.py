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
		GObject.GObject.__init__(self, type=Gtk.WindowType.TOPLEVEL)

		self._parent = parent

		# configure window
		self.set_title(_('Preferences'))
		self.set_default_size(750, 500)
		self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self.set_modal(True)
		self.set_skip_taskbar_hint(True)
		self.set_transient_for(parent)
		self.set_wmclass('Sunflower', 'Sunflower')

		self.connect('delete_event', self._hide)
		self.connect('key-press-event', self._handle_key_press)

		# create user interface
		header_bar = Gtk.HeaderBar.new()
		header_bar.set_show_close_button(True)
		header_bar.set_title(_('Preferences'))
		self.set_titlebar(header_bar)

		hbox = Gtk.HBox.new(False, 0)

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
		self._label_restart.set_alignment(0.5, 0.5)
		self._label_restart.set_use_markup(True)
		self._label_restart.set_property('no-show-all', True)

		# pack buttons
		hbox.pack_start(self._labels, False, False, 0)
		hbox.pack_start(self._tabs, True, True, 0)

		header_bar.pack_start(self._label_restart)
		header_bar.pack_end(self._button_save)
		header_bar.pack_end(self._button_revert)

		self.add(hbox)

	def _show(self, widget, tab_name=None):
		"""Show dialog and reload options"""
		self._load_options()
		if tab_name:
			self._tabs.set_visible_child_name(tab_name)
		self.show_all()
		return True

	def _hide(self, widget=None, data=None):
		"""Hide dialog"""
		should_close = True

		if self._button_save.get_sensitive():
			dialog = Gtk.MessageDialog(
			                    self,
			                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
			                    Gtk.MessageType.QUESTION,
								Gtk.ButtonsType.NONE,
			                    _("There are unsaved changes.\nDo you want to save them?")
			                )
			dialog.add_buttons(
						Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
						Gtk.STOCK_NO, Gtk.ResponseType.NO,
						Gtk.STOCK_YES, Gtk.ResponseType.YES,
					)
			dialog.set_default_response(Gtk.ResponseType.YES)
			result = dialog.run()
			dialog.destroy()

			if result == Gtk.ResponseType.YES:
				self._save_options()

			elif result == Gtk.ResponseType.CANCEL:
				should_close = False

		if should_close:
			self.hide()

		return True  # avoid destroying components

	def _load_options(self, widget=None, data=None):
		"""Change interface to present current state of configuration"""
		# call all tabs to load their options
		pages = filter(lambda page: hasattr(page, '_load_options'), self._tabs.get_children())
		list(map(lambda page: page._load_options(), pages))

		# disable save button and hide label
		self._button_save.set_sensitive(False)
		self._button_revert.set_sensitive(False)
		self._label_restart.hide()

	def _save_options(self, widget=None, data=None):
		"""Save options"""
		# call all tabs to save their options
		pages = filter(lambda page: hasattr(page, '_save_options'), self._tabs.get_children())
		list(map(lambda page: page._save_options(), pages))

		# disable save button
		self._button_save.set_sensitive(False)
		self._button_revert.set_sensitive(False)

		# call main window to propagate new settings
		self._parent.apply_settings()

		# write changes to configuration file
		self._parent.save_config()

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys"""
		if event.keyval == Gdk.KEY_Escape:
			self._hide()

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
