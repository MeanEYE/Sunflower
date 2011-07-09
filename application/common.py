import os
import user


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


def format_size(size):
	"""Convert size to more human readable format"""
	for x in ['B','kB','MB','GB','TB']:
		if size < 1024.0:
			return "%3.1f %s" % (size, x)
		size /= 1024.0

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
