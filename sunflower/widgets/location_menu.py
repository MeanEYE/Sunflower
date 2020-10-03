from __future__ import absolute_import

import os
import urllib.parse

from gi.repository import Gtk, Pango
from sunflower import common
from sunflower.parameters import Parameters
from sunflower.plugin_base.item_list import ItemList


class LocationMenu:
	"""Interface which shows list of paths to jump to."""

	def __init__(self, application):
		self._application = application
		self._active_object = None
		self._headers = {}
		self._assigned = {}

		# create popover interface
		self._popover = Gtk.Popover.new()
		self._popover.set_position(Gtk.PositionType.BOTTOM)
		self._popover.set_modal(True)

		# create widget container
		container = Gtk.VBox.new(False, 0)
		container.set_border_width(5)

		# create search field
		self._search_field = Gtk.SearchEntry.new()
		self._search_field.connect('search-changed', self.__handle_search_changed)
		self._search_query = None

		# create notebook for different lists
		list_container = Gtk.ScrolledWindow.new()
		list_container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
		list_container.set_size_request(-1, 300)
		list_container.set_shadow_type(Gtk.ShadowType.IN)

		self._list = Gtk.ListBox.new()
		self._list.set_header_func(self.__handle_set_header)
		self._list.set_filter_func(self.__handle_filter_check_location)

		# create button box and commonly used buttons
		hbox_buttons = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
		hbox_buttons.get_style_context().add_class('linked')

		button_open = Gtk.Button.new_from_icon_name('document-open-symbolic', Gtk.IconSize.BUTTON)
		button_open.connect('clicked', self.__handle_open_click)
		button_open.set_tooltip_text(_('Open'))
		hbox_buttons.pack_start(button_open, False, False, 0)

		button_open_tab = Gtk.Button.new_from_icon_name('tab-new-symbolic', Gtk.IconSize.BUTTON)
		button_open_tab.connect('clicked', self.__handle_open_tab_click)
		button_open_tab.set_tooltip_text(_('Open selected path in new tab'))
		hbox_buttons.pack_start(button_open_tab, False, False, 0)

		self._button_open_opposite = Gtk.Button.new_from_icon_name('go-next-symbolic', Gtk.IconSize.BUTTON)
		self._button_open_opposite.connect('clicked', self.__handle_open_opposite_click)
		self._button_open_opposite.set_tooltip_text(_('Open selected path in opposite list'))
		hbox_buttons.pack_start(self._button_open_opposite, False, False, 0)

		button_open_terminal = Gtk.Button.new_from_icon_name('utilities-terminal-symbolic', Gtk.IconSize.BUTTON)
		button_open_terminal.connect('clicked', self.__handle_open_terminal_click)
		button_open_terminal.set_tooltip_text(_('Open terminal at selected path'))
		hbox_buttons.pack_start(button_open_terminal, False, False, 0)

		# populate headers
		self.add_header(Bookmark, GenericHeader(_('Bookmarks')))

		# populate lists
		self.update_bookmarks()

		# pack interface
		list_container.add(self._list)

		container.pack_start(self._search_field, True, False, 0)
		container.pack_start(list_container, True, True, 5)
		container.pack_start(hbox_buttons, True, False, 0)

		container.show_all()
		self._popover.add(container)

		# attach location menu to mount manager
		self._application.mount_manager.attach_location_menu(self)

	def update_bookmarks(self):
		"""Populate bookmarks menu."""
		options = self._application.bookmark_options
		icon_manager = self._application.icon_manager

		# clear existing entries
		self.clear_locations(Bookmark)

		# sunflower bookmarks
		if options.get('add_home'):
			self.add_location(Bookmark(os.path.expanduser('~'), 'user-home', _('Home directory')))

		for data in options.get('bookmarks'):
			icon_name = icon_manager.get_icon_for_directory(data['uri'])
			self.add_location(Bookmark(data['uri'], icon_name, data['name']))

		# gnome bookmarks
		bookmarks_files = (
					os.path.expanduser('~/.gtk-bookmarks'),
					os.path.join(common.get_config_directory(), 'gtk-3.0', 'bookmarks')
				)
		available_files = [path for path in bookmarks_files if os.path.exists(path)]

		if options.get('system_bookmarks') and len(available_files) > 0:
			lines = []
			with open(available_files[0], 'r') as raw_file:
				lines.extend(raw_file.readlines(False))

			# parse files
			for line in lines:
				try:
					uri, name = line.strip().split(' ', 1)

				except:
					uri = line.strip()
					name = urllib.parse.unquote(uri.split('://')[1]) if '://' in uri else uri
					name = os.path.basename(name)

				# add entry
				icon_name = icon_manager.get_icon_for_directory(uri)
				self.add_location(Bookmark(uri, icon_name, name))

	def __get_selected_location(self):
		"""Return location object selected or None."""
		return self._list.get_selected_row()

	def __handle_open_click(self, widget, data=None):
		"""Handle clicking on open button."""
		selected_location = self.__get_selected_location()
		assert self._active_object is not None or selected_location is not None

		# close menu
		self._popover.popdown()

		# open selected path in currently active list
		if isinstance(self._active_object, ItemList):
			self._active_object.change_path(selected_location.get_location())

		return True

	def __handle_open_tab_click(self, widget, data=None):
		"""Handle clicking on open in new tab button."""
		selected_location = self.__get_selected_location()
		assert self._active_object is not None or selected_location is not None

		# close menu
		self._popover.popdown()

		# create options to pass to new tab
		options = Parameters()
		options.set('path', selected_location.get_location())

		# create new tab
		TabClass = self._application.plugin_classes['file_list']
		self._application.create_tab(self._active_object._notebook, TabClass, options)

		return True

	def __handle_open_opposite_click(self, widget, data=None):
		"""Handle slicking on open in opposite panel button."""
		selected_location = self.__get_selected_location()
		assert self._active_object is not None or selected_location is not None

		# close menu
		self._popover.popdown()

		# open in opposite object
		opposite_object = self._application.get_opposite_object(self._active_object)
		if isinstance(opposite_object, ItemList):
			opposite_object.change_path(selected_location.get_location())

		return True

	def __handle_open_terminal_click(self, widget, data=None):
		"""Handle clicking on open in terminal button."""
		selected_location = self.__get_selected_location()
		assert self._active_object is not None or selected_location is not None

		# close menu
		self._popover.popdown()

		# create options to pass to new tab
		options = Parameters()
		options.set('path', selected_location.get_location())

		# create new tab
		TabClass = self._application.plugin_classes['system_terminal']
		self._application.create_tab(self._active_object._notebook, TabClass, options)

		return True

	def __handle_set_header(self, row, before=None, data=None):
		"""Set header widget for specified row."""
		class_name = row.__class__.__name__

		# make sure we have header for this class
		if class_name not in self._headers:
			return

		if class_name in self._assigned and self._assigned[class_name]:
			return

		# set new header
		row.set_header(self._headers[class_name])
		self._assigned[class_name] = row

	def __handle_search_changed(self, widget):
		"""Handle change in search entry."""
		for class_name in self._assigned.keys():
			self._assigned[class_name] = None

		self._search_query = widget.get_text().lower()
		self._list.invalidate_filter()

	def __handle_filter_check_location(self, row, data=None):
		"""Determine whether location should be visible."""
		if self._search_query:
			# determine visibility
			location = row.get_location()
			result = location is not None and self._search_query in location.lower()
		else:
			# show location by default
			result = True

		return result

	def add_header(self, Class, widget):
		"""Add header widget for specified location class name."""
		self._headers[Class.__name__] = widget
		self._assigned[Class.__name__] = None

	def add_location(self, widget):
		"""Add location row. If header for this row class has been specified it will
		be automatically assigned to the destination group."""
		self._list.add(widget)

	def remove_location(self, location):
		"""Remove specified location."""
		if location in self._assigned.values():
			self._assigned[location.__class__.__name__] = None

		self._list.remove(location)

	def get_locations(self, Class=None):
		"""Return list of bookmarks for provided location class."""
		result = []
		return result

	def clear_locations(self, Class=None):
		"""Clear all locations for specified location class."""
		pass

	def show(self, reference, active_object=None):
		"""Show location menu for reference widget."""
		# update icons
		if self._application.get_left_object() == self._active_object:
			self._button_open_opposite.get_image().set_from_icon_name('go-next-symbolic', Gtk.IconSize.BUTTON)
		else:
			self._button_open_opposite.get_image().set_from_icon_name('go-previous-symbolic', Gtk.IconSize.BUTTON)

		# store active object for later use
		self._active_object = active_object

		# show menu
		self._popover.set_relative_to(reference)
		self._popover.popup()


