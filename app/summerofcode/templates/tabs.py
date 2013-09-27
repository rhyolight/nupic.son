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

from melange.templates import tabs

from soc.logic import links
from soc.modules.gsoc.views.helper import url_names


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
  url = links.LINKER.program(data.program, url_names.GSOC_PROFILE_SHOW)
  tabs_list.append(tabs.Tab(VIEW_PROFILE_TAB_ID, VIEW_PROFILE_NAME, url))

  # add Edit Profile tab
  url = links.LINKER.program(data.program, url_names.GSOC_PROFILE_EDIT)
  tabs_list.append(tabs.Tab(EDIT_PROFILE_TAB_ID, EDIT_PROFILE_NAME, url))

  if selected_tab_id and selected_tab_id not in [
      tab.tab_id for tab in tabs_list]:
    raise ValueError('Selected Tab ID %s does not belong to any tabs.' %
        selected_tab_id)

  return tabs.Tabs(
      data, TEMPLATE_PATH, tabs_list, selected_tab_id=selected_tab_id)
