from zip_provider import ZipProvider


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_provider(ZipProvider)
