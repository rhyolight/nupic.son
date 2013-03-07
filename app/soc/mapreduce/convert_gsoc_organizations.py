# Copyright 2012 the Melange authors.
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

"""Mapreduce updating GSoCOrganization.
"""


from mapreduce import operation


def process_org_tags(org):
  """Copy organization tags stored in OrgTag to the organization entity.
  """

  tags = []

  for org_tag in org.org_tag:
    tags.append(org_tag.tag)

  org.tags = list(set(tags))

  yield operation.db.Put(org)
  yield operation.counters.Increment('org_tags_updated')
