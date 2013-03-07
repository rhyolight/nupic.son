#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests for google.apphosting.tools.devappserver2.devappserver2."""


import argparse
import getpass
import itertools
import os
import os.path
import tempfile
import unittest

import google
import mox

from google.appengine.tools.devappserver2 import devappserver2


class WinError(Exception):
  pass


class GenerateStoragePathsTest(unittest.TestCase):
  """Tests for devappserver._generate_storage_paths."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(getpass, 'getuser')
    self.mox.StubOutWithMock(tempfile, 'gettempdir')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_working_getuser(self):
    getpass.getuser().AndReturn('johndoe')
    tempfile.gettempdir().AndReturn('/tmp')

    self.mox.ReplayAll()
    self.assertEqual(
        [os.path.join('/tmp', 'appengine.myapp.johndoe'),
         os.path.join('/tmp', 'appengine.myapp.johndoe.1'),
         os.path.join('/tmp', 'appengine.myapp.johndoe.2')],
        list(itertools.islice(devappserver2._generate_storage_paths('myapp'),
                              3)))
    self.mox.VerifyAll()

  def test_broken_getuser(self):
    getpass.getuser().AndRaise(Exception())
    tempfile.gettempdir().AndReturn('/tmp')

    self.mox.ReplayAll()
    self.assertEqual(
        [os.path.join('/tmp', 'appengine.myapp'),
         os.path.join('/tmp', 'appengine.myapp.1'),
         os.path.join('/tmp', 'appengine.myapp.2')],
        list(itertools.islice(devappserver2._generate_storage_paths('myapp'),
                              3)))
    self.mox.VerifyAll()


class GetStoragePathTest(unittest.TestCase):
  """Tests for devappserver._get_storage_path."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(devappserver2, '_generate_storage_paths')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_no_path_given_directory_does_not_exist(self):
    path = tempfile.mkdtemp()
    os.rmdir(path)
    devappserver2._generate_storage_paths('myapp').AndReturn([path])

    self.mox.ReplayAll()
    self.assertEqual(
        path,
        devappserver2._get_storage_path(None, 'myapp'))
    self.mox.VerifyAll()
    self.assertTrue(os.path.isdir(path))

  def test_no_path_given_directory_exists(self):
    path1 = tempfile.mkdtemp()
    os.chmod(path1, 0777)
    path2 = tempfile.mkdtemp()  # Made with mode 0700.

    devappserver2._generate_storage_paths('myapp').AndReturn([path1, path2])

    self.mox.ReplayAll()
    self.assertEqual(
        path2,
        devappserver2._get_storage_path(None, 'myapp'))
    self.mox.VerifyAll()

  def test_path_given_does_not_exist(self):
    path = tempfile.mkdtemp()
    os.rmdir(path)

    self.assertEqual(
        path,
        devappserver2._get_storage_path(path, 'myapp'))
    self.assertTrue(os.path.isdir(path))

  def test_path_given_not_directory(self):
    _, path = tempfile.mkstemp()

    self.assertRaises(
        IOError,
        devappserver2._get_storage_path, path, 'myapp')

  def test_path_given_exists(self):
    path = tempfile.mkdtemp()

    self.assertEqual(
        path,
        devappserver2._get_storage_path(path, 'myapp'))


class PortParserTest(unittest.TestCase):

  def test_valid_port(self):
    self.assertEqual(8080, devappserver2.PortParser()('8080'))

  def test_port_zero_allowed(self):
    self.assertEqual(0, devappserver2.PortParser()('0'))

  def test_port_zero_not_allowed(self):
    self.assertRaises(argparse.ArgumentTypeError,
                      devappserver2.PortParser(allow_port_zero=False), '0')

  def test_negative_port(self):
    self.assertRaises(argparse.ArgumentTypeError, devappserver2.PortParser(),
                      '-1')

  def test_port_too_high(self):
    self.assertRaises(argparse.ArgumentTypeError, devappserver2.PortParser(),
                      '65536')

  def test_port_max_value(self):
    self.assertEqual(65535, devappserver2.PortParser()('65535'))

  def test_not_an_int(self):
    self.assertRaises(argparse.ArgumentTypeError, devappserver2.PortParser(),
                      'a port')

if __name__ == '__main__':
  unittest.main()