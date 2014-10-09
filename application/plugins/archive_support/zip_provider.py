import zipfile

from plugin_base.provider import Provider


class ZipProvider(Provider):
	"""Provider for handling of ZIP archives."""

	is_local = False
	protocol = None
	archives = (
			'application/zip',
			'application/jar',
			'application/war'
		)

	def __init__(self, parent, path=None, selection=None):
		Provider.__init__(self, parent, path, selection)

	def list_dir(self, path, relative_to=None):
		"""Get directory list."""
		print path
