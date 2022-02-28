import sys

from gi.repository import Gtk, Gdk
from subprocess import check_output, run
from threading import Thread
from sunflower.common import executable_exists


class Clipboard:
	"""Support for various clipboard implementations accross different platforms
	and different protocols."""

	def __init__(self):
		self.text_support = []
		self.data_support = []

		self.add_provider(GtkProvider())
		self.add_provider(CommandProvider())
		self.add_provider(FakeProvider())

	def add_provider(self, provider):
		"""Add new clipboard provider to the system."""
		if not issubclass(provider.__class__, Provider):
			print('Invalid clipboard provider class: {}'.format(provider.__class__.__name__), file=sys.stderr)
			return

		text, data = provider.available()
		if text:
			self.text_support.append(provider)
		if data:
			self.data_support.append(provider)

	def set_text(self, text):
		"""Set text content."""
		if len(self.text_support) == 0:
			return
		provider = self.text_support[0]
		provider.set_text(text)

	def set_data(self, data, mime_types):
		"""Set data as content with provided list of mime types."""
		if len(self.data_support) == 0:
			return
		provider = self.data_support[0]
		provider.set_data(data, mime_types)

	def get_text(self):
		"""Return text value stored in clipboard."""
		if len(self.text_support) == 0:
			return
		provider = self.text_support[0]
		return provider.get_text()

	def get_data(self, mime_types):
		"""Return data stored for provided types in clipboard."""
		if len(self.data_support) == 0:
			return
		provider = self.data_support[0]
		return provider.get_data(mime_types)

	def text_available(self):
		"""Check if clipboard with text is available."""
		if len(self.text_support) == 0:
			return
		provider = self.text_support[0]
		return provider.text_available()

	def data_available(self, mime_types):
		"""Check if clipboard with specified mime types is available."""
		if len(self.data_support) == 0:
			return
		provider = self.data_support[0]
		return provider.data_available()


class Provider:
	"""Clipboard functionality provider class defined object that implements
	a single way of setting and getting clipboard data."""

	def available(self):
		"""Test environment and return tuple of boolean values indicating usability."""
		return False, False  # text, data

	def set_text(self, text):
		"""Set text content."""
		pass

	def set_data(self, data, mime_types):
		"""Set data as content with provided list of mime types."""
		pass

	def get_text(self):
		"""Return text value stored in clipboard."""
		return None

	def get_data(self, mime_types):
		"""Return data stored for provided types in clipboard."""
		return None

	def text_available(self):
		"""Check if clipboard with text is available."""
		return False

	def data_available(self, mime_types):
		"""Check if clipboard with specified mime types is available."""
		return False


class GtkProvider(Provider):
	"""Clipboard functionality provided through Gtk API."""

	def __init__(self):
		try:
			self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		except:
			self.clipboard = None

	def available(self):
		"""Test environment and return boolean value indicating usability."""
		text, data = False, False

		if not self.clipboard:
			return text, data

		text = hasattr(self.clipboard, 'set_text') and callable(self.clipboard.set_text)
		data = hasattr(self.clipboard, 'set_with_data') and callable(self.clipboard.set_text)

		return text, data

	def set_text(self, text):
		"""Set text content."""
		self.clipboard.set_text(text, -1)

	def set_data(self, data, mime_types):
		"""Set data as content with provided list of mime types."""
		targets = [(mime_type, 0, 0) for mime_type in mime_types]
		raw_data = data

		def get_func(clipboard, selection, info, data):
			"""Handle request from application"""
			target = selection.get_target()
			selection.set(target, 8, raw_data)

		def clear_func(clipboard, data):
			"""Clear function"""
			pass

		return self.clipboard.set_with_data(targets, get_func, clear_func)

	def get_text(self):
		"""Return text value stored in clipboard."""
		return self.clipboard.wait_for_text()

	def get_data(self, mime_types):
		"""Return data stored for provided types in clipboard."""
		target = mime_types[0]
		return self.clipboard.wait_for_contents(target)

	def text_available(self):
		"""Check if clipboard with text is available."""
		return self.clipboard.wait_is_text_available()

	def data_available(self, mime_types):
		"""Check if clipboard with specified mime types is available."""
		targets_available = [self.clipboard.wait_is_target_available(target) for target in mime_types]
		return any(targets_available)


class FakeProvider(Provider):
	"""Fake provider which offers clipboard functionality only within application."""

	def __init__(self):
		self.text = None
		self.data = {}

	def available(self):
		"""Test environment and return tuple of boolean values indicating usability."""
		return True, True

	def set_text(self, text):
		"""Set text content."""
		self.text = text

	def set_data(self, data, mime_types):
		"""Set data as content with provided list of mime types."""
		for mime_type in mime_types:
			self.data[mime_type] = data

	def get_text(self):
		"""Return text value stored in clipboard."""
		return self.text

	def get_data(self, mime_types):
		"""Return data stored for provided types in clipboard."""
		data = None

		for mime_type in mime_types:
			if mime_type in self.data:
				data = self.data[mime_type]
				break

		return data

	def text_available(self):
		"""Check if clipboard with text is available."""
		return self.text is not None

	def data_available(self, mime_types):
		"""Check if clipboard with specified mime types is available."""
		targets_available = [target in self.data for target in mime_types]
		return any(targets_available)


class CommandProvider(Provider):
	"""Clipboard integration using command line application and piping."""

	def __init__(self):
		commands = ['xclip', 'wl-copy', 'wl-paste']
		self.available_commands = tuple(filter(lambda command: executable_exists(command), commands))

	def available(self):
		"""Test environment and return tuple of boolean values indicating usability."""
		result = len(self.available_commands) > 0
		return result, result

	def set_text(self, text):
		"""Set text content."""
		commands = (
				('wl-copy',),
				('xclip', '-selection', 'clipboard'),
				)

		for command in commands:
			try:
				run(command, input=text, text=True)
			except:
				pass
			else:
				break

	def set_data(self, data, mime_types):
		"""Set data as content with provided list of mime types."""
		commands = (
				('wl-copy', '-t', mime_types[0]),
				('xclip', '-selection', 'clipboard', '-t', mime_types[0]),
				)

		for command in commands:
			try:
				run(command, input=data, text=True)
			except:
				pass
			else:
				break

	def get_text(self):
		"""Return text value stored in clipboard."""
		result = None
		commands = (
				('wl-paste',),
				('xclip', '-selection', 'clipboard', '-o'),
				)

		for command in commands:
			try:
				result = check_output(command).decode('unicode-escape')
			except:
				pass
			else:
				break

		return result

	def get_data(self, mime_types):
		"""Return data stored for provided types in clipboard."""
		result = None
		commands = (
				('wl-paste', '-t', mime_types[0]),
				('xclip', '-selection', 'clipboard', '-o', '-t', mime_types[0]),
				)

		for command in commands:
			try:
				result = check_output(command, input=data, text=True).decode('unicode-escape')
			except:
				pass
			else:
				break

		return result

	def text_available(self):
		"""Check if clipboard with text is available."""
		return self.get_text() is not None

	def data_available(self, mime_types):
		"""Check if clipboard with specified mime types is available."""
		return self.get_data(mime_types) is not None

