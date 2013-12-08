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

"""Module containing the view for GSoC participants list page."""

from google.appengine.ext import ndb

from melange.request import access
from melange.request import exception
from soc.views.helper import addresses
from soc.views.helper import url_patterns
from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.helper.url_patterns import url


class MentorsList(Template):
  """Template for list of mentors for admins."""

  def __init__(self, data):
    self.data = data

    def getMentorFor(entity, *args):
      """Helper function to get value of mentor_for column."""
      org_keys = map(ndb.Key.from_old_key, entity.mentor_for)
      return ', '.join(org.name for org in ndb.get_multi(org_keys) if org)

    def getOrgAdminFor(entity, *args):
      """Helper function to get value of org_admin_for column."""
      org_keys = map(ndb.Key.from_old_key, entity.org_admin_for)
      return ', '.join(org.name for org in ndb.get_multi(org_keys) if org)


    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn('name', 'Name',
                          lambda e, *args: e.name().strip())
    list_config.addSimpleColumn('link_id', 'Username')
    list_config.addPlainTextColumn('is_org_admin', 'Org Admin',
        lambda e, *args: 'Yes' if e.is_org_admin else 'No', hidden=True)
    list_config.addSimpleColumn('email', 'Email')
    list_config.addPlainTextColumn(
        'org_admin_for', 'Org Admin For', getOrgAdminFor)
    list_config.addPlainTextColumn('mentor_for', 'Mentor For', getMentorFor)

    addresses.addAddressColumns(list_config)

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')

    self._list_config = list_config

  def context(self):
    description = \
        'List of organization admins and mentors participating in %s' % (
            self.data.program.name)

    return {
        'lists': [lists.ListConfigurationResponse(
            self.data, self._list_config, 0, description)],
    }

  def getListData(self):
    if lists.getListIndex(self.data.request) != 0:
      return None

    q = GSoCProfile.all()
    q.filter('program', self.data.program)
    q.filter('is_mentor', True)

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models
    # ('mentor_for', 'org_admin_for')
    prefetcher = lists.ListFieldPrefetcher(GSoCProfile, [])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=prefetcher)

    return response_builder.build()

  def templatePath(self):
    return 'modules/gsoc/participants/_mentors_list.html'


class MentorsListAdminPage(GSoCRequestHandler):
  """View for the organization admin and mentors page for admin."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gsoc/participants/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'admin/list/mentors/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_list_mentors'),
    ]

  def jsonContext(self, data, check, mutator):
    list_content = MentorsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "List of organization admins and mentors for %s" % (
            data.program.name),
        'mentors_list': MentorsList(data),
    }
