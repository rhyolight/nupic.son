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

"""Logic for ProjectSurveyRecord Model.
"""

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com>',
    ]


from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord


def getEvalRecord(survey, project):
  """Return the mentor evaluation record for the given project.

  Args:
    survey: survey entity for which the record should be searched
    project: the project entity for which we need look for the
        evaluation record
  """
  q = GSoCGradingProjectSurveyRecord.all()
  q.filter('survey', survey)
  q.filter('project', project)

  return q.get()
