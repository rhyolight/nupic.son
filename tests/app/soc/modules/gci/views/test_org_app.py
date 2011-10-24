#!/usr/bin/env python2.5
#
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


"""Tests for organization applications.
"""

__authors__ = [
  '"Orcun Avsar" <orc.avs@gmail.com>',
  ]


from soc.models.org_app_survey import OrgAppSurvey

from tests.test_utils import GCIDjangoTestCase


class GCIOrgAppEditPageTest(GCIDjangoTestCase):
  """Tests for organization applications edit page.
  """

  def setUp(self):
    self.init()
    self.url = '/gci/org/application/edit/%s' % self.gci.key().name()

  def assertTemplatesUsed(self, response):
    """Asserts all the templates for edit page were used.
    """

    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/org_app/edit.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/_form.html')

  def testAccessCheck(self):
    """Asserts only the host can access the page.
    """

    response = self.client.get(self.url)
    self.assertResponseForbidden(response)

    self.data.createHost()
    response = self.client.get(self.url)
    self.assertResponseOK(response)

  def testPage(self):
    """Tests organization applications edit page.
    """

    self.data.createHost()
    response = self.client.get(self.url)
    self.assertTemplatesUsed(response)

    postdata = {
        'title': 'Test Title',
        'short_name': 'Test Short Name',
        'content': 'Test Content',
        'survey_start': '2011-10-13 00:00:00',
        'survey_finish': '2011-10-13 00:00:00',
        'schema': 'Test Scheme',
    }
    response = self.post(self.url, postdata)
    self.assertResponseRedirect(response, '%s?validated' % self.url)

    query = OrgAppSurvey.all().filter('program = ', self.gci)
    self.assertEqual(query.count(), 1,
                     ('There must be one and only one OrgAppSurvey '
                      'instance for the program.'))

    survey = query.get()
    self.assertEqual(survey.title, 'Test Title')
    self.assertEqual(survey.modified_by.key(), self.data.user.key())
