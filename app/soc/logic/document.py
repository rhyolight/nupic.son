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

"""Logic for Document Model."""

from soc.models import document as document_model


def getDocumentQueryForRoles(data):
  """Build the query to fetch documents for a given role in a program.

  Args:
    data: RequestData object for this request.

  Returns:
    A query object that fetches all the documents that should be visible for
    the profile's roles in the current program.
  """
  query = document_model.Document.all()
  query.filter('scope', data.program)

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

  num_visibilities = len(visibilities)

  if num_visibilities == 1:
    query.filter('dashboard_visibility', visibilities[0])
  else:
    query.filter('dashboard_visibility IN', visibilities)

  return query
