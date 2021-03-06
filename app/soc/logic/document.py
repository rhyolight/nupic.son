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


def getDocumentQueryForRoles(data, visibilities):
  """Build the query to fetch documents for a given role in a program.

  Args:
    data: RequestData object for this request.
    visibilities: a list of visibilities for the query

  Returns:
    A query object that fetches all the documents that should be visible for
    the profile's roles in the current program.
  """
  query = document_model.Document.all()
  query.filter('scope', data.program)

  num_visibilities = len(visibilities)

  # When number of visibilities is 0, then the profile should belong
  # to a host, so we apply no filtering.
  if num_visibilities == 1:
    query.filter('dashboard_visibility', visibilities[0])
  elif num_visibilities > 1:
    query.filter('dashboard_visibility IN', visibilities)

  return query
