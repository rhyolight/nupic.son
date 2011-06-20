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

"""Module containing the AccessChecker class that contains helper functions
for checking access.
"""

__authors__ = [
    '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation, BadRequest
from soc.logic.exceptions import NotFound
from soc.views.helper import access_checker

from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.models.student_proposal import StudentProposal


DEF_MAX_PROPOSALS_REACHED = ugettext(
    'You have reached the maximum number of proposals allowed '
    'for this program.')

DEF_NO_PROJECT_SURVEY_MSG = ugettext(
    'The project survey with the requested parameters does not exist.')

DEF_NO_RECORD_FOUND = ugettext(
    'The Record with the specified key was not found.')

DEF_SURVEY_DOES_NOT_BELONG_TO_YOU_MSG = ugettext(
    'This survey does not correspond to the project you are mentor for, '
    'hence you cannot access this survey.')

DEF_SURVEY_NOT_ACCESSIBLE_FOR_PROJECT_MSG = ugettext(
    'You cannot access this survey because you do not have any '
    'ongoing project.')


class Mutator(access_checker.Mutator):

  def projectSurveyRecordFromKwargs(self):
    """Sets the survey record in RequestData object.
    """
    # kwargs which defines a survey
    fields = ['prefix', 'sponsor', 'program', 'survey']

    key_name = '/'.join(self.data.kwargs[field] for field in fields)
    self.data.project_survey = ProjectSurvey.get_by_key_name(key_name)

    if not self.data.project_survey:
      raise NotFound(DEF_NO_PROJECT_SURVEY_MSG)

    self.projectFromKwargs()

    q = GSoCProjectSurveyRecord.all()
    q.filter('project', self.data.project)
    q.filter('survey', self.data.project_survey)
    self.data.project_survey_record = q.get()

  def gradingSurveyRecordFromKwargs(self):
    """Sets a GradingSurveyRecord entry in the RequestData object.
    """
    if not 'key' in self.data.kwargs:
      raise BadRequest(access_checker.DEF_NOT_VALID_REQUEST_MSG)

    try:
      record = GSoCGradingRecord.get(db.Key(self.data.kwargs['key']))
      self.data.record = record
    except db.datastore_errors.BadKeyError:
      record = None

    if not record:
      raise NotFound(DEF_NO_RECORD_FOUND) 


class DeveloperMutator(access_checker.DeveloperMutator, Mutator):
  pass


class AccessChecker(access_checker.AccessChecker):
  """Helper classes for access checking in GSoC module.
  """

  def canStudentPropose(self):
    """Checks if the student is eligible to submit a proposal.
    """

    # check if the timeline allows submitting proposals
    self.studentSignupActive()

    # check how many proposals the student has already submitted 
    fields = {
        'scope': self.data.profile
        }
    query = db.Query(StudentProposal)
    query.filter('scope = ', self.data.profile).ancestor(self.data.user)

    if query.count() >= self.data.program.apps_tasks_limit:
      # too many proposals access denied
      raise AccessViolation(DEF_MAX_PROPOSALS_REACHED)

  def isStudentForSurvey(self):
    """Checks if the student can take survey for the project.
    """
    assert access_checker.isSet(self.data.project)

    self.isProjectInURLValid()

    # check if the project belongs to the current user and if so he
    # can access the survey
    expected_profile_key = self.data.project.parent_key()
    if expected_profile_key != self.data.profile.key():
      raise AccessViolation(DEF_SURVEY_DOES_NOT_BELONG_TO_YOU_MSG)

    # check if the project is still ongoing
    if self.data.project.status in ['invalid', 'withdrawn', 'failed']:
      raise AccessViolation(DEF_SURVEY_NOT_ACCESSIBLE_FOR_PROJECT_MSG)

class DeveloperAccessChecker(access_checker.DeveloperAccessChecker):
  pass
