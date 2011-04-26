#!/usr/bin/env python
#
#		Sunflower.py
#
#		Copyright (c) 2011. by MeanEYE[rcf]
#		RCF Group, http://rcf-group.com
#
#		This program is free software; you can redistribute it and/or modify
#		it under the terms of the GNU General Public License as published by
#		the Free Software Foundation; either version 3 of the License, or
#		(at your option) any later version.
#
#		This program is distributed in the hope that it will be useful,
#		but WITHOUT ANY WARRANTY; without even the implied warranty of
#		MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#		GNU General Public License for more details.
#
#		You should have received a copy of the GNU General Public License
#		along with this program; if not, write to the Free Software
#		Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#		MA 02110-1301, USA.

import os
import sys
import subprocess

search_paths = os.environ["PATH"].split(os.pathsep)
interpreter_list = ('python2.9', 'python2.8', 'python2.7', 'python2.6')
application_file = os.path.join(os.path.dirname(sys.argv[0]), 'application', 'main.py')

def _can_execute(path):
	"""Check if specified path can be executed"""
	return os.path.exists(path) and os.access(path, os.X_OK)

def _check_interpreter(interpreter):
	"""Check path for existing interpreters"""
	result = None

	for path in search_paths:
		full_path = os.path.join(path, interpreter)

		if _can_execute(full_path):
			# interpreter was found in specified directory
			result = full_path
			break

	return result

def _get_interpreter():
	"""Return latest interpreter"""
	result = None

	# check every interpreter in the list
	for item in interpreter_list:
		full_path = _check_interpreter(item)

		if full_path is not None:
			result = full_path
			break

	return result

# get 2.x interpreter
interpreter = _get_interpreter()

if interpreter is not None:
	# interpreter found, form startup parameters
	params = [interpreter, application_file]
	params.extend(sys.argv[1:])
	
	# create new process with specified parameters
	code = subprocess.call(params)
	sys.exit(code)

else:
	# no valid interpreters found, notify user
	print ("No valid Python 2.x interpreter was found!")
	sys.exit(2)
