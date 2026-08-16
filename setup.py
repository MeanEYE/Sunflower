#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path


def get_translation_files():
	"""Collect compiled translation files, keyed by language directory."""
	return [
			(f'share/locale/{path.parts[1]}/LC_MESSAGES', [str(path)])
			for path in sorted(Path('translations').glob('*/LC_MESSAGES/sunflower.mo'))
		]


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
			'PyGObject',
			'chardet'
			],
		packages=find_packages(),
		package_data={'': ['plugin.conf']},
		data_files=[
			('share/sunflower/images', [str(path) for path in Path('images').rglob('*') if path.is_file() and path.suffix != '.xcf']),
			('share/sunflower/styles', ['styles/main.css']),
			('share/applications', ['Sunflower.desktop']),
			*get_translation_files()
			],
		entry_points={'console_scripts': ['sunflower = sunflower.__main__:main']}
	)
