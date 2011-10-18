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

"""GradingRecord related functions.
"""

__authors__ = [
  '"Akeda Bagus" <admin@gedex.web.id>',
  ]

from google.appengine.ext import db

from soc.models.org_app_survey import OrgAppSurvey
from soc.models.org_app_record import OrgAppRecord


def getForProgram(program):
  """Return the org_app survey for a given program.

  Args:
    program: program entity for which the survey should be searched
  """
  # retrieve a GradingSurveyRecord
  q = OrgAppSurvey.all()
  q.filter('program', program)
  survey = q.get()

  return survey


def getForSurvey(org_app_survey):
  """Return the org_app survey for a given program.

  Args:
    program: program entity for which the survey should be searched
  """
  # retrieve a GradingSurveyRecord
  q = OrgAppRecord.all()
  q.filter('survey', org_app_survey)
  record = q.get()

  return record
