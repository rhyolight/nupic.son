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

"""Unit tests for slot transfer admin view."""

from tests import profile_utils
from tests import test_utils


class SlotsTransferAdminPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for SlotsTransferAdminPage class."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/slots/transfer/%s' % self.gsoc.key().name()

  def testLoneUserAccessForbidden(self):
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    self.data.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    self.data.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)
