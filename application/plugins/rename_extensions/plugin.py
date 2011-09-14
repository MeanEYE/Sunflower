from default import DefaultRename
from letter_case import LetterCaseRename
from audio_metadata import AudioMetadataRename


def register_plugin(application):
	"""Register plugin classes with application"""
	application.register_rename_extension('default', DefaultRename)
	application.register_rename_extension('letter_case', LetterCaseRename)
	application.register_rename_extension('audio_metadata', AudioMetadataRename)
