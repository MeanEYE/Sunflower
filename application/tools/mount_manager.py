import gtk


class MountManager(gtk.Window):
	"""Display and organize mounts"""
	
	def __init__(self, application):
		gtk.Window.__init__(self, type=gtk.WINDOW_TOPLEVEL)
		
		self._application = application
		
		# configure window
		self.set_title(_('Mount manager'))
		self.set_default_size(320, 240)
		self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
		self.set_skip_taskbar_hint(True)
		self.set_modal(True)
		self.set_transient_for(application)
		self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.set_wmclass('Sunflower', 'Sunflower')
		
		# create user interface
		vbox = gtk.VBox(False, 5)
		vbox.set_border_width(7)
		
		hbox_controls = gtk.HBox(False, 5)
		
		# create a tree view
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		
		self._list = gtk.TreeView()
		
		# pack user interface
		container.add(self._list)
		
		vbox.pack_start(container, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)
		
		self.add(vbox)
				
	def show(self, widget=None, data=None):
		"""Show mount manager"""
		gtk.Window.show_all(self)
