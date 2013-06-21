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

"""Logic for Document Model related to GSoC modules."""

from soc.models import document as document_model


def getVisibilities(data):
  """Returns a list of document visibilities for the current user
  based on the data specified in request data.

  Args:
    data: a RequestData object specified for this request

  Returns:
    a list of visibilities for the current user
  """
  visibilities = []
  if data.is_student:
    visibilities.append(document_model.STUDENT_VISIBILITY.identifier)
    if data.student_info.number_of_projects > 0:
      visibilities.append(
          document_model.ACCEPTED_STUDENT_VISIBILITY.identifier)
  if data.is_org_admin:
    visibilities.append(document_model.ORG_ADMIN_VISIBILITY.identifier)
  if data.is_mentor:
    visibilities.append(document_model.MENTOR_VISIBILITY.identifier)
  return visibilities
