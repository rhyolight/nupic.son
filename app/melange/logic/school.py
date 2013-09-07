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

"""Logic for schools."""

import threading

from google.appengine.ext import ndb

from melange.models import school as school_model


#: Maximal number of schools that can be stored in one cluster.
MAX_SCHOOLS_PER_CLUSTER = 5000

class _CachedSchools(object):
  """Helper class that manages already cached lists of schools for
  particular programs.
  """

  def __init__(self):
    """Initializes a new instance of the class."""
    # makes sure that ndb.Future is created once per program
    self._init_lock = threading.Lock()

    # maps program keys to ndb.Future objects with schools
    self._cached_map = {}

  def get(self, program_key):
    """Returns schools, which have been predefined for the specified program.

    Args:
      program_key: program key.

    Returns:
      list of school_model.School entities.
    """
    if program_key not in self._cached_map:
      with self._init_lock:
        if program_key not in self._cached_map:
          self._cached_map[program_key] = _schoolsFromDBFuture(
              program_key)

    return self._cached_map[program_key].get_result()

_CACHED_SCHOOLS = _CachedSchools()

@ndb.tasklet
def _schoolsFromDBFuture(program_key):
  """Tasklet that fetches asynchronously all schools, which have been
  predefined for the specified program, directly from datastore.

  Args:
    program_key: program key.

  Returns:
    ndb.Future object whose result is a list of 
    school_model.School entities.
  """
  school_clusters = yield ndb.Query(
      kind=school_model.SchoolCluster._get_kind(),
      ancestor=ndb.Key.from_old_key(program_key)).fetch_async(1000)

  schools = []
  for school_cluster in school_clusters:
    schools.extend(school_cluster.schools)

  raise ndb.Return(schools)


def getSchoolsForProgram(program_key):
  """Returns schools that were defined for the specified program.

  Args:
    program_key: program key.

  Returns:
    list of school_model.School entities.
  """
  return _CACHED_SCHOOLS.get(program_key)


def uploadSchools(input_data, program):
  """Uploads a list of predefined schools for the specified program.

  Args:
    input_data: list of tuples. Each element of that tuple represents a single
      school and has exactly three elements. The first one is unique
      identifier of the school, the second one is its name and the third
      one is the country in which the institution is located.
    program: program entity.

  Returns:
    list of newly created school_model.SchoolCluster entities that contain
    all school coming from the input data.
  """
  if len(input_data) > MAX_SCHOOLS_PER_CLUSTER:
    raise ValueError(
        '%s items in input. Maximal supported value is %s' % (
            len(input_data), MAX_SCHOOLS_PER_CLUSTER))

  school_cluster = school_model.SchoolCluster(
      parent=ndb.Key.from_old_key(program.key()))

  for uid, name, country in input_data:
    school_cluster.schools.append(
        school_model.School(uid=uid, name=name, country=country))

  school_cluster.put()

  program.predefined_schools_counter += len(school_cluster.schools)
  program.put()
