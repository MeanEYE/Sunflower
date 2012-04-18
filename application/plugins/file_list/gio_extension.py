import gtk
import gio

from plugin_base.mount_manager_extension import MountManagerExtension


class SambaExtension(MountManagerExtension):
	"""Mount manager extension that provides editing and mounting
	of Samba shares through GIO backend.

	"""

	def __init__(self, parent, window):
		MountManagerExtension.__init__(self, parent, window)

	def unmount(self, uri):
		"""Handle unmounting specified URI"""
		pass

	def get_information(self):
		"""Get extension information"""
		return 'samba', "Samba"
