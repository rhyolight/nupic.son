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

"""Logic for Survey related models which stores evaluation survey for projects.
"""


from google.appengine.ext import db

from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.project_survey import ProjectSurvey

MIDTERM_ID = 'midterm'
FINAL_ID = 'final'


def getSurveysForProgram(model, program, surveys):
  """Return the survey entity for a given program and the survey link id.

  Args:
    model: The Survey Model against which we need to query
    program: entity representing the program from which the featured
        projects should be fetched
    surveys: link id of the survey(s) which should be fetched
  """
  q = db.Query(model)
  q.filter('scope', program)

  if isinstance(surveys, list):
    q.filter('link_id IN', surveys)
    return q.fetch(1000)
  else:
    q.filter('link_id', surveys)
    return q.get()


def getMidtermProjectSurveyForProgram(program):
  return getSurveysForProgram(ProjectSurvey, program, MIDTERM_ID)


def getMidtermGradingProjectSurveyForProgram(program):
  return getSurveysForProgram(GradingProjectSurvey, program, MIDTERM_ID)


def getFinalProjectSurveyForProgram(program):
  return getSurveysForProgram(ProjectSurvey, program, FINAL_ID)


def getFinalGradingProjectSurveyForProgram(program):
  return getSurveysForProgram(GradingProjectSurvey, program, FINAL_ID)
