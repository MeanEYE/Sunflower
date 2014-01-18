'''
@author: sevka
'''
import gtk
import os
import gio
import gobject
import copy
import pango


class BreadCrumbs(gtk.HBox):
	'''
	Bread crumbs widget
	'''
	CRUMBS_TYPE_NORMAL 		= 1
	CRUMBS_TYPE_SMART 		= 2
	CRUMBS_TYPE_COMPRESS 	= 3

	def __init__(self, parent, callback, options = {'smart_bread_crumbs': True}):
		'''
		Bread Crumbs construnctor
		:param callback: Callback, which called when directory has to be changed
		'''
		gtk.HBox.__init__(self)

		self._parent = parent
		self._options = options
		self._callback = callback
	
		self._longest_common_path = None
		self._path = None
		self._lastWidth = 0
		self._colors = None

		self._pathHBox = gtk.HBox()
		self.connect('size_allocate', self._path_resized)
		
		self.pack_start(self._pathHBox, True, True)
		self.set_no_show_all(True)
	
	def __get_smart_crumbs_color(self, c):
		s = c.saturation
		v = c.value
		if s > 0.3:
			s = s / 2
			v = v * 1.5
		else:
			v = v / 1.5 if v > 0.5 else v * 2.5
		c2 =  gtk.gdk.color_from_hsv(c.hue, s, v)
		return c2
		
	def apply_color(self, colors = None):
		if colors:
			self._colors = colors
		if self._colors:
			smart_crumbs_color = self.__get_smart_crumbs_color(self._colors[0])
			for child in self._pathHBox.get_children():
				if child.type == self.CRUMBS_TYPE_SMART:
					child.get_children()[0].modify_fg(gtk.STATE_NORMAL, smart_crumbs_color)
				else:
					child.get_children()[0].modify_fg(gtk.STATE_NORMAL, self._colors[1])
				
				child.modify_bg(gtk.STATE_NORMAL, self._colors[0])

	def _path_clicked(self, sender, b, path):
		'''
		Called when path clicked. Then Callback called
		'''
		self._callback(path)
		self.apply_color(self._colors)
	
	def _calculateVisibledCrumbsWidth(self):
		labelWidth = 0
		for child in self._pathHBox.get_children():
			if child.get_visible():
				labelWidth += child.get_allocation().width
		return labelWidth

	def _path_resized(self, sender, allocation):
		labelWidth = self._calculateVisibledCrumbsWidth()
		lastWidth = self._lastWidth
		self._lastWidth = self._pathHBox.get_allocation().width
		if labelWidth < self._pathHBox.get_allocation().width and (self._shortenNormal or self._shortenSmart) and lastWidth > 0 and self._pathHBox.get_allocation().width > lastWidth:
			self.refresh()
			return
		
		labelWidth = self._calculateVisibledCrumbsWidth()
		while labelWidth >= self._pathHBox.get_allocation().width:

			for child in reversed(self._pathHBox.get_children()):
				if child.type == self.CRUMBS_TYPE_SMART and child.get_visible():
					child.hide()
					self._shortenSmart = True
					labelWidth = self._calculateVisibledCrumbsWidth()
					break
			else:
				normalCrumbs = []
				self._shortenNormal = True
				self._compressEventBox.show()
				for child in self._pathHBox.get_children():
					if child.type == self.CRUMBS_TYPE_NORMAL and child.get_visible():
						normalCrumbs.append(child)
				i = int(round(len(normalCrumbs) / 2.0))
				if (i < len(normalCrumbs) - 1):
					normalCrumbs[i].hide()
					labelWidth = self._calculateVisibledCrumbsWidth()
				else:
					normalCrumbs[0].hide()
					break


	def _mouse_enter(self, sender, b, n):
		'''
		Method called when mouse enters path item
		'''
		children = self._pathHBox.get_children()
		last_underline = False
		for i in range(0, n+2):
			if children[i].get_children()[0].get_label() == "/...":
				last_underline = True
			if i == n+1 and not last_underline:
				break
			attr = pango.AttrList()
			attr.insert(pango.AttrUnderline(pango.UNDERLINE_SINGLE, 0, len(children[i].get_children()[0].get_text())))
			children[i].get_children()[0].set_attributes(attr)
			if children[i].type == self.CRUMBS_TYPE_SMART:
				children[i].get_children()[0].modify_fg(gtk.STATE_NORMAL, self._colors[1])
			
	
	def _mouse_leave(self, sender, b, n):
		'''
		Method called when mouse leaves path item
		'''
		children = self._pathHBox.get_children()
		for i in range(0,n+2):
			attr = pango.AttrList()
			attr.insert(pango.AttrUnderline(pango.UNDERLINE_NONE, 0, len(children[i].get_children()[0].get_text())))
			children[i].get_children()[0].set_attributes(attr)
			if children[i].type == self.CRUMBS_TYPE_SMART:
				children[i].get_children()[0].modify_fg(gtk.STATE_NORMAL, self.__get_smart_crumbs_color(self._colors[0]))

	def refresh(self, path = None):
		'''
		Refresh panel on directory change
		:param path: new directory
		'''
		if path == None:
			path = self._path
		self._shortenNormal = False
		self._shortenSmart = False
		for child in self._pathHBox.get_children():
			self._pathHBox.remove(child)
		pathToCD = '/'
		if path == '/':
			items = ['']
		else:
			items = path.split('/')
		
		if not self._longest_common_path:
			self._longest_common_path = self._path
		else:
			commonPath = os.path.commonprefix([path, self._path])
			commonPath2 = os.path.commonprefix([path, self._longest_common_path])
			if commonPath:
				if len(path) > len(self._longest_common_path) or path != commonPath2:
					self._longest_common_path = path
			else:
				self._longest_common_path = path
		k = 0
		for item in items:
			pathToCD = os.path.join(pathToCD, item)
			if item != '' or len(items) == 1:
				item = '/' + item
			eventBox = gtk.EventBox()
			label = gtk.Label(item)
			eventBox.add(label)
			eventBox.type = self.CRUMBS_TYPE_NORMAL
			eventBox.connect('button-press-event', self._path_clicked, pathToCD)
			eventBox.connect('enter-notify-event', self._mouse_enter, k)
			eventBox.connect('leave-notify-event', self._mouse_leave, k)
			if round(len(items) / 2.0) == k:
				self._compressEventBox = gtk.EventBox();
				self._compressEventBox.type = self.CRUMBS_TYPE_COMPRESS
				self._compressEventBox.add(gtk.Label("/..."))
				self._pathHBox.pack_start(self._compressEventBox, False, False)
				self._compressEventBox.hide()
			self._pathHBox.pack_start(eventBox, False, False)

			k += 1
			
		if self._options['smart_bread_crumbs'] and self._longest_common_path and len(self._longest_common_path) > len(path):
			items2 = self._longest_common_path.split('/')
			i = 0
			for item in items2:
				i += 1
				if i > len(items):
					pathToCD = os.path.join(pathToCD, item)
					eventBox = gtk.EventBox()
					if i == (len(items) + 1) and len(items) == 1 and items[0] == '':
						label = gtk.Label(item)
					else:
						label = gtk.Label('/' + item)
					font = pango.FontDescription()
#					font.set_weight(pango.WEIGHT_THIN)
#					font.set_style(pango.STYLE_ITALIC)
					label.modify_font(font)
					eventBox.add(label)
					eventBox.type = self.CRUMBS_TYPE_SMART
					eventBox.connect('button-press-event', self._path_clicked, pathToCD)
					eventBox.connect('enter-notify-event', self._mouse_enter, k)
					eventBox.connect('leave-notify-event', self._mouse_leave, k)
					self._pathHBox.pack_start(eventBox, False, False)
					k += 1
		self._path = path
		self.show()
		self._pathHBox.show_all()
		if not self._shortenNormal:
			self._compressEventBox.hide()
		self.apply_color()
