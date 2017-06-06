import os
import sys

import random
import string
import threading

import unittest
from testfixtures import TempDirectory

# to run with pycharm helper
# sys.argv[0] = os.getcwd()+'/main.py'
# sys.path.insert(1, os.getcwd())

# to run in Sunflower/tests
sys.argv[0] = os.path.dirname(os.path.dirname(sys.argv[0]))+'/application/'
sys.path.insert(1, sys.argv[0])

from gui.main_window import MainWindow
from operation import Operation, CopyOperation, MoveOperation
from plugins.file_list.local_provider import LocalProvider


class GlobalExceptionWatcher(object):
	def _store_excepthook(self):
		'''
		Uses as an exception handlers which stores any uncaught exceptions.
		'''
		formated_exc = self.__org_hook()
		self._exceptions.append(formated_exc)
		return formated_exc

	def __enter__(self):
		'''
		Register us to the hook.
		'''
		self._exceptions = []
		self.__org_hook = threading._format_exc
		threading._format_exc = self._store_excepthook

	def __exit__(self, type, value, traceback):
		'''
		Remove us from the hook, assure no exception were thrown.
		'''
		threading._format_exc = self.__org_hook
		if len(self._exceptions) != 0:
			tracebacks = os.linesep.join(self._exceptions)
			raise Exception('Exceptions in other threads: %s' % tracebacks)


class OperationTestCase(unittest.TestCase):

	def setUp(self):
		self.temp_dir = TempDirectory()
		MainWindow._parse_arguments = lambda *args: False
		self.app = MainWindow()
		self.source = self.temp_dir.makedir('source')
		self.dest = self.temp_dir.makedir('dest')
		self.files = []

		for x in xrange(20):
			filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
			with open('/dev/urandom', 'rb') as urandom:
				self.temp_dir.write(('source', filename), urandom.read(1024))
				self.files.append(filename)

		self.source_provider = LocalProvider(self.app, self.source)
		self.destination_provider = LocalProvider(self.app, self.dest)

	def tearDown(self):
		TempDirectory.cleanup_all()
		self.app.destroy()


