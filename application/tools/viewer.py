import os
import chardet
import codecs
import gtk
import pango
import gobject
import subprocess

from common import executable_exists
from widgets.status_bar import StatusBar
from plugin_base.provider import Mode as FileMode


class Viewer:
	"""Simple file viewer implementation"""

	def __init__(self, path, provider, parent):
		self._window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		self.path = path
		self._provider = provider
		self._parent = parent
		self._application = self._parent._parent
		self._page_count = 0

		associations_manager = self._application.associations_manager
		self._mime_type = associations_manager.get_mime_type(path)

		if associations_manager.is_mime_type_unknown(self._mime_type):
			data = associations_manager.get_sample_data(path, provider)
			self._mime_type = associations_manager.get_mime_type(data=data)

		# configure window
		self._window.set_title(_('{0} - Viewer').format(os.path.basename(self.path)))
		self._window.set_size_request(800, 600)
		self._window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self._window.set_resizable(True)
		self._window.set_skip_taskbar_hint(False)
		self._window.set_wmclass('Sunflower', 'Sunflower')
		self._window.set_border_width(0)

		# connect signals
		self._window.connect('destroy', self._handle_destroy)
		self._window.connect('key-press-event', self._handle_key_press)

		# create user interface according to mime type
		vbox = gtk.VBox(homogeneous=False, spacing=0)
		self.status_bar = StatusBar()
		self.status_bar.set_border_width(2)
		self.status_bar.add_group_with_icon('mime_type', 'document-properties', self._mime_type)
		self.status_bar.show()

		self._notebook = gtk.Notebook()
		self._notebook.set_border_width(2)

		# create extensions
		self._create_extensions()

		# create page for executables
		if self._mime_type in ('application/x-executable', 'application/x-sharedlib') \
		and executable_exists('nm'):
			# get output from command
			data = ''
			try:
				output = subprocess.Popen(
									['nm', '-al', path],
									stdout=subprocess.PIPE
								).communicate()

				data = output[0]

			except OSError as error:
				# report error to user
				raise error

			# create new page
			self._create_text_page(_('Executable'), data)

		# create text page if needed
		if associations_manager.is_mime_type_subset(self._mime_type, 'text/plain'):
			# get data from the file
			raw_file = self._provider.get_file_handle(self.path, FileMode.READ)
			data = raw_file.read()
			raw_file.close()

			# create new page
			self._create_text_page(_('Text'), data)

		# create image page if needed
		if self._mime_type.startswith('image/'):
			container = gtk.ScrolledWindow()
			container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			container.set_shadow_type(gtk.SHADOW_NONE)
			container.set_border_width(5)
			viewport = gtk.Viewport()
			image = gtk.Image()

			# load raw data
			raw_file = provider.get_file_handle(path, FileMode.READ)
			raw_data = raw_file.read()
			raw_file.close()

			# get pixbuf from raw data
			try:
				loader = gtk.gdk.PixbufLoader()
				loader.write(raw_data)
				loader.close()

			except gobject.GError:
				pass

			else:
				# set image
				image.set_from_pixbuf(loader.get_pixbuf())

			viewport.add(image)
			container.add(viewport)
			self._insert_page(_('Image'), container)

		# pack user interface
		vbox.pack_start(self._notebook, True, True, 0)
		vbox.pack_start(self.status_bar, False, False, 0)

		self._window.add(vbox)

		# show all widgets if there are pages present
		if self._page_count > 0:
			self._window.show_all()

		else:
			# show information and close window
			dialog = gtk.MessageDialog(
									self._application,
									gtk.DIALOG_DESTROY_WITH_PARENT,
									gtk.MESSAGE_INFO,
									gtk.BUTTONS_OK,
									_('Viewer is unable to display this file type.')
								)
			dialog.run()
			dialog.destroy()

			self._window.destroy()

	def _create_extensions(self):
		"""Create extension widgets"""
		class_list = self._application.get_viewer_extension_classes(self._mime_type)

		# we don't have any registered extensions for this mime type
		if len(class_list) == 0:
			return

		# create all extensions and populate notebook
		for ExtensionClass in class_list:
			extension = ExtensionClass(self)
			self._append_page(extension.get_title(), extension.get_container())

	def _append_page(self, title, container):
		"""Append new page to viewer"""
		self._page_count += 1
		self._notebook.append_page(container, gtk.Label(title))
		container.grab_focus()

	def _insert_page(self, title, container, position=0):
		"""Insert page at desired position in viewer notebook"""
		self._page_count += 1
		self._notebook.insert_page(container, gtk.Label(title), position)

	def _create_text_page(self, title, content, position=0):
		"""Create text page with specified data"""
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_border_width(5)

		font = pango.FontDescription('monospace 9')
		text_view = gtk.TextView()
		text_view.set_editable(False)
		text_view.set_cursor_visible(True)
		text_view.modify_font(font)

		# try to detect file character encoding and convert to Unicode
		encoding = chardet.detect(content)['encoding']
		if encoding is not None:
			content = codecs.decode(content, encoding)

		text_view.get_buffer().set_text(content)

		# add container to notebook
		container.add(text_view)
		self._append_page(title, container)

	def _handle_destroy(self, widget):
		"""Handle destroying viewer window"""
		return False

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in history list"""
		result = False

		if event.keyval == gtk.keysyms.Escape:
			# close window on escape
			self._window.destroy()
			result = True

		elif event.keyval in range(gtk.keysyms._1, gtk.keysyms._9 + 1):
			# switch to specified page
			index = event.keyval - gtk.keysyms._1

			if index <= self._notebook.get_n_pages() - 1:
				self._notebook.set_current_page(index)

			result = True

		return result
