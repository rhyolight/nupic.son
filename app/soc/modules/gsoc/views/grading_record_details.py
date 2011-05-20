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

"""Module for displaying GradingSurveyGroups and records.
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from google.appengine.ext import db

from soc.views.template import Template

from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import lists
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


class GradingRecordsOverview(RequestHandler):
  """View to display all GradingRecords for a single group.
  """

  def djangoURLPatterns(self):
    return [
        url(r'grading_records/overview/%s$' % url_patterns.ID,
         self, name='gsoc_grading_record_overview'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/grading_record/overview.html'

  def context(self):
    return {
        'page_name': 'Evaluation Group Overview',
        'record_list': GradingRecordsList(self.request, self.data)
        }

  def jsonContext(self):
    """Handler for JSON requests.
    """
    idx = lists.getListIndex(self.request)
    if idx == 0:
      return GradingRecordsList(self.request, self.data).listContent().content()
    else:
      super(GradingRecordsOverview, self).jsonContext()


class GradingRecordsList(Template):
  """Lists all GradingRecords for a single GradingSurveyGroup.
  """

  def __init__(self, request, data):
    """Initializes the template.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    self.request = request
    self.data = data
    # TODO(ljvderijk) Move to a mutator and use 404 if not exists
    self.survey_group = GSoCGradingSurveyGroup.get_by_id(
        int(self.data.kwargs['id']))

    list_config = lists.ListConfiguration()

    func = lambda rec, *args, **kwargs: \
        'Present' if rec.student_record else 'Missing'
    list_config.addColumn('student_record', 'Survey by Student', func)

    def mentorRecordInfo(rec, *args, **kwargs):
      """Displays information about a GradingRecord's mentor_record property.
      """
      if not rec.mentor_record:
        return 'Missing'

      if rec.mentor_record.grade:
        return 'Passing Grade'
      else:
        return 'Fail Grade'

    list_config.addColumn('mentor_record', 'Survey by Mentor', mentorRecordInfo)

    list_config.addSimpleColumn('grade_decision', 'Decision')
    r = data.redirect
    list_config.setRowAction(lambda e, *args, **kwargs: 
        r.key(str(e.key())).urlOf('gsoc_grading_record_detail'))

    self._list_config = list_config

  def context(self):
    """Returns the context for the current template.
    """
    list = lists.ListConfigurationResponse(self.data, self._list_config, idx=0)
    return {'lists': [list]}

  def listContent(self):
    """Returns the ListContentResponse object that is constructed from the data.
    """
    q = GSoCGradingRecord.all()
    q.filter('grading_survey_group', self.survey_group)

    starter = lists.keyStarter
    prefetcher = lists.modelPrefetcher(
        GSoCGradingRecord, ['mentor_record', 'student_record'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q,
        starter, prefetcher=prefetcher)
    return response_builder.build()

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'v2/soc/list/lists.html'


class GradingRecordDetails(RequestHandler):
  """View to display GradingRecord details.
  """

  def djangoURLPatterns(self):
    return [
        url(r'grading_records/detail/%s$' % url_patterns.KEY,
         self, name='gsoc_grading_record_detail'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def context(self):
    # TODO: Write mutator for this which takes a Model so it can throw a KindError
    record = GSoCGradingRecord.get(db.Key(self.kwargs['key']))

    return {
        'page_name': 'Grading Record Details',
        'record': record,
        }

  def templatePath(self):
    return 'v2/modules/gsoc/grading_record/details.html'
