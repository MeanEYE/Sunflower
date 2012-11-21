import os
import gtk
import pango
import subprocess

from common import executable_exists
from widgets.status_bar import StatusBar
from plugin_base.provider import Mode as FileMode


class Viewer:
	"""Simple file viewer implementation"""

	def __init__(self, path, provider, parent):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		self._path = path
		self._provider = provider
		self._parent = parent
		self._application = self._parent._parent

		associations_manager = self._application.associations_manager
		mime_type = associations_manager.get_mime_type(path)

		if associations_manager.is_mime_type_unknown(mime_type):
			data = associations_manager.get_sample_data(path, provider)
			mime_type = associations_manager.get_mime_type(data=data)

		# configure window
		self.window.set_title(_('{0} - Viewer').format(os.path.basename(self._path)))
		self.window.set_size_request(800, 600)
		self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.window.set_resizable(True)
		self.window.set_skip_taskbar_hint(False)
		self.window.set_wmclass('Sunflower', 'Sunflower')
		self.window.set_border_width(0)

		# connect signals
		self.window.connect('destroy', self._handle_destroy)
		self.window.connect('key-press-event', self._handle_key_press)

		# create user interface according to mime type
		vbox = gtk.VBox(homogeneous=False, spacing=0)
		status_bar = StatusBar()
		status_bar.set_border_width(2)
		status_bar.add_group_with_icon('mime_type', 'document-properties', mime_type)
		status_bar.show()

		self._notebook = gtk.Notebook()
		self._notebook.set_border_width(5)

		# create page for executables
		if mime_type in ('application/x-executable', 'application/x-sharedlib') \
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
		if associations_manager.is_mime_type_subset(mime_type, 'text/plain'):
			# get data from the file
			raw_file = self._provider.get_file_handle(self._path, FileMode.READ)
			data = raw_file.read()
			raw_file.close()

			# create new page
			self._create_text_page(_('Text'), data)

		# create image page if needed
		if mime_type.startswith('image/'):
			container = gtk.ScrolledWindow()
			container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			container.set_shadow_type(gtk.SHADOW_NONE)
			container.set_border_width(5)
			viewport = gtk.Viewport()

			image = gtk.Image()
			image.set_from_file(self._path)

			viewport.add(image)
			container.add(viewport)
			self._insert_page(_('Image'), container)

		# pack user interface
		vbox.pack_start(self._notebook, True, True, 0)
		vbox.pack_start(status_bar, False, False, 0)

		self.window.add(vbox)
		
		# show all widgets
		self.window.show_all()

	def _append_page(self, title, container):
		"""Append new page to viewer"""
		self._notebook.append_page(container, gtk.Label(title))
		container.grab_focus()

	def _insert_page(self, title, container, position=0):
		"""Insert page at desired position in viewer notebook"""
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
			self.window.destroy()
			result = True

		elif event.keyval in range(gtk.keysyms._1, gtk.keysyms._9 + 1):
			# switch to specified page
			index = event.keyval - gtk.keysyms._1

			if index <= self._notebook.get_n_pages() - 1:
				self._notebook.set_current_page(index)

			result = True

		return result
