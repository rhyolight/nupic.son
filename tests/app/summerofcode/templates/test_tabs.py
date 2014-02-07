# Copyright 2014 the Melange authors.
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

"""Tests for tabs module."""

import unittest

from melange.models import organization as org_model

from soc.views.helper import request_data

from summerofcode.templates import tabs as soc_tabs

from tests import org_utils
from tests import program_utils
from tests import timeline_utils


class OrgTabsTest(unittest.TestCase):
  """Unit tests for orgTabs function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    self.org_app = program_utils.seedApplicationSurvey(program.key())
    self.org = org_utils.seedOrganization(program.key())

    self.kwargs = {
        'sponsor': org_model.getSponsorId(self.org.key),
        'program': org_model.getProgramId(self.org.key),
        'organization': org_model.getOrgId(self.org.key)
        }

  def testPreferencesTab(self):
    """Tests that Preferences tab is present for accepted organizations only."""
    # check that tab is not present for organizations that are not accepted
    statuses = [
        org_model.Status.APPLYING, org_model.Status.PRE_ACCEPTED,
        org_model.Status.PRE_REJECTED, org_model.Status.REJECTED]
    for status in statuses:
      self.org.status = status
      self.org.put()
      data = request_data.RequestData(None, None, self.kwargs)
      tabs = soc_tabs.orgTabs(data)
      self.assertNotIn(
          soc_tabs.ORG_PREFERENCES_TAB_ID, [tab.tab_id for tab in tabs.tabs])

    # check that tab is present for an organization that is accepted
    self.org.status = org_model.Status.ACCEPTED
    self.org.put()
    data = request_data.RequestData(None, None, self.kwargs)
    tabs = soc_tabs.orgTabs(data)
    self.assertIn(
        soc_tabs.ORG_PREFERENCES_TAB_ID, [tab.tab_id for tab in tabs.tabs])

  def testSurveyResponseTab(self):
    """Tests that survey response tab has the right URL."""
    # organization application is now
    self.org_app.survey_start = timeline_utils.past()
    self.org_app.survey_end = timeline_utils.future()
    self.org_app.put()

    data = request_data.RequestData(None, None, self.kwargs)
    tabs = soc_tabs.orgTabs(data)

    survey_response_tab = [
        tab for tab in tabs.tabs
        if tab.tab_id == soc_tabs.ORG_APP_RESPONSE_TAB_ID][0]
    self.assertEqual(
        '/gsoc/org/application/submit/%s' % self.org.key.id(),
        survey_response_tab.url)

    # organization application is complete
    self.org_app.survey_start = timeline_utils.past(delta=100)
    self.org_app.survey_end = timeline_utils.past(delta=50)
    self.org_app.put()

    data = request_data.RequestData(None, None, self.kwargs)
    tabs = soc_tabs.orgTabs(data)

    survey_response_tab = [
        tab for tab in tabs.tabs
        if tab.tab_id == soc_tabs.ORG_APP_RESPONSE_TAB_ID][0]
    self.assertEqual(
        '/gsoc/org/survey_response/show/%s' % self.org.key.id(),
        survey_response_tab.url)
