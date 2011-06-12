import gtk

from widgets.settings_page import SettingsPage

COL_NAME			= 0
COL_PRIMARY_KEY		= 1
COL_PRIMARY_MODS	= 2
COL_SECONDARY_KEY	= 3
COL_SECONDARY_MODS	= 4


class AcceleratorOptions(SettingsPage):
	"""Accelerator options extension class"""

	def __init__(self, parent, application):
		SettingsPage.__init__(self, parent, application, 'accelerators', _('Keybindings'))

		# create list box
		container = gtk.ScrolledWindow()
		container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		container.set_shadow_type(gtk.SHADOW_IN)

		self._accels = gtk.TreeStore(str, int, int, int, int)

		self._list = gtk.TreeView()
		self._list.set_model(self._accels)
		self._list.set_rules_hint(True)

		# create and configure cell renderers
		cell_name = gtk.CellRendererText()
		cell_primary = gtk.CellRendererAccel()
		cell_secondary = gtk.CellRendererAccel()

		# create and pack columns
		col_name = gtk.TreeViewColumn('Test', cell_name, text=COL_NAME)
		col_name.set_min_width(200)
		col_name.set_resizable(True)

		col_primary = gtk.TreeViewColumn(
									'Test',
									cell_primary,
									accel_key=COL_PRIMARY_KEY,
									accel_mods=COL_PRIMARY_MODS
								)
		col_primary.set_min_width(100)

		col_secondary = gtk.TreeViewColumn(
									'Test',
									cell_secondary,
									accel_key=COL_SECONDARY_KEY,
									accel_mods=COL_SECONDARY_MODS
								)
		col_secondary.set_min_width(100)

		self._list.append_column(col_name)
		self._list.append_column(col_primary)
		self._list.append_column(col_secondary)

		# pack interface
		container.add(self._list)

		self.pack_start(container, True, True, 0)
