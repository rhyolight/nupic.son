# Copyright 2011 the Melange authors.
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

"""Tests for app.soc.logic.site."""

import os
import unittest

from soc.logic import site
from soc.models import site as site_model
from soc.views.helper import request_data


class SiteFunctionsTest(unittest.TestCase):
  """Tests for basic site settings functions."""

  def setUp(self):
    self.default_host = os.environ.get('HTTP_HOST', None)
    self.default_application_id = os.environ.get('APPLICATION_ID', None)
    self.default_current_version_id = os.environ.get('CURRENT_VERSION_ID', None)

  def testGetHostName(self):
    """Tests that a correct host name is returned."""
    test_data = request_data.RequestData(None, None, None)
    test_data._site = site_model.Site(link_id='test', hostname='test_host')

    try:
      expected_host = os.environ['HTTP_HOST'] = 'some.testing.host.tld'
      self.assertEqual(site.getHostname(), expected_host)
    finally:
      if self.default_host is None:
        del os.environ['HTTP_HOST']
      else:
        os.environ['HTTP_HOST'] = self.default_host

    # test a data object
    expected_host = 'test_host'
    self.assertEqual(site.getHostname(data=test_data), expected_host)

    test_data.site.hostname = ''
    try:
      expected_host = os.environ['HTTP_HOST'] = 'some.testing.host.tld'
      self.assertEqual(site.getHostname(data=test_data), expected_host)
    finally:
      if self.default_host is None:
        del os.environ['HTTP_HOST']
      else:
        os.environ['HTTP_HOST'] = self.default_host

  def testIsSecondaryHostName(self):
    """Tests if a request is from a secondary hostname."""
    test_data = request_data.RequestData(None, None, None)
    test_data._site = site_model.Site(link_id='test', hostname='test_host')

    try:
      os.environ['HTTP_HOST'] = 'some.testing.host.tld'
      self.assertFalse(site.isSecondaryHostname())

      self.assertFalse(site.isSecondaryHostname(data=test_data))

      test_data.site.hostname = "testing"
      self.assertTrue(site.isSecondaryHostname(data=test_data))
    finally:
      if self.default_host is None:
        del os.environ['HTTP_HOST']
      else:
        os.environ['HTTP_HOST'] = self.default_host
