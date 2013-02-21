import gtk
import subprocess

from plugin_base.viewer_extension import ViewerExtension


def register_plugin(application):
	"""Register plugin class with application"""
	application.register_viewer_extension(('text/plain',), GVimViewer)


class GVimViewer(ViewerExtension):
	"""Viewer extension that embeds GVim window into notebook and allows you to
	view files using your configuration.
	
	"""

	def __init__(self, parent):
		ViewerExtension.__init__(self, parent)
		
		self._process = None

		# create container
		self._container = gtk.Viewport()
		self._container.set_shadow_type(gtk.SHADOW_IN)

		# create socket for embeding GVim window
		self._socket = gtk.Socket()
		self._socket.connect('realize', self.__socket_realized)

		# pack interface
		self._container.add(self._socket)
		
	def __socket_realized(self, widget, data=None):
		"""Connect process when socket is realized"""
		socket_id = self._socket.get_id()

		# generate command string
		command = (
				'gvim',
				'--socketid', str(socket_id),
				'-R', self._parent.path
			)

		# create new process
		self._process = subprocess.Popen(command)

	def get_title(self):
		"""Return page title"""
		return _('GVim')

	def get_container(self):
		"""Return container widget to be embeded to notebook"""
		return self._container

	def focus_object(self):
		"""Focus main object in extension"""
		self._socket.child_focus(gtk.DIR_TAB_FORWARD)
