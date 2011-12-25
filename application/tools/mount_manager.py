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
		self.set_wmclass('Sunflower', 'Sunflower')
		self.set_border_width(7)

		self.connect('delete-event', self._hide)
		
		# create user interface
		vbox = gtk.VBox(False, 5)
		
		hbox_controls = gtk.HBox(False, 5)
		
		# create a tree view
		container = gtk.ScrolledWindow() 
		container.set_shadow_type(gtk.SHADOW_IN)
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		
		self._list = gtk.TreeView()
		self._list.connect('key-press-event', self._handle_key_press)

		# create controls
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.connect('clicked', self._hide)
		
		# pack user interface
		container.add(self._list)

		hbox_controls.pack_end(button_close, False, False, 0)
		
		vbox.pack_start(container, True, True, 0)
		vbox.pack_start(hbox_controls, False, False, 0)
		
		self.add(vbox)

	def _hide(self, widget=None, data=None):
		"""Hide mount manager"""
		self.hide()

		return True

	def _handle_key_press(self, widget, event, data=None):
		"""Handle pressing keys in mount manager list"""
		result = False

		if event.keyval == gtk.keysyms.Return:
			result = True

		elif event.keyval == gtk.keysyms.Escape:
			# hide window on escape
			self._hide()
			result = True

		return result
				
	def show(self, widget=None, data=None):
		"""Show mount manager"""
		gtk.Window.show_all(self)
