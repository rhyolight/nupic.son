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

from soc.views import template
from soc.views.helper import lists
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


class SurveyResponseList(template.Template):
  """Template for listing all responses to the specified survey."""

  def __init__(self, data, survey, idx=0, description=''):
    """Creates a new SurveyRecordList template.

    Args:
      data: request_data.RequestData object for the current request.
      survey: Survey entity to show the responses for
      idx: The index of the list to use.
      description: The (optional) description of the list.
    """
    super(SurveyResponseList, self).__init__(data)

    self.survey = survey
    self.idx = idx
    self.description = description

    # Create the configuration based on the schema of the survey
    list_config = lists.ListConfiguration()
    schema = surveys.SurveySchema(survey)

    for field in schema:
      label = field.getLabel()
      field_id = field.getFieldName()
      list_config.addPlainTextColumn(
          field_id, label, _field_or_empty(field_id), hidden=True)

    self.list_config = list_config
