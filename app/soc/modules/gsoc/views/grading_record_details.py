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

"""Module for displaying GradingSurveyGroups and records."""

import collections

from google.appengine.api import taskqueue
from google.appengine.ext import db

from django import http

from melange.request import access
from melange.request import exception

from soc.views import forms
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.modules.gsoc.logic import grading_record
from soc.modules.gsoc.logic import survey
from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns as gsoc_url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url

class GradingGroupCreate(base.GSoCRequestHandler):
  """View to display GradingRecord details."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'grading_records/group/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_grading_group'),
    ]

  def context(self, data, check, mutator):
    return {
        'page_name': 'Grading Group Create Page',
        'err': bool(data.GET.get('err', False))
        }

  def post(self, data, check, mutator):
    """Handles the POST request when creating a Grading Group"""
    student_survey = None
    grading_survey = None
    survey_type = None

    if 'midterm' in data.POST:
      student_survey = survey.getMidtermProjectSurveyForProgram(data.program)
      grading_survey = survey.getMidtermGradingProjectSurveyForProgram(
          data.program)
      survey_type = 'Midterm'
    elif 'final' in data.POST:
      student_survey = survey.getFinalProjectSurveyForProgram(data.program)
      grading_survey = survey.getFinalGradingProjectSurveyForProgram(
          data.program)
      survey_type = 'Final'
    else:
      raise exception.BadRequest('No valid evaluation type present')

    if not student_survey or not grading_survey:
      data.redirect.program()
      return data.redirect.to('gsoc_grading_group', extra=['err=1'])

    q = GSoCGradingSurveyGroup.all()
    q.filter('student_survey', student_survey)
    q.filter('grading_survey', grading_survey)

    existing_group = q.get()

    if existing_group:
      data.redirect.id(existing_group.key().id())
    else:
      props = {
          'name': '%s - %s Evaluation' %(data.program.name, survey_type),
          'program': data.program,
          'grading_survey': grading_survey,
          'student_survey': student_survey,
      }
      new_group = GSoCGradingSurveyGroup(**props)
      new_group.put()
      data.redirect.id(new_group.key().id())

    return data.redirect.to('gsoc_grading_record_overview')

  def templatePath(self):
    return 'modules/gsoc/grading_record/create_group.html'

class GradingRecordsOverview(base.GSoCRequestHandler):
  """View to display all GradingRecords for a single group."""

  def djangoURLPatterns(self):
    return [
        url(r'grading_records/overview/%s$' % url_patterns.ID,
         self, name='gsoc_grading_record_overview'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.surveyGroupFromKwargs()
    check.isHost()

  def templatePath(self):
    return 'modules/gsoc/grading_record/overview.html'

  def context(self, data, check, mutator):
    return {
        'page_name': 'Evaluation Group Overview',
        'record_list': GradingRecordsList(data),
        }

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    idx = lists.getListIndex(data.request)
    if idx == 0:
      return GradingRecordsList(data).listContent().content()
    else:
      # TODO(nathaniel): Should this be a return statement?
      super(GradingRecordsOverview, self).jsonContext(data, check, mutator)

  def post(self, data, check, mutator):
    """Handles the POST request from the list and starts the appropriate task.
    """
    post_dict = data.POST

    if post_dict['button_id'] == 'update_records':
      task_params = {'group_key': data.survey_group.key().id_or_name()}
      task_url = '/tasks/gsoc/grading_record/update_records'

      task = taskqueue.Task(params=task_params, url=task_url)
      task.add()
    elif post_dict['button_id'] == 'update_projects':
      task_params = {'group_key': data.survey_group.key().id_or_name(),
                     'send_mail': 'true'}
      task_url = '/tasks/gsoc/grading_record/update_projects'

      task = taskqueue.Task(params=task_params, url=task_url)
      task.add()

    return http.HttpResponse()


class GradingRecordsList(Template):
  """Lists all GradingRecords for a single GradingSurveyGroup.
  """

  class ListPrefetcher(lists.Prefetcher):
    """Prefetcher used by GradingRecordsList.

    See lists.Prefetcher for specification.
    """

    def prefetch(self, entities):
      """Prefetches GSoCProfile entities belonging to a student and a mentor
      of the projects corresponding to the items in the specified list of
      GSoCGradingRecord entities.

      See lists.Prefetcher.prefetch for specification.

      Args:
        entities: the specified list of GSoCGradingRecord instances

      Returns:
        prefetched GSoCProfile entities in a structure whose format is
        described in lists.Prefetcher.prefetch
      """
      mentor_records_map = collections.defaultdict(list)
      student_profiles = {}

      for entity in entities:
        project = entity.parent()
        mentor_key = project.mentors[0]
        record_key = entity.key()
        if record_key:
          mentor_records_map[mentor_key].append(record_key)
          student_profiles[record_key] = project.parent()

      entities = db.get(mentor_records_map.keys())
      mentors = {}
      for mentor in entities:
        if mentor:
          for record_key in mentor_records_map[mentor.key()]:
            mentors[record_key] = mentor

      return ([mentors, student_profiles], {})

  def __init__(self, data):
    """Initializes the template.

    Args:
      data: The RequestData object
    """
    self.data = data

    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn(
        'key', 'Key',
        (lambda ent, *args: "%s/%d/%d" % (
            ent.parent_key().parent().name(),
            ent.parent_key().id(),
            ent.key().id())),
        hidden=True)

    title_func = lambda rec, *args: rec.parent().title
    list_config.addPlainTextColumn(
        'project_title', 'Project Title', title_func)
    org_func = lambda rec, *args: rec.parent().org.name
    list_config.addPlainTextColumn('org_name', 'Organization', org_func)

    stud_rec_func = lambda rec, *args: \
        'Present' if rec.student_record else 'Missing'
    list_config.addPlainTextColumn(
        'student_record', 'Evaluation by Student', stud_rec_func)

    stud_id_func = lambda rec, *args: rec.parent().parent().link_id
    list_config.addPlainTextColumn(
        'student_id', 'Student username', stud_id_func, hidden=True)

    stud_email_func = lambda rec, *args: args[1][rec.key()].email
    list_config.addPlainTextColumn('student_email', 'Student Email Address',
        stud_email_func, hidden=True)

    stud_fn_func = lambda rec, *args: args[1][rec.key()].given_name
    list_config.addPlainTextColumn('student_fn', 'Student First Name',
        stud_fn_func, hidden=True)

    stud_ln_func = lambda rec, *args: args[1][rec.key()].surname
    list_config.addPlainTextColumn('student_ln', 'Student Last Name',
        stud_ln_func, hidden=True)

    mentor_email_func = lambda rec, *args: args[0][rec.key()].email

    list_config.addPlainTextColumn('mentor_email', 'Mentor Email Address',
        mentor_email_func, hidden=True)

    mentor_fn_func = lambda rec, *args: args[0][rec.key()].given_name
    list_config.addPlainTextColumn('mentor_fn', 'Mentor First Name',
        mentor_fn_func, hidden=True)

    mentor_ln_func = lambda rec, *args: args[0][rec.key()].surname
    list_config.addPlainTextColumn('mentor_ln', 'Mentor Last Name',
        mentor_ln_func, hidden=True)


    list_config.addPostButton(
        'update_records', 'Update Records', '', [0,'all'], [])
    list_config.addPostButton(
        'update_projects', 'Update Projects', '', [0,'all'], [])

    def mentorRecordInfo(rec, *args):
      """Displays information about a GradingRecord's mentor_record property.
      """
      if not rec.mentor_record:
        return 'Missing'

      if rec.mentor_record.grade:
        return 'Passing Grade'
      else:
        return 'Fail Grade'

    list_config.addPlainTextColumn(
        'mentor_record', 'Evaluation by Mentor', mentorRecordInfo)

    list_config.addSimpleColumn('grade_decision', 'Decision')
    list_config.setRowAction(lambda e, *args:
        data.redirect.grading_record(e).urlOf('gsoc_grading_record_detail'))

    self._list_config = list_config

  def context(self):
    """Returns the context for the current template."""
    return {'lists': [lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0)]}

  def listContent(self):
    """Returns the ListContentResponse object that is constructed from the data.
    """
    q = GSoCGradingRecord.all()
    q.filter('grading_survey_group', self.data.survey_group)

    starter = lists.keyStarter
    prefetcher = GradingRecordsList.ListPrefetcher()

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q,
        starter, prefetcher=prefetcher)
    return response_builder.build()

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'soc/list/lists.html'


class GradingRecordForm(gsoc_forms.GSoCModelForm):
  """Django form to edit a GradingRecord manually.
  """

  class Meta:
    model = GSoCGradingRecord
    css_prefix = 'gsoc_grading_record'
    fields = ['grade_decision', 'locked']
    widgets = forms.choiceWidgets(GSoCGradingRecord, ['grade_decision'])


class GradingRecordDetails(base.GSoCRequestHandler):
  """View to display GradingRecord details.
  """

  def djangoURLPatterns(self):
    return [
        url(r'grading_records/detail/%s$' % gsoc_url_patterns.GRADING_RECORD,
         self, name='gsoc_grading_record_detail'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.gradingSurveyRecordFromKwargs()
    check.isHost()

  def context(self, data, check, mutator):
    assert isSet(data.record)

    record = data.record

    if data.POST:
      record_form = GradingRecordForm(data=data.POST)
    else:
      # locked is initially set to true because the user is editing it manually
      record_form = GradingRecordForm(
          instance=record, initial={'locked': True})

    return {
        'page_name': 'Grading Record Details',
        'record': record,
        'record_form': record_form,
        }

  def post(self, data, check, mutator):
    """Handles the POST request when editing a GradingRecord."""
    assert isSet(data.record)

    record_form = GradingRecordForm(data=data.POST)

    if not record_form.is_valid():
      return self.get(data, check, mutator)

    decision = record_form.cleaned_data['grade_decision']
    locked = record_form.cleaned_data['locked']

    record = data.record
    record.grade_decision = decision
    record.locked = locked
    record.put()

    grading_record.updateProjectsForGradingRecords([record])

    # pass along these params as POST to the new task
    task_params = {'record_key': str(record.key())}
    task_url = '/tasks/gsoc/grading_record/mail_result'

    mail_task = taskqueue.Task(params=task_params, url=task_url)
    mail_task.add('mail')

    data.redirect.id(record.grading_survey_group.key().id_or_name())
    return data.redirect.to('gsoc_grading_record_overview')

  def templatePath(self):
    return 'modules/gsoc/grading_record/details.html'
