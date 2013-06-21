# Copyright 2013 the Melange authors.
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

"""Logic for surveys that are taken by students."""

from google.appengine.ext import db

from soc.modules.gsoc.models import project_survey as project_survey_model


def constructEvaluationKey(program_key, survey_type):
  """Returns key name of the student evaluation with the specified type and for
  the specified program.

  Args:
    program_key: program key.
    survey_type: type of the evaluation. Currently supported types are:
        MIDTERM_EVAL and FINAL_EVAL.

  Returns:
    a string that represents key name of the evaluation.

  Raises:
    ValueError: if survey type is not supported.
  """
  if survey_type not in project_survey_model.SURVEY_TYPES:
    raise ValueError('survey type %s is not supported.' % survey_type)
  return db.Key.from_path(
      project_survey_model.ProjectSurvey.kind(),
      'gsoc_program/%s/%s' % (program_key.name(), survey_type))


def getStudentEvaluations(program_key):
  """Returns survey entities that work as evaluations to be taken by students
  in the specified program.

  Args:
    program_key: program key

  Returns:
    set of evaluation entities
  """
  keys = []
  for survey_type in project_survey_model.SURVEY_TYPES:
    keys.append(constructEvaluationKey(program_key, survey_type))

  return set(entity for entity in db.get(keys) if entity is not None)
