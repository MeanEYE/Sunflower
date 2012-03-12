import os
import gtk
import pango

from widgets.status_bar import StatusBar


class Viewer:
	"""Simple file viewer implementation"""

	def __init__(self, path, provider, parent):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		self._path = path
		self._provider = provider
		self._parent = parent
		self._application = self._parent._parent

		mime_type = self._application.associations_manager.get_mime_type(path)

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

		if 'text/' in mime_type:
			# text file
			container = gtk.ScrolledWindow()
			container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			container.set_shadow_type(gtk.SHADOW_NONE)

			font = pango.FontDescription('monospace 9')
			text_view = gtk.TextView()
			text_view.set_editable(False)
			text_view.set_cursor_visible(False)
			text_view.modify_font(font)
			
			with open(self._path, 'r') as raw_file:
				data = raw_file.read()

			text_view.get_buffer().set_text(data)

			container.add(text_view)
			vbox.pack_start(container, True, True, 0)

		elif 'image/' in mime_type:
			# image file
			container = gtk.ScrolledWindow()
			container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			container.set_shadow_type(gtk.SHADOW_NONE)
			viewport = gtk.Viewport()

			image = gtk.Image()
			image.set_from_file(self._path)

			viewport.add(image)
			container.add(viewport)
			vbox.pack_start(container, True, True, 0)

		# pack user interface
		vbox.pack_end(status_bar, False, False, 0)

		self.window.add(vbox)
		
		# show all widgets
		self.window.show_all()

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

		return result
