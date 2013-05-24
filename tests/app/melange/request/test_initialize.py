# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for melange.request.initialize."""

import unittest

from django import http

from melange.request import initialize


class MelangeInitializerTest(unittest.TestCase):
  """Tests the MelangeInitializer implementation of Initializer."""

  # TODO(nathaniel): More than just a smoke test?
  def testInitializer(self):
    """Tests that per-request objects are created."""
    request = http.HttpRequest()

    data, check, mutator = initialize.MELANGE_INITIALIZER.initialize(
        request, [], {})
    self.assertEqual(request, data.request)
    self.assertEqual(data, check.data)
    self.assertEqual(data, mutator.data)
