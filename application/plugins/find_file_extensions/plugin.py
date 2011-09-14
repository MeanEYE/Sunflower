from default import DefaultFindFiles
from size import SizeFindFiles
from contents import ContentsFindFiles


def register_plugin(application):
	"""register plugin classes with application"""
	application.register_find_extension('default', DefaultFindFiles)
	application.register_find_extension('size', SizeFindFiles)
	application.register_find_extension('contents', ContentsFindFiles)
