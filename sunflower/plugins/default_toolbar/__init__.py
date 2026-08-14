from gi.repository import Gtk

# GTK 4 removed tool items, plain widgets are used on the toolbar box
if Gtk.get_major_version() == 3:
	ToolbarButton = Gtk.ToolButton
	SeparatorBase = Gtk.SeparatorToolItem

else:
	ToolbarButton = Gtk.Button
	SeparatorBase = Gtk.Separator