class GenericHeader(Gtk.VBox):
	"""Simple group title for locations."""

	def __init__(self, title):
		Gtk.VBox.__init__(self)
		self.set_border_width(5)

		# create title
		self._title = Gtk.Label.new('<b>{}</b>'.format(title))
		self._title.set_use_markup(True)
		self._title.set_alignment(0, 0.5)
		self._title.show()

		# create separator
		separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)

		# pack user interface
		self.pack_start(self._title, True, False, 0)
		self.pack_start(separator, True, False, 0)

		# show all components
		self.show_all()


class Location(Gtk.ListBoxRow):
	"""Generic location widget."""

	def __init__(self):
		Gtk.ListBoxRow.__init__(self)
		self.set_activatable(True)

	def _create_interface(self):
		"""Create interface for the widget to display."""
		pass

	def get_location(self):
		"""Return location path."""
		return None


class Bookmark(Location):
	"""Bookmark list item used for displaying and handling individual bookmarked paths."""

	def __init__(self, location, icon, title):
		Location.__init__(self)
		self._location = location

		# interface elements
		self._icon = None
		self._title = None
		self._subtitle = None

		# create user interface
		self._create_interface()
		self._icon.set_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR)
		self._title.set_text(title)
		self._subtitle.set_markup('<small>{}</small>'.format(location))

		self.show_all()

	def _create_interface(self):
		"""Create interface for the widget to display."""
		container = Gtk.HBox.new(False, 5)
		container.set_border_width(5)
		title_container = Gtk.VBox.new(False, 0)

		# create bookmark icon
		self._icon = Gtk.Image.new()

		# create title
		self._title = Gtk.Label.new()
		self._title.set_alignment(0, 0.5)
		self._title.set_ellipsize(Pango.EllipsizeMode.END)

		self._subtitle = Gtk.Label.new()
		self._subtitle.set_alignment(0, 0.5)
		self._subtitle.set_use_markup(True)
		self._subtitle.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

		# pack user interface
		title_container.pack_start(self._title, True, False, 0)
		title_container.pack_start(self._subtitle, True, False, 0)
		container.pack_start(self._icon, False, False, 0)
		container.pack_start(title_container, True, True, 0)
		self.add(container)

	def get_location(self):
		"""Return location associated with bookmark."""
		return self._location
