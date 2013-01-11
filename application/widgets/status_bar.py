import gtk


class StatusBar(gtk.HBox):
	"""Plugin status bar"""

	def __init__(self):
		gtk.HBox.__init__(self, False, 15)

		self.set_border_width(1)
		self.set_property('no-show-all', True)

		self._icons = {}
		self._labels = {}

		# create default label
		self._label = gtk.Label()
		self._label.set_use_markup(True)
		self._label.set_alignment(0, 0.5)
		self._label.show()

		# pack interface
		self.pack_end(self._label, True, True, 0)

	def set_text(self, text, group=None):
		"""Set default label text"""
		if group is None:
			# set default label
			self._label.set_markup(text)

		elif group in self._labels:
			# set specified group label
			self._labels[group].set_markup(text)

	def add_group_with_icon(self, name, icon_name, value='', tooltip=None):
		"""Add status bar group with icon"""
		icon = gtk.Image()
		icon.set_from_icon_name(icon_name, gtk.ICON_SIZE_MENU)
		icon.show()

		label = gtk.Label(value)
		label.set_use_markup(True)
		label.set_alignment(0, 0.5)
		label.show()

		# configure tooltip
		if tooltip is not None:
			label.set_tooltip_text(tooltip)
			icon.set_tooltip_text(tooltip)

		# pack group
		hbox = gtk.HBox(False, 3)
		hbox.show()

		hbox.pack_start(icon, False, False, 0)
		hbox.pack_start(label, False, False, 0)

		self.pack_start(hbox, False, False, 0)

		# add group to local cache
		self._labels[name] = label
		self._icons[name] = icon
