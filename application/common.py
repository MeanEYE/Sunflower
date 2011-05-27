def format_size(size):
	"""Convert size to more human readable format"""
	for x in ['B','kB','MB','GB','TB']:
		if size < 1024.0:
			return "%3.1f %s" % (size, x)
		size /= 1024.0
