import os
import user
import subprocess
import locale


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


# file size formats
class SizeFormat:
	LOCAL = 0
	SI = 1
	IEC = 2

	multiplier = {
			SI: 1000.0,
			IEC: 1024.0
		}
	unit_names = {
			SI: ['B','kB','MB','GB','TB'],
			IEC: ['B','KiB','MiB','GiB','TiB']
		}


def format_size(size, format_type, include_unit=True):
	"""Convert size to more human readable format"""
	result = size

	# format as localized decimal number
	if format_type == SizeFormat.LOCAL:
		result = ('{0}', '{0} B')[include_unit].format(locale.format('%d', size, True))

	# format based on specified standard
	else:
		names = SizeFormat.unit_names[format_type]
		multiplier = SizeFormat.multiplier[format_type]

		for name in names:
			if size < multiplier:
				result = '{0:3.1f} {1}'.format(size, name)
				break

			size /= multiplier

	return result

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

def get_cache_directory():
	"""Get full path to cache files for curring user."""
	if 'XDG_CACHE_HOME' in os.environ:
		result = os.path.abspath(os.environ['XDG_CACHE_HOME'])
	else:
		result = os.path.join(user.home, '.cache')

	return result

def get_config_directory():
	"""Get full path to configuration files for current user."""
	if 'XDG_CONFIG_HOME' in os.environ:
		result = os.path.abspath(os.environ['XDG_CONFIG_HOME'])
	else:
		result = os.path.join(user.home, '.config')

	return result

def get_data_directory():
	"""Get full path to user data files."""
	if 'XDG_DATA_HOME' in os.environ:
		result = os.path.abspath(os.environ['XDG_DATA_HOME'])
	else:
		result = os.path.join(user.home, '.local', 'share')

	return result

def get_user_directory(directory):
	"""Get full path to current users predefined directory"""
	result = None
	config_file = os.path.join(get_config_directory(), 'user-dirs.dirs')

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
		env = os.environ.copy()
		env.update({'LD_TRACE_LOADED_OBJECTS': '1'})
		output = subprocess.Popen(
							[command],
							env=env,
							stdout=subprocess.PIPE
						).communicate()

	except OSError as error:
		# report error to user
		raise error

	libraries = ('libX11.so', 'libvlc.so')
	matching = filter(lambda library: library in output[0], libraries)

	return len(matching) > 0

def executable_exists(command):
	"""Check if specified command exists in search path"""
	default_paths = os.pathsep.join(('/bin', '/usr/bin', '/usr/local/bin'))
	search_paths = os.environ.get('PATH', default_paths).split(os.pathsep)
	found_commands = filter(lambda path: os.path.exists(os.path.join(path, command)), search_paths)

	return len(found_commands) > 0
