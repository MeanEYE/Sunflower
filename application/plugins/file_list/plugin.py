from file_list import FileList
from trash_list import TrashList
from gio_extension import SambaExtension, FtpExtension, DavExtension, SftpExtension
from gio_provider import NetworkProvider, TrashProvider, DavProvider, DavsProvider, Gphoto2Provider, MtpProvider
from gio_provider import SambaProvider, FtpProvider, SftpProvider
from local_provider import LocalProvider


def register_plugin(application):
	"""Register plugin classes with application."""
	application.register_class('file_list', _('Local file list'), FileList)
	application.register_class('trash_list', _('Trash can'), TrashList)

	# register providers
	application.register_provider(LocalProvider)
	application.register_provider(SambaProvider)
	application.register_provider(FtpProvider)
	application.register_provider(SftpProvider)
	application.register_provider(NetworkProvider)
	application.register_provider(TrashProvider)
	application.register_provider(DavProvider)
	application.register_provider(DavsProvider)
	application.register_provider(Gphoto2Provider)
	application.register_provider(MtpProvider)

	# register mount manager extension
	application.register_mount_manager_extension(SambaExtension)
	application.register_mount_manager_extension(FtpExtension)
	application.register_mount_manager_extension(SftpExtension)
	application.register_mount_manager_extension(DavExtension)
