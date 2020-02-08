#!/usr/bin/env python3

from setuptools import setup, find_packages

def get_version():
	"""Get software version from the main window."""
	import gi
	gi.require_version('Gtk', '3.0')
	gi.require_version('Notify', '0.7')
	from sunflower.gui.main_window import MainWindow
	return '{major}.{minor}.{build}'.format(**MainWindow.version)


setup(
		name='Sunflower',
		version=get_version(),
		description='Twin-panel file manager.',
		author='Mladen Mijatov',
		author_email='meaneye.rcf@gmail.com',
		url='https://sunflower-fm.org',
		license='GPLv3',
		install_requires=[
			'gir1.2-gtk-3.0 >= 3.22',
			'gir1.2-notify >= 0.7',
			'gir1.2-gdkpixbuf >= 2.0',
			'gir1.2-vte >= 2.90',
			'gir1.2-glib >= 2.0',
			'gir1.2-pango',
			],
		packages=find_packages(),
		include_package_data=True,
		data_files=[
			('share/icons/hicolor/scalable/apps', ['images/sunflower.svg']),
			('share/pixmaps/sunflower', ['images/splash.png']),
			('share/applications', ['Sunflower.desktop'])
			],
		entry_points={'console_scripts': ['sunflower = sunflower.__main__:main']}
		)
