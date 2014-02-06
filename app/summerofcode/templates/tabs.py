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

"""Module containing templates with Summer Of Code tabs."""

from django.utils import translation

from melange.models import organization as org_model
from melange.request import links
from melange.templates import tabs

from summerofcode.views.helper import urls


TEMPLATE_PATH = 'summerofcode/_tabs.html'

EDIT_PROFILE_TAB_ID = 'edit_profile_tab'
VIEW_PROFILE_TAB_ID = 'view_profile_tab'

EDIT_PROFILE_NAME = translation.ugettext('Edit Profile')
VIEW_PROFILE_NAME = translation.ugettext('View Profile')

def profileTabs(data, selected_tab_id=None):
  """Returns tabs that join together profile related items.

  Args:
    data: request_data.RequestData object for the current request.
    selected_tab_id: identifier of the tab that should be initially selected.

  Returns:
    Tabs object with profile related tabs.
  """
  tabs_list = []

  # add View Profile tab
  url = links.LINKER.program(data.program, urls.UrlNames.PROFILE_SHOW)
  tabs_list.append(tabs.Tab(VIEW_PROFILE_TAB_ID, VIEW_PROFILE_NAME, url))

  # add Edit Profile tab
  url = links.LINKER.program(data.program, urls.UrlNames.PROFILE_EDIT)
  tabs_list.append(tabs.Tab(EDIT_PROFILE_TAB_ID, EDIT_PROFILE_NAME, url))

  if selected_tab_id and selected_tab_id not in [
      tab.tab_id for tab in tabs_list]:
    raise ValueError('Selected Tab ID %s does not belong to any tabs.' %
        selected_tab_id)

  return tabs.Tabs(
      data, TEMPLATE_PATH, tabs_list, selected_tab_id=selected_tab_id)


ORG_PROFILE_TAB_ID = 'org_profile_tab'
ORG_APP_RESPONSE_TAB_ID = 'app_response_tab'
ORG_PREFERENCES_TAB_ID = 'org_preferences_tab'

ORG_PROFILE_NAME = translation.ugettext('Profile')
ORG_APP_RESPONSE_NAME = translation.ugettext('Questionnaire')
ORG_PREFERENCES_NAME = translation.ugettext('Preferences')

def orgTabs(data, selected_tab_id=None):
  """Returns tabs that join together organization related items.

  Args:
    data: request_data.RequestData object for the current request.
    selected_tab_id: identifier of the tab that should be initially selected.

  Returns:
    Tabs object with organization related tabs.
  """
  tabs_list = []

  # add Organization Profile tab
  url = links.LINKER.organization(
      data.url_ndb_org.key, urls.UrlNames.ORG_PROFILE_EDIT)
  tabs_list.append(tabs.Tab(ORG_PROFILE_TAB_ID, ORG_PROFILE_NAME, url))

  # add Application Response tab
  # A link to edit and resubmit the application should be used during
  # the organization application period. A link to see the survey response
  # in read-only mode should be used afterwards.
  if data.timeline.orgSignup():
    url = links.LINKER.organization(
        data.url_ndb_org.key, urls.UrlNames.ORG_APPLICATION_SUBMIT)
  else:
    url = links.LINKER.organization(
        data.url_ndb_org.key, urls.UrlNames.ORG_SURVEY_RESPONSE_SHOW)
  tabs_list.append(
      tabs.Tab(ORG_APP_RESPONSE_TAB_ID, ORG_APP_RESPONSE_NAME, url))

  # add Organization Preferences tab if the organization is accepted
  if data.url_ndb_org.status == org_model.Status.ACCEPTED:
    url = links.LINKER.organization(
        data.url_ndb_org.key, urls.UrlNames.ORG_PREFERENCES_EDIT)
    tabs_list.append(
        tabs.Tab(ORG_PREFERENCES_TAB_ID, ORG_PREFERENCES_NAME, url))

  return tabs.Tabs(
      data, TEMPLATE_PATH, tabs_list, selected_tab_id=selected_tab_id)
