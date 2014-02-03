# Copyright 2014 the Melange authors.
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

"""Module containing the template to list survey responses."""

from soc.views.helper import surveys


def _field_or_empty(field_id):
  """In a list returns the contents of the field with the id or an empty
  string if the field does not exist.

  Args:
    field_id: Name of the field for which the value should be retrieved.

  Returns:
    A function that returns value of the specified field for a given entity
    or the empty string, if the field does not exist.
  """
  return lambda entity, *args: getattr(entity, field_id, '')


def addColumnsForSurvey(list_config, survey):
  """Adds text columns corresponding to questions in the specified survey
  to the specified list configuration.

  Args:
    list_config: lists.ListConfiguration object.
    survey: Survey entity for which columns are to be added.
  """
  schema = surveys.SurveySchema(survey)
  for field in schema:
    label = field.getLabel()
    field_id = field.getFieldName()
    list_config.addPlainTextColumn(
        field_id, label, _field_or_empty(field_id), hidden=True)

