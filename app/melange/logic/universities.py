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


# Maximal safe number of bytes after which no new universities should be added
_MAX_SAFE_SIZE = 1000000

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
  to_put = []
  university_cluster = universities_model.UniversityCluster(
      parent=ndb.Key.from_old_key(program_key))

  for uid, name, country in input_data:
    university_cluster.universities.append(
        universities_model.University(uid=uid, name=name, country=country))

    # check if the current size of proto buffer is still safe
    if university_cluster._to_pb().ByteSize() > _MAX_SAFE_SIZE:
      # safe current list in the data store and create a new entity
      to_put.append(university_cluster)
      university_cluster = universities_model.UniversityCluster(
          parent=ndb.Key.from_old_key(program_key))

  to_put.append(university_cluster)
  ndb.put_multi(to_put)
