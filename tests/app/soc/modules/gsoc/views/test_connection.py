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

"""Tests for the connection view.
"""

from google.appengine.ext import db

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase
from tests.test_utils import MailTestCase

class ConnectionTest(GSoCDjangoTestCase, MailTestCase):
  """ Tests connection page.
  """

  def setUp(self):
    super(ConnectionTest, self).setUp()
    self.init()

  def assertConnectionTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/connection/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def testOrgAdminConnection(self):
    pass

  def testUserAcceptRoles(self):
    pass

  def testUserConnection(self):
    pass

  def testViewConnection(self):
    pass