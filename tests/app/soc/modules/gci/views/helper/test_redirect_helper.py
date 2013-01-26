# Copyright 2012 the Melange authors.
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

"""This module unit tests for RedirectHelper class."""

from soc.views.helper.access_checker import unset
from soc.views.helper.response import Response

from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names

from tests.test_utils import GCITestCase
from tests.test_utils import MockRequest


class RedirectHelperTest(GCITestCase):
  """Unit tests for RedirectHelper class."""

  def setUp(self):
    self.init()
    request = MockRequest(path="/")

    self.handler = GCIRequestHandler()
    self.handler.response = Response()
    data, _, _, _ = self.handler.init(request, (), {})

    self.redirect = data.redirect

  def testProgram(self):
    expected = {
        'sponsor': self.sponsor.link_id,
        'program': self.gci.link_id,
        }

    self.handler.kwargs = {}
    self.redirect.program(program=self.gci)
    self.assertEqual(self.redirect.kwargs, expected)

    self.handler.kwargs = {}
    self.redirect.program()
    self.assertEqual(self.redirect.kwargs, expected)

    self.redirect._data._program = unset
    self._assertAssertionError(self.redirect.program)

  def testUserOrg(self):
    expected = {
        'user': 'test_user',
        'organization': self.org.link_id,
        'sponsor': self.sponsor.link_id,
        'program': self.gci.link_id
        }

    self.handler.kwargs = {}
    self.redirect.userOrg(user='test_user', organization=self.org)
    self.assertEqual(self.redirect.kwargs, expected)

    self.handler.kwargs = {}
    self.redirect._data.kwargs['user'] = 'test_user'
    self.redirect.userOrg(organization=self.org)
    self.assertEqual(self.redirect.kwargs, expected)

    self.handler.kwargs = {}
    del self.redirect._data.kwargs['user']
    self.redirect._data.organization = self.org
    self.redirect.userOrg(user='test_user')
    self.assertEqual(self.redirect.kwargs, expected)

    self.handler.kwargs = {}
    self.redirect._data.organization = None
    self._assertAssertionError(self.redirect.userOrg)

  def _assertAssertionError(self, callable, *args, **kwargs):
    with self.assertRaises(AssertionError):
      callable(*args, **kwargs)
