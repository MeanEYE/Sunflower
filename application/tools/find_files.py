import os
import gtk


class FindFiles(gtk.Window):
	"""Find files tool"""

	def __init__(self, parent, application):
		super(FindFiles, self).__init__(type=gtk.WINDOW_TOPLEVEL)

		self._parent = parent
		self._provider = self._parent.get_provider()
		self._application = application
		self._extensions = []
		self._path = self._parent.path
		
		# configure window
		self.set_title(_('Find files'))
		self.set_default_size(640, 600)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_transient_for(application)
		self.set_border_width(7)
		self.set_wmclass('Sunflower', 'Sunflower')
		
		# create interface
		vbox = gtk.VBox(False, 7)
		
