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

"""Logic for universities."""

from google.appengine.ext import ndb

from melange.models import universities as universities_model


#: Maximal number of universities that can be stored in one cluster.
MAX_UNIVERSITIES_PER_CLUSTER = 5000

def uploadUniversities(input_data, program_key):
  """Uploads a list of predefined universities for the specified program.

  Args:
    input_data: list of tuples. Each element of that tuple represents a single
      university and has exactly three elements. The first one is unique
      identifier of the university, the second one is its name and the third
      one is the country in which the institution is located.
    program: program key.

  Returns:
    list of newly created university_model.Universities entities that contain
    all universities coming from the input data.
  """
  if len(input_data) > MAX_UNIVERSITIES_PER_CLUSTER:
    raise ValueError(
        '%s items in input. Maximal supported value is %s' % (
            len(input_data), MAX_UNIVERSITIES_PER_CLUSTER))

  university_cluster = universities_model.UniversityCluster(
      parent=ndb.Key.from_old_key(program_key))

  for uid, name, country in input_data:
    university_cluster.universities.append(
        universities_model.University(uid=uid, name=name, country=country))

  university_cluster.put()


def getUniversitiesForProgram(program_key):
  """Returns universities that were defined for the specified program.

  Args:
    program_key: program key.

  Returns:
    list of university_model.Unversity entities.
  """
  university_clusters = ndb.Query(
      kind=universities_model.UniversityCluster._get_kind(),
      ancestor=ndb.Key.from_old_key(program_key)).fetch(1000)

  universities = []
  for university_cluster in university_clusters:
    universities.extend(university_cluster.universities)

  return universities
