from gi.repository import Gtk, GObject


class StatusBar(Gtk.Box):
	"""Plugin status bar"""

	def __init__(self):
		Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=15)

		set_border_width(self, 4)
		if Gtk.get_major_version() == 3:
			self.set_property('no-show-all', True)

		else:
			self.hide()

		self._icons = {}
		self._labels = {}

		# create default label
		self._label = Gtk.Label()
		self._label.set_use_markup(True)
		self._label.set_xalign(0)
		self._label.set_yalign(0.5)
		self._label.show()

		# pack interface
		if Gtk.get_major_version() == 3:
			self.pack_end(self._label, True, True, 0)

		else:
			self._label.set_hexpand(True)
			self.append(self._label)

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
		icon = Gtk.Image()
		if Gtk.get_major_version() == 3:
			icon.set_from_icon_name(icon_name, Gtk.IconSize.MENU)

		else:
			icon.set_from_icon_name(icon_name)
		icon.show()

		label = Gtk.Label(label=value)
		label.set_use_markup(True)
		label.set_xalign(0)
		label.set_yalign(0.5)
		label.show()

		# configure tooltip
		if tooltip is not None:
			label.set_tooltip_text(tooltip)
			icon.set_tooltip_text(tooltip)

		# pack group
		hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
		hbox.show()

		if Gtk.get_major_version() == 3:
			hbox.pack_start(icon, False, False, 0)
			hbox.pack_start(label, False, False, 0)

			self.pack_start(hbox, False, False, 0)

		else:
			hbox.append(icon)
			hbox.append(label)

			# groups are packed at the start, default label stays at the end
			self.append(hbox)
			self.reorder_child_after(self._label, hbox)

		# add group to local cache
		self._labels[name] = label
		self._icons[name] = icon
