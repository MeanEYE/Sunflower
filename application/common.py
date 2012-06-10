import os
import user
import subprocess


# user directories
class UserDirectory:
	DESKTOP = 'XDG_DESKTOP_DIR'
	DOWNLOADS = 'XDG_DOWNLOAD_DIR'
	TEMPLATES = 'XDG_TEMPLATES_DIR'
	PUBLIC = 'XDG_PUBLICSHARE_DIR'
	DOCUMENTS = 'XDG_DOCUMENTS_DIR'
	MUSIC = 'XDG_MUSIC_DIR'
	PICTURES = 'XDG_PICTURES_DIR'
	VIDEOS = 'XDG_VIDEOS_DIR'


# file mode formats
class AccessModeFormat:
	OCTAL = 0
	TEXTUAL = 1


def format_size(size):
	"""Convert size to more human readable format"""
	for x in ['B','kB','MB','GB','TB']:
		if size < 1024.0:
			return "%3.1f %s" % (size, x)
		size /= 1024.0

def format_mode(mode, format):
	"""Convert mode to more human readable format"""
	result = ''

	if format == AccessModeFormat.TEXTUAL:
		# create textual representation
		mask = 256

		for i in 'rwxrwxrwx':
			result += i if mode & mask else '-'
			mask >>= 1

	elif format == AccessModeFormat.OCTAL:
		# create octal
		result = oct(mode)

	return result

def get_user_directory(directory):
	"""Get full path to current users predefined directory"""
	result = None
	config_file = os.path.join(user.home, '.config', 'user-dirs.dirs')

	if os.path.isfile(config_file):
		# read configuration file
		with open(config_file, 'r') as raw_file:
			lines = raw_file.read().splitlines(False)

		# get desired path
		for line in lines:
			data = line.split('=')

			if data[0] == directory:
				result = data[1].replace('$HOME', user.home)
				result = result.strip('"')
				break

	return result

def is_x_app(command):
	"""Checks if command uses grafical user interfaces."""
	try:
		output = subprocess.Popen(
							[command],
							env={'LD_TRACE_LOADED_OBJECTS':'1'},
							stdout=subprocess.PIPE
						).communicate()

	except OSError as error:
		# report error to user
		raise error

	return 'libX11.so' in output[0]

def executable_exists(command):
	"""Check if specified command exists in search path"""
	paths = os.environ["PATH"].split(os.pathsep)
	result = False

	for path in paths:
		if os.path.exists(os.path.join(path, command)):
			result = True
			break

	return result
