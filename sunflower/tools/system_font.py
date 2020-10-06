from __future__ import absolute_import

from gi.repository import Gio, Pango

MONOSPACE_FONT_STRING = None

def get_monospace_font_string():
	global MONOSPACE_FONT_STRING
	if MONOSPACE_FONT_STRING is None:
		schema = Gio.SettingsSchemaSource.get_default()
		gnome_interface = schema.lookup('org.gnome.desktop.interface',True)
		if gnome_interface is None:
			# not in gnome desktop environment, use 'monospace 10'
			MONOSPACE_FONT_STRING = 'monospace 10'
		else:
			settings = Gio.Settings.new('org.gnome.desktop.interface')
			MONOSPACE_FONT_STRING = settings.get_string('monospace-font-name')
	return MONOSPACE_FONT_STRING
