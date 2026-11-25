#!/usr/bin/env python3

import re

from setuptools import setup, find_packages
from pathlib import Path


def get_translation_files():
	"""Collect compiled translation files, keyed by language directory."""
	return [
			(f'share/locale/{path.parts[1]}/LC_MESSAGES', [str(path)])
			for path in sorted(Path('translations').glob('*/LC_MESSAGES/sunflower.mo'))
		]


def get_version():
	"""Get software version from the main window.

	Version is parsed out of the source instead of importing the module, as
	that would require GTK to be available while building packages."""
	source = Path('sunflower/gui/main_window.py').read_text()
	major = re.search(r"'major': (\d+)", source).group(1)
	minor = re.search(r"'minor': (\d+)", source).group(1)
	build = re.search(r"'build': (\d+)", source).group(1)
	result = '{0}.{1}.{2}'.format(major, minor, build)

	return result


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
			('share/sunflower/images', [str(path) for path in Path('images').rglob('*') if path.is_file() and path.suffix != '.xcf' and path.name != 'screenshot.png']),
			('share/sunflower/styles', ['styles/main.css']),
			('share/icons/hicolor/scalable/apps', ['images/sunflower.svg']),
			('share/applications', ['Sunflower.desktop']),
			*get_translation_files()
			],
		entry_points={'console_scripts': ['sunflower = sunflower.__main__:main']}
	)
