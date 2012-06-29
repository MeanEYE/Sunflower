import gtk

from gui.input_dialog import InputDialog, ApplicationInputDialog
from widgets.settings_page import SettingsPage


class Column:
	NAME = 0
	COMMAND = 1


class AssociationsOptions(SettingsPage):
	"""Mime-type associations options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'accelerators', _('Associations'))

		# create interface
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._associations = gtk.TreeStore(str, str)
		self._list = gtk.TreeView(model=self._associations)
		self._list.set_rules_hint(True)
		self._list.set_headers_visible(False)

		cell_title = gtk.CellRendererText()
		cell_command = gtk.CellRendererText()

		col_title = gtk.TreeViewColumn(None, cell_title, text=0)
		col_title.set_min_width(200)
		col_title.set_resizable(True)

		col_command = gtk.TreeViewColumn(None, cell_command, text=1)
		col_command.set_resizable(True)
		col_command.set_expand(True)

		self._list.append_column(col_title)
		self._list.append_column(col_command)

		# create add menu
		self._add_menu = gtk.Menu()
		
		item_add_mime_type = gtk.MenuItem(label=_('Add mime type'))
		item_add_mime_type.connect('activate', self.__add_mime_type)

		item_add_application = gtk.MenuItem(label=_('Add application to mime type'))
		item_add_application.connect('activate', self.__add_application)
		
		self._add_menu.append(item_add_mime_type)
		self._add_menu.append(item_add_application)
		
		self._add_menu.show_all()
		
		# create controls
		hbox_controls = gtk.HBox(homogeneous=False, spacing=5)
		
		button_add = gtk.Button(stock=gtk.STOCK_ADD)
		button_add.connect('clicked', self.__button_add_clicked)
		
		# pack interface
		container.add(self._list)
		
		hbox_controls.pack_start(button_add, False, False, 0)

		self.pack_start(container, True, True, 0)
		self.pack_end(hbox_controls, False, False, 0)

	def __button_add_clicked(self, widget, data=None):
		"""Handle clicking on add button"""
		self._add_menu.popup(
						None, None,
						self.__get_menu_position,
						1, 0, widget
					)

	def __add_mime_type(self, widget, data=None):
		"""Show dialog for adding mime type"""
		dialog = InputDialog(self._application)
		dialog.set_title(_('Add mime type'))
		dialog.set_label(_('Enter MIME type (eg. image/png):'))

		response = dialog.get_response()

		# add new mime type to the table
		if response[0] == gtk.RESPONSE_OK:
			mime_type = response[1]
			description = self._application.associations_manager.get_mime_description(mime_type)

			# add item to the store
			self._associations.append(None, (description, mime_type))

			# enable save button on parent
			self._parent.enable_save()

	def __add_application(self, widget, data=None):
		"""Show dialog for adding application to mime type"""
		selection = self._list.get_selection()
		item_list, selected_iter = selection.get_selected()

		if selected_iter is not None:
			level = item_list.iter_depth(selected_iter)

			if level == 0:
				parent = selected_iter
			
			else:
				parent = item_list.iter_parent(selected_iter)

			dialog = ApplicationInputDialog(self._application)
			response = dialog.get_response()

			# add new mime type to the table
			if response[0] == gtk.RESPONSE_OK:
				name = response[1]
				command = response[2]

				# add data to store
				self._associations.append(parent, (name, command))

				# enable save button on parent
				self._parent.enable_save()

		else:
			# warn user about selection
			dialog = gtk.MessageDialog(
									self._parent,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_INFO,
									gtk.BUTTONS_OK,
									_(
										'You need to select mime type to which application '
										'will be added. You can also select another application '
										'in which case new one will be added to its parent.'
									) 
								)
			dialog.run()
			dialog.destroy()
					
	def __get_menu_position(self, menu, button):
		"""Get history menu position"""
		# get coordinates
		window_x, window_y = self._parent.window.get_position()
		button_x, button_y = button.translate_coordinates(self._parent, 0, 0)
		button_h = button.get_allocation().height

		# calculate absolute menu position
		pos_x = window_x + button_x
		pos_y = window_y + button_y + button_h

		return (pos_x, pos_y, True)

	def _load_options(self):
		"""Load options and update interface"""
		config = self._application.association_options
		manager = self._application.associations_manager

		# clear the storage
		self._associations.clear()

		# get all mime types from config file
		mime_types = config._get_data().keys()

		for mime_type in mime_types:
			# add mime type to the list
			description = manager.get_mime_description(mime_type)
			parent = self._associations.append(None, (description, mime_type))

			# get all applications
			applications = config.get(mime_type)
			count = len(applications) / 2

			for index in xrange(1, count + 1):
				application = applications[index-1]
				self._associations.append(parent, (application['name'], application['command']))

	def _save_options(self):
		"""Method called when save button is clicked"""
		config = self._application.association_options
		
		# iterate over groups
		for row in self._associations:
			mime_type = self._associations.get_value(row.iter, Column.COMMAND)
			children = row.iterchildren()
			applications = []
			
			# store accelerators for current group
			for index, child in enumerate(children, 0):

				application = {
						'name': self._associations.get_value(child.iter, Column.NAME),
						'command': self._associations.get_value(child.iter, Column.COMMAND)
					}

				applications.append(application)

			# add applications to config
			config.set(mime_type, applications)
