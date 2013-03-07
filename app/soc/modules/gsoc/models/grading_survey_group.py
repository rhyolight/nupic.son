# Copyright 2009 the Melange authors.
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

"""GradingSurveyGroup has the ability to link a GradingProjectSurvey to a
ProjectSurvey for evaluation purposes.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import grading_project_survey as grading_project_survey_model
from soc.modules.gsoc.models import project_survey as project_survey_model


class GSoCGradingSurveyGroup(db.Model):
  """The GradingSurveyGroups links a ProjectSurvey with a GradingProjectSurvey.

  The purpose of this model is to be able to link two different types of
  Surveys together so that a decision can be made about whether or not a
  Student has passed the evaluation. This model will link the Surveys together
  a GradingRecord will link the SurveyRecords.

  A GradingSurvey group can also work with only a GradingProjectSurvey defined.

  The GradingSurveyGroup can have several GradingRecords attached to it. These
  will contain matching SurveyRecords for the surveys set in this group, of
  course only if they are filled in.
  """

  #: Name to give to this group for easy human-readable identification.
  name = db.StringProperty(
      required=True, verbose_name=ugettext('Survey Group Name'))

  #: Program that this group belongs to.
  program = db.ReferenceProperty(
      reference_class=program_model.GSoCProgram, required=True,
      collection_name='gsoc_grading_survey_groups')

  #: GradingProjectSurvey which belongs to this group.
  grading_survey = db.ReferenceProperty(
      reference_class=grading_project_survey_model.GradingProjectSurvey,
      required=True, collection_name='gsoc_grading_survey_groups')

  #: non-required ProjectSurvey that belongs to this group.
  student_survey = db.ReferenceProperty(
      reference_class=project_survey_model.ProjectSurvey, required=False,
      collection_name='gsoc_project_survey_groups')

  #: DateTime when the last GradingRecord update was started for this group.
  last_update_started = db.DateTimeProperty(
      verbose_name=ugettext('Last Record update started'))

  #: DateTime when the last GradingRecord update was completed for this group.
  last_update_complete = db.DateTimeProperty(
      verbose_name=ugettext('Last Record update completed'))
