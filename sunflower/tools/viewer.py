from __future__ import absolute_import

import gi
import os
import chardet
import codecs
import subprocess

from gi.repository import Gio, Gtk, Gdk, Pango, GObject, GdkPixbuf
from sunflower.common import executable_exists, decode_file_name, get_monospace_font_string
from sunflower.widgets.status_bar import StatusBar
from sunflower.plugin_base.provider import Mode as FileMode

try:
	gi.require_version('GtkSource', '4')
	from gi.repository import GtkSource
	GTK_SOURCE_AVAILABLE = True
except:
	GTK_SOURCE_AVAILABLE = False


class Viewer(Gtk.Window):
	"""Simple file viewer implementation"""

	FONT = None

	def __init__(self, path, provider, parent):
		Gtk.Window.__init__(self)

		# load font
		if not self.FONT:
			self.FONT = Pango.FontDescription.from_string(get_monospace_font_string())

		# viewer does not support directories
		if provider.is_dir(path):
			return

		self.path = path
		self._provider = provider
		self._parent = parent
		self._application = self._parent._parent
		self._page_count = 0
		self._options = self._application.options.section('viewer')

		# detect mime type
		associations_manager = self._application.associations_manager
		self._mime_type = associations_manager.get_mime_type(path)

		if associations_manager.is_mime_type_unknown(self._mime_type):
			data = associations_manager.get_sample_data(path, provider)
			self._mime_type = associations_manager.get_mime_type(data=data)

		# configure window
		display_filename = decode_file_name(os.path.basename(self.path))
		self.set_title(_('{0} - Viewer').format(display_filename))
		self.set_size_request(800, 600)
		self.set_resizable(True)

		header_bar = Gtk.HeaderBar.new()
		if Gtk.get_major_version() == 3:
			header_bar.set_title(display_filename)
			header_bar.set_subtitle(self._mime_type)
			header_bar.set_show_close_button(True)

		else:
			# GTK 4 header bar has no title and subtitle, provide our own
			title_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
			title_box.set_valign(Gtk.Align.CENTER)

			title_label = Gtk.Label.new(display_filename)
			title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
			title_label.get_style_context().add_class('title')
			title_box.append(title_label)

			subtitle_label = Gtk.Label.new(self._mime_type)
			subtitle_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
			subtitle_label.get_style_context().add_class('subtitle')
			title_box.append(subtitle_label)

			header_bar.set_title_widget(title_box)
			header_bar.set_show_title_buttons(True)
		self.set_titlebar(header_bar)

		self._stack = Gtk.Stack.new()
		stack_switcher = Gtk.StackSwitcher.new()
		stack_switcher.set_stack(self._stack)
		header_bar.pack_start(stack_switcher)

		# create extensions
		self._create_extensions()

		# connect signals
		self.connect('destroy', self._handle_destroy)
		if Gtk.get_major_version() == 3:
			self.connect('key-press-event', self._handle_key_press)

		else:
			key_controller = Gtk.EventControllerKey.new()
			key_controller.connect('key-pressed', self._handle_key_pressed)
			self.add_controller(key_controller)
		# create page for executables
		if self._mime_type in ('application/x-executable', 'application/x-sharedlib') \
		and executable_exists('nm'):
			try:
				output = subprocess.Popen(['nm', '-al', path], stdout=subprocess.PIPE).communicate()
				data = output[0]
			except OSError as error:
				pass
			else:
				self._create_text_page(_('Executable'), data)

		# create source code viewer
		if GTK_SOURCE_AVAILABLE:
			language_manager = GtkSource.LanguageManager.new()
			language = language_manager.guess_language(path, self._mime_type)

			if language:
				# load contents
				code_buffer = GtkSource.Buffer.new_with_language(language)
				raw_file = self._provider.get_file_handle(self.path, FileMode.READ)
				code_buffer.set_text(raw_file.read().decode())
				raw_file.close()

				# create viewer
				viewer = GtkSource.View.new_with_buffer(code_buffer)
				viewer.set_monospace(True)
				viewer.set_indent_width(4)
				viewer.set_tab_width(4)
				viewer.set_show_line_numbers(True)
				viewer.set_editable(False)
				if Gtk.get_major_version() == 3:
					viewer.modify_font(self.FONT)

				else:
					self.__apply_font(viewer)

				if self._options.get('word_wrap'):
					viewer.set_wrap_mode(Gtk.WrapMode.WORD)

				code_buffer.place_cursor(code_buffer.get_start_iter())

				window = Gtk.ScrolledWindow.new()
				if Gtk.get_major_version() == 3:
					window.set_shadow_type(Gtk.ShadowType.NONE)

				else:
					window.set_has_frame(False)
				window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
				if Gtk.get_major_version() == 3:
					window.add(viewer)

				else:
					window.set_child(viewer)

				# add page
				self.add_page(_('Code'), window)

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
			container = Gtk.ScrolledWindow()
			container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
			if Gtk.get_major_version() == 3:
				container.set_shadow_type(Gtk.ShadowType.NONE)

			else:
				container.set_has_frame(False)
			viewport = Gtk.Viewport()
			image = Gtk.Image()

			# load raw data
			raw_file = provider.get_file_handle(path, FileMode.READ)
			raw_data = raw_file.read()
			raw_file.close()

			# get pixbuf from raw data
			try:
				loader = GdkPixbuf.PixbufLoader()
				loader.write(raw_data)
				loader.close()

			except GObject.GError:
				pass

			else:
				# set image
				image.set_from_pixbuf(loader.get_pixbuf())

			if Gtk.get_major_version() == 3:
				viewport.add(image)

			else:
				viewport.set_child(image)
			if Gtk.get_major_version() == 3:
				container.add(viewport)

			else:
				container.set_child(viewport)
			self.add_page(_('Image'), container)

		# pack user interface
		if Gtk.get_major_version() == 3:
			self.add(self._stack)

		else:
			self.set_child(self._stack)

		# show all widgets if there are pages present
		if self._page_count > 0:
			if Gtk.get_major_version() == 3:
				self.show_all()

			else:
				self.show()

		else:
			dialog = Gtk.MessageDialog(
									transient_for=self._application,
									destroy_with_parent=True,
									message_type=Gtk.MessageType.INFO,
									buttons=Gtk.ButtonsType.OK,
									text=_('Viewer is unable to display this file type.')
								)
			run_dialog(dialog)
			dialog.destroy()
			self.destroy()

	def __apply_font(self, widget):
		"""Apply configured font to text widget. (GTK 4)

		Replacement for `modify_font` which no longer exists, font is
		applied through widget specific style provider instead.

		"""
		rules = ['font-family: "{0}"'.format(self.FONT.get_family())]

		if self.FONT.get_size() > 0:
			size = self.FONT.get_size() / Pango.SCALE
			unit = 'px' if self.FONT.get_size_is_absolute() else 'pt'
			rules.append('font-size: {0}{1}'.format(size, unit))

		provider = Gtk.CssProvider.new()
		provider.load_from_string('textview {{ {0}; }}'.format('; '.join(rules)))
		widget.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	def _create_extensions(self):
		"""Create extension widgets."""
		class_list = self._application.get_viewer_extension_classes(self._mime_type)

		# we don't have any registered extensions for this mime type
		if len(class_list) == 0:
			return

		# create all extensions and populate tack
		for ExtensionClass in class_list:
			extension = ExtensionClass(self)
			self.add_page(extension.get_title(), extension.get_container())

	def add_page(self, title, container, position=None):
		"""Add new page to stack."""
		self._page_count += 1
		self._stack.add_titled(container, title, title)

		if position:
			self._stack.child_set_property('position', position)

	def _create_text_page(self, title, content, position=0):
		"""Create text page with specified data."""
		container = Gtk.ScrolledWindow()
		container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		if Gtk.get_major_version() == 3:
			container.set_shadow_type(Gtk.ShadowType.NONE)

		else:
			container.set_has_frame(False)

		text_view = Gtk.TextView()
		text_view.set_editable(False)
		text_view.set_cursor_visible(True)
		text_view.set_monospace(True)
		if Gtk.get_major_version() == 3:
			text_view.modify_font(self.FONT)

		else:
			self.__apply_font(text_view)

		if self._options.get('word_wrap'):
			container.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
			text_view.set_wrap_mode(Gtk.WrapMode.WORD)

		else:
			container.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

		# try to detect file character encoding and convert to Unicode
		encoding = chardet.detect(content)['encoding']
		if encoding is not None:
			content = codecs.decode(content, encoding)

		if len(content) > 0:
			text_buffer = text_view.get_buffer()
			text_buffer.set_text(content)
			text_buffer.place_cursor(text_buffer.get_start_iter())

		# add container to notebook
		if Gtk.get_major_version() == 3:
			container.add(text_view)

		else:
			container.set_child(text_view)
		self.add_page(title, container)

	def _handle_destroy(self, widget):
		"""Handle destroying viewer window."""
		return False

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in history list. (GTK 3)"""
		return self._handle_keyval(event.keyval, event.get_state())

	def _handle_key_pressed(self, controller, keyval, keycode, state):
		"""Handle pressing keys in history list. (GTK 4)"""
		return self._handle_keyval(keyval, state)

	def _handle_keyval(self, keyval, state):
		"""Handle pressing keys in history list."""
		result = False

		if keyval == Gdk.KEY_Escape:
			# close window on escape
			self.destroy()
			result = True

		elif keyval in range(Gdk.KEY_1, Gdk.KEY_9 + 1):
			# switch to specified page
			index = keyval - Gdk.KEY_1

			if Gtk.get_major_version() == 3:
				children = self._stack.get_children()

			else:
				children = [page.get_child() for page in self._stack.get_pages()]
			if index < len(children):
				self._stack.set_focus_child(children[index])
			result = True

		return result
