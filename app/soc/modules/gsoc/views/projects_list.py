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

"""Module containing the views for listing all the projects accepted
into a GSoC program, excluding those which have been withdrawn
or failed one of the evaluations.
"""

from soc.logic.exceptions import AccessViolation
from soc.views.base_templates import ProgramSelect
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.helper.url_patterns import url


class ProjectList(Template):
  """Template for listing the student projects accepted in the program."""

  def __init__(self, data, query, idx=0):
    """Initializes a new object.

    Args:
      data: RequestData object associated with the request
      query: query to be used to retrieve Project entities
      idx: index of the list
    """
    self.data = data
    self.query = query
    self.idx = idx

    r = data.redirect
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        (lambda ent, *args: "%s/%s" % (
            ent.parent_key().name(), ent.key().id())), hidden=True)
    list_config.addPlainTextColumn('student', 'Student',
        lambda entity, *args: entity.parent().name())
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization',
        lambda entity, *args: entity.org.name)
    list_config.addSimpleColumn('status', 'Status', hidden=True)
    list_config.addPlainTextColumn('mentors', 'Mentors',
        lambda entity, *args: args[0][entity.key()], hidden=True)
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('student')
    list_config.setRowAction(lambda e, *args:
        r.project(id=e.key().id_or_name(), student=e.parent().link_id).
        urlOf('gsoc_project_details'))
    self._list_config = list_config

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx,
        description='List of projects accepted into %s' % (
            self.data.program.name))

    return {
        'lists': [list],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == self.idx:
      starter = lists.keyStarter

      list_model_prefetcher = lists.listModelPrefetcher(
            GSoCProject, ['org'], ['mentors'], parent=True)

      def prefetcher(entities):
        """Prefetches the specified fields.

        For motivation of the code flow and more comments, please see the
        comments in lists.listModelPrefetcher method.
        """
        prefetched_list, _ = list_model_prefetcher(entities)
        mentor_names = {}
        for e in entities:
          mentor_names[e.key()] = ', '.join(
              [prefetched_list[0][m_key].name() for m_key in e.mentors])

        return [mentor_names], {}

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, self.query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return "v2/modules/gsoc/projects_list/_project_list.html"


class ListProjects(GSoCRequestHandler):
  """View methods for listing all the projects accepted into a program."""

  def templatePath(self):
    return 'v2/modules/gsoc/projects_list/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""

    return [
        url(r'projects/list/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_accepted_projects')
    ]

  def checkAccess(self):
    """Access checks for the view."""
    self.check.acceptedStudentsAnnounced()

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    list_query = project_logic.getAcceptedProjectsQuery(
        program=data.program)
    list_content = ProjectList(data, list_query).getListData()

    if list_content:
      return list_content.content()
    else:
      raise AccessViolation('You do not have access to this data')

  def context(self, data, check, mutator):
    """Handler for GSoC Accepted Projects List page HTTP get request."""
    program = data.program
    list_query = project_logic.getAcceptedProjectsQuery(program=data.program)

    return {
        'page_name': '%s - Accepted Projects' % program.short_name,
        'program_name': program.name,
        'project_list': ProjectList(data, list_query),
        'program_select': ProgramSelect(data, 'gsoc_accepted_projects'),
    }
