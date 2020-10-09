from gi.repository import Gtk, Gdk, GObject

class ShortcutsWindow():
	"""Shortcuts display"""

	def __init__(self, parent):
		self._parent = parent

	def _show(self, widget, data=None):
		self._window = Gtk.ShortcutsWindow()
		self._window.set_title(_('Keyboard shortcuts'))
		self._window.set_default_size(750, 500)
		self._window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self._window.set_modal(True)
		self._window.set_skip_taskbar_hint(True)
		self._window.set_transient_for(self._parent)

		manager = self._parent.accelerator_manager
		bookmarks = self._parent.bookmark_options.get('bookmarks')
		groups = manager.get_groups()
		groups.sort()
		
		# create rename list
		replace_list = {}

		key_name = '{0}.bookmark_home'.format('item_list')
		replace_list[key_name] = _('Home directory')

		# add bookmarks to the replace list
		for number in range(1, 11):
			key_name = '{0}.{1}_{2}'.format('item_list', 'bookmark', number)

			if number < len(bookmarks):
				# bookmark exists
				bookmark_value = bookmarks[number-1]['name']

			else:
				# bookmark doesn't exist, add generic name
				bookmark_value = 'Bookmark #{0}'.format(number)

			replace_list[key_name] = bookmark_value


		for group_name in groups:
			title, methods = manager.get_group_data(group_name)

			method_names = sorted(methods) # iterates over dict keys

			section = Gtk.ShortcutsSection(title=title, section_name=group_name)
			section.show()

			group = Gtk.ShortcutsGroup()
			group.show()
			
			i = 0

			for method_name in method_names:
				# add all methods from the group
				title = methods[method_name]['title'].replace('_', '')

				# check if specified method name has a rename value
				key_name = '{0}.{1}'.format(group_name, method_name)
				if key_name in replace_list:
					title = title.format(replace_list[key_name])

				# get accelerators
				primary = manager.get_accelerator(group_name, method_name, True)
				secondary = manager.get_accelerator(group_name, method_name, False)

				# make sure we have something to display
				if primary is None:
					primary = (0, 0)

				if secondary is None:
					secondary = (0, 0)

				accelerator_name = Gtk.accelerator_name(primary[0], Gdk.ModifierType(primary[1]))

				if (accelerator_name == ''):
					continue

				short = Gtk.ShortcutsShortcut(title=title, accelerator=accelerator_name)
				short.show()
				group.add(short)

				i += 1

				# split shortcuts into groups to fit them on screen
				if (i % 10 == 0):
					section.add(group)
					group = Gtk.ShortcutsGroup()
					group.show()

			section.add(group)

			self._window.add(section)

		self._window.show_all()
