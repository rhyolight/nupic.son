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

"""Module containing views for the Summer Of Code organization homepage."""

from google.appengine.ext import db

from django.utils import translation

from melange.request import access
from melange.request import links
from melange.utils import lists as melange_lists

from soc.views import template
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.views.helper import urls


ORG_HOME_PAGE_TITLE = translation.ugettext('%s')

PROJECT_LIST_DESCRIPTION = translation.ugettext(
    'List of projects accepted into %s.')

CONTACT_TEMPLATE_PATH = 'modules/gsoc/_connect_with_us.html'

class Contact(template.Template):
  """Contact template."""

  def __init__(self, template_path, data):
    """Initializes a new instance of Contact template.

    Args:
      template_path: Path to the template that should be rendered.
      data: request_data.RequestData for the current request.
    """
    super(Contact, self).__init__(data)
    self.template_path = template_path

  def context(self):
    """See template.Template.context for specification."""
    return {
        'facebook_link': self.data.url_ndb_org.contact.facebook,
        'twitter_link': self.data.url_ndb_org.contact.twitter,
        'blogger_link': self.data.url_ndb_org.contact.blog,
        'pub_mailing_list_link': self.data.url_ndb_org.contact.mailing_list,
        'irc_channel_link': self.data.url_ndb_org.contact.irc_channel,
        'google_plus_link': self.data.url_ndb_org.contact.google_plus
    }


class _ProjectDetailsRowRedirect(melange_lists.RedirectCustomRow):
  """Class which provides redirects for rows of public organization list."""

  def __init__(self, data):
    """Initializes a new instance of the row redirect.

    See lists.RedirectCustomRow.__init__ for specification.

    Args:
      data: request_data.RequestData for the current request.
    """
    super(_ProjectDetailsRowRedirect, self).__init__()
    self.data = data

  def getLink(self, item):
    """See lists.RedirectCustomRow.getLink for specification."""
    project_key = db.Key(item['columns']['key'])
    return links.LINKER.userId(
        project_key.parent(), project_key.id(), 'gsoc_project_details')


# TODO(daniel): replace this class with new style list
class ProjectList(template.Template):
  """List of projects."""

  def __init__(self, data, description):
    """See template.Template.__init__ for specification."""
    super(ProjectList, self).__init__(data)
    self._list_config = lists.ListConfiguration()
    self._list_config.addPlainTextColumn('student', 'Student',
        lambda entity, *args: entity.parent().name())
    self._list_config.addSimpleColumn('title', 'Title')
    self._list_config.addPlainTextColumn(
        'mentors', 'Mentor',
        lambda entity, m, *args: ", ".join(
            [m[i].name() for i in entity.mentors]))
    self._list_config.setDefaultSort('student')
    self._description = description

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return 'modules/gsoc/admin/_accepted_orgs_list.html'

  def context(self):
    """See template.Template.context for specification."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, self._description)
    return {'lists': [list_configuration_response]}


class OrgHomePage(base.GSoCRequestHandler):
  """View to display organization homepage."""

  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_home/base.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    # TODO(daniel): should we keep all these legacy patterns here?
    # TODO(daniel): remove '2' when old view is not ready
    return [
        soc_url_patterns.url(r'org2/%s$' % url_patterns.ORG, self,
            name=urls.UrlNames.ORG_HOME),
        soc_url_patterns.url(r'org2/show/%s$' % url_patterns.ORG, self),
        soc_url_patterns.url(r'org2/home/%s$' % url_patterns.ORG, self),
    ]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    context = {
        'page_name': ORG_HOME_PAGE_TITLE % data.url_ndb_org.name,
        'organization': data.url_ndb_org,
        'contact': Contact(CONTACT_TEMPLATE_PATH, data),
    }

    if data.timeline.studentsAnnounced():
      context['students_announced'] = True
      context['project_list'] = ProjectList(
          data, PROJECT_LIST_DESCRIPTION % data.url_ndb_org.name)

    return context

  def jsonContext(self, data, check, mutator):
    """See base.RequestHandler.jsonContext for specification."""
    query = project_logic.getAcceptedProjectsQuery(
        program=data.program, org=data.url_ndb_org.key.to_old_key())

    response = melange_lists.JqgridResponse(
        melange_lists.GSOC_PROJECTS_LIST_ID,
        row=_ProjectDetailsRowRedirect(data))
    return response.getData(query)