class CopyOperationTestCase(OperationTestCase):

	def test_copy_simple(self):

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				False,          # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)


		operation = CopyOperation(self.app, self.source_provider, self.destination_provider, options)
		operation.set_selection(self.files)
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(os.listdir(self.source), os.listdir(self.dest))
		for file in self.files:
			self.assertEqual(self.temp_dir.read(('source', file)), self.temp_dir.read(('dest', file)))

	def test_copy_silent_same_file(self):

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
		with open('/dev/urandom', 'rb') as urandom:
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', filename), urandom.read(1024))

		source_provider = LocalProvider(self.app, self.source)
		destination_provider = LocalProvider(self.app, self.dest)

		operation = CopyOperation(self.app, source_provider, destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(self.temp_dir.read(('source', filename)), self.temp_dir.read(('dest', filename)))

	def test_copy_silent_same_file(self):
		# Without SILENT_OVERWRITE dont copy file same file

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
		with open('/dev/urandom', 'rb') as urandom:
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', filename), urandom.read(1024))

		source_provider = LocalProvider(self.app, self.source)
		destination_provider = LocalProvider(self.app, self.dest)

		operation = CopyOperation(self.app, source_provider, destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

	def test_copy_from_expanded(self):

			options = (
					'*',            # FILE_TYPE = 0
					self.dest,      # DESTINATION = 1
					True,           # SET_OWNER = 2
					True,           # SET_MODE = 3
					True,           # SET_TIMESTAMP = 4
					False,          # SILENT = 5
					False,          # SILENT_MERGE = 6
					False,          # SILENT_OVERWRITE = 7
			)

			self.files = []

			self.source = self.temp_dir.makedir('source/subdir')
			filename = 'subdir/{}'.format(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)))
			with open('/dev/urandom', 'rb') as urandom:
				self.files.append(self.temp_dir.write(('source', filename), urandom.read(1024)))

			operation = CopyOperation(self.app, self.source_provider, self.destination_provider, options)
			operation.set_selection(self.files)
			with GlobalExceptionWatcher():
				operation.start()
				operation.join()

			self.assertEqual(os.listdir(self.source), os.listdir(self.dest))
			for file in self.files:
				self.assertEqual(self.temp_dir.read(('source', file)), self.temp_dir.read(('dest', file)))

	def test_copy_from_expanded_silent_same(self):

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		self.files = []

		self.source = self.temp_dir.makedir('source/subdir')
		filename = 'subdir/{}'.format(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)))
		with open('/dev/urandom', 'rb') as urandom:
			self.files.append(self.temp_dir.write(('source', filename), urandom.read(1024)))
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', os.path.basename(filename)), urandom.read(1024))

		operation = CopyOperation(self.app, self.source_provider, self.destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(self.temp_dir.read(('source', filename)), self.temp_dir.read(('dest', os.path.basename(filename))))

	def test_copy_from_expanded_silent_same(self):
		# Without SILENT_OVERWRITE dont copy file same file

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		self.files = []

		self.source = self.temp_dir.makedir('source/subdir')
		filename = 'subdir/{}'.format(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)))
		with open('/dev/urandom', 'rb') as urandom:
			self.files.append(self.temp_dir.write(('source', filename), urandom.read(1024)))
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', os.path.basename(filename)), urandom.read(1024))

		operation = CopyOperation(self.app, self.source_provider, self.destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()


class MoveOperationTestCase(OperationTestCase):

	def test_move_simple(self):

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				False,          # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		source_listdir = os.listdir(self.source)
		source_content = []
		for filename in self.files:
			source_content.append(self.temp_dir.read(('source', filename)))

		operation = MoveOperation(self.app, self.source_provider, self.destination_provider, options)
		operation.set_selection(self.files)
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(os.listdir(self.source), [])
		self.assertEqual(source_listdir, os.listdir(self.dest))

		dest_content = []

		for filename in self.files:
			dest_content.append(self.temp_dir.read(('dest', filename)))

		self.assertEqual(dest_content, source_content)

	def test_move_silent_same_file(self):

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
		with open('/dev/urandom', 'rb') as urandom:
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', filename), urandom.read(1024))

		source_content = (self.temp_dir.read(('source', filename)))

		source_provider = LocalProvider(self.app, self.source)
		destination_provider = LocalProvider(self.app, self.dest)

		operation = MoveOperation(self.app, source_provider, destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(source_content, self.temp_dir.read(('dest', filename)))
		self.assertFalse(filename in os.listdir(self.source))

	def test_move_silent_same_file(self):
		# Without SILENT_OVERWRITE dont move file same file

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
		with open('/dev/urandom', 'rb') as urandom:
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', filename), urandom.read(1024))

		source_content = (self.temp_dir.read(('source', filename)))

		source_provider = LocalProvider(self.app, self.source)
		destination_provider = LocalProvider(self.app, self.dest)

		operation = MoveOperation(self.app, source_provider, destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertTrue(filename in os.listdir(self.source))

	def test_move_from_expanded(self):

			options = (
					'*',            # FILE_TYPE = 0
					self.dest,      # DESTINATION = 1
					True,           # SET_OWNER = 2
					True,           # SET_MODE = 3
					True,           # SET_TIMESTAMP = 4
					False,          # SILENT = 5
					False,          # SILENT_MERGE = 6
					False,          # SILENT_OVERWRITE = 7
			)

			self.files = []

			self.source = self.temp_dir.makedir('source/subdir')
			for x in xrange(20):
				filename = 'subdir/{}'.format(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)))
				with open('/dev/urandom', 'rb') as urandom:
					self.temp_dir.write(('source', filename), urandom.read(1024))
					self.files.append(filename)

			source_listdir = os.listdir(self.source)
			source_content = []
			for filename in self.files:
				source_content.append(self.temp_dir.read(('source', filename)))


			operation = MoveOperation(self.app, self.source_provider, self.destination_provider, options)
			operation.set_selection(self.files)
			with GlobalExceptionWatcher():
				operation.start()
				operation.join()

			self.assertEqual(os.listdir(self.source), [])
			self.assertEqual(source_listdir, os.listdir(self.dest))

			dest_content = []

			for file in self.files:
				dest_content.append(self.temp_dir.read(('dest', os.path.basename(file))))

			self.assertEqual(dest_content, source_content)

	def test_move_from_expanded_silent_same(self):

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				True,          # SILENT_MERGE = 6
				True,          # SILENT_OVERWRITE = 7
		)

		self.source = self.temp_dir.makedir('source/subdir')
		filename = 'subdir/{}'.format(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)))
		with open('/dev/urandom', 'rb') as urandom:
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', os.path.basename(filename)), urandom.read(1024))

		source_listdir = os.listdir(self.source)
		source_content = (self.temp_dir.read(('source', filename)))

		operation = MoveOperation(self.app, self.source_provider, self.destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(os.listdir(self.source), [])
		self.assertEqual(source_listdir, os.listdir(self.dest))

	def test_move_from_expanded_silent_same(self):
		# Without SILENT_OVERWRITE dont move file same file

		options = (
				'*',            # FILE_TYPE = 0
				self.dest,      # DESTINATION = 1
				True,           # SET_OWNER = 2
				True,           # SET_MODE = 3
				True,           # SET_TIMESTAMP = 4
				True,           # SILENT = 5
				False,          # SILENT_MERGE = 6
				False,          # SILENT_OVERWRITE = 7
		)

		self.source = self.temp_dir.makedir('source/subdir')
		filename = 'subdir/{}'.format(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)))
		with open('/dev/urandom', 'rb') as urandom:
			self.temp_dir.write(('source', filename), urandom.read(1024))
			self.temp_dir.write(('dest', os.path.basename(filename)), urandom.read(1024))

		source_listdir = os.listdir(self.source)
		source_content = (self.temp_dir.read(('source', filename)))

		operation = MoveOperation(self.app, self.source_provider, self.destination_provider, options)
		operation.set_selection([filename])
		with GlobalExceptionWatcher():
			operation.start()
			operation.join()

		self.assertEqual(source_listdir, os.listdir(self.dest))


if __name__ == '__main__':

		unittest.main()
