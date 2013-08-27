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

"""Logic for tasks."""

from melange.appengine import db as melange_db

from soc.modules.gci.models import task as task_model


def queryTasksForMentor(profile_key, extra_filters=None):
  """Returns a query to fetch tasks for which the specified mentor has been
  assigned based on the specified criteria.

  Args:
    profile: profile key of the mentor.
    extra_filters: a dictionary containing additional constraints on the query.
  """
  query = task_model.GCITask.all()
  query.filter('mentors', profile_key)

  extra_filters = extra_filters or {}
  for prop, value in extra_filters.iteritems():
    melange_db.addFilterToQuery(query, prop, value)

  return query
