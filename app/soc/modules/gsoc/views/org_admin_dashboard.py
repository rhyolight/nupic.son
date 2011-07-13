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

"""Module for the GSoC organization page listing all evaluations.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation
from soc.views.helper import lists
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import grading_project_survey as gps_logic
from soc.modules.gsoc.logic import grading_project_survey_record as gpsr_logic
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views import dashboard
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


DEF_NOT_ADMIN_MSG = ugettext(
    'You must be an organization administrator for at least one '
    'organization in the program to access this page.')


class MentorEvaluationComponent(dashboard.Component):
  """Component for listing mentor evaluations for organizations.
  """

  def __init__(self, request, data):
    self.request = request
    self.data = data

    evaluation = 'midterm'
    mm_eval = gps_logic.getGradingProjectSurveyForProgram(
        self.data.program, evaluation)

    r = data.redirect
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn('key', 'Key', (lambda ent, *args: "%s/%s" % (
        ent.parent().key().name(), ent.key().id())), hidden=True)
    list_config.addColumn('student', 'Student',
                          lambda entity, *args: entity.parent().name())
    list_config.addSimpleColumn('title', 'Project Title')
    list_config.addColumn('org', 'Organization',
                          lambda entity, *args: entity.org.name)
    list_config.addColumn(
        'mentors', 'Mentors', lambda entity, mentors, *args: ', '.join(
            [mentors.get(m).name() for m in entity.mentors]))
    list_config.addColumn(
        'status', 'Status', lambda entity, *args: dashboard.colorize(
            gpsr_logic.evalRecordExistsForStudent(
            mm_eval, entity), "Submitted", "Not submitted"))
    list_config.setDefaultSort('student')
    list_config.setRowAction(lambda entity, *args, **kwargs:
        r.survey_record(
            'midterm', entity.key().id_or_name(),
            entity.parent().link_id).urlOf(
                'gsoc_take_mentor_evaluation'))
    self._list_config = list_config

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0)

    return {
        'lists': [list],
        'title': 'Mentor Evaluations - Midterm',
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 0:
      list_query = project_logic.getProjectsQueryForOrgs(
          orgs=self.data.org_admin_for)

      starter = lists.keyStarter
      prefetcher = lists.listModelPrefetcher(
          GSoCProject, ['org'], ['mentors'], parent=True)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.request, self._list_config, list_query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return'v2/modules/gsoc/dashboard/list_component.html'


class Dashboard(dashboard.Dashboard):
  """View for the list of all the organization related components.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the org evaluations.
    """
    return [
        url(r'dashboard/org/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_org_dashboard')]

  def checkAccess(self):
    """Denies access if the user is not an org admin.
    """
    self.check.isProfileActive()

    if self.data.is_org_admin:
      return

    raise AccessViolation(DEF_NOT_ADMIN_MSG)

  def _getActiveComponents(self):
    """Returns the components that are active on the page.
    """
    components = [MentorEvaluationComponent(self.request, self.data)]
    return components
