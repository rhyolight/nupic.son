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

"""Logic for GSoC GradingProjectSurvey Model.
"""

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com>',
    ]


from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey


def getGradingProjectSurveyForProgram(program, survey):
  """Return the survey entity for a given program and the survey link id.

  Args:
    program: entity representing the program from which the featured
        projects should be fetched
    survey: link id of the survey which should be fetched
  """
  q = GradingProjectSurvey.all()
  q.filter('scope', program)
  q.filter('link_id', survey)

  return q.get()
