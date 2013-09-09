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

import collections
import csv
import json

from google.appengine.api import memcache
from google.appengine.ext import blobstore

from django.utils import html as html_utils


_SCHOOL_LIST_MEMCACHE_KEY_PATTERN = 'schools/%(program_key)s'

class School(object):
  """Class that represents a single school."""

  def __init__(self, uid, name, country):
    """Initializes a new instance of School class.

    Args:
      uid: identifier of the school.
      name: full name of the school.
      country: country in which the school is located.
    """
    self.uid = uid
    self.name = name
    self.country = country


def getSchoolsFromReader(reader):
  """Returns schools that were predefined for the specified input reader.

  Args:
    reader: reader object that describes input for the underlying CSV reader.

  Returns:
    list of School objects.
  """
  if not reader:
    return []
  else:

    schools = []
    csv_reader = csv.reader(reader, delimiter='\t')
    for row in csv_reader:
      # skip possible empty lines
      if row:
        schools.append(School(
            html_utils.escape(row[0]),
            html_utils.escape(row[1]),
            html_utils.escape(row[2])))
    return schools


def getMappedByCountries(program):
  """Returns a dictionary that maps countries to schools that are located in
  these countries.

  Args:
    program: program entity.

  Returns:
    a dict that maps countries to list of names of schools that are located
    in the given country.
  """
  if program.schools:
    memcache_key = _SCHOOL_LIST_MEMCACHE_KEY_PATTERN % {
        'program_key': program.key().name()
        }
    cached_map = memcache.get(memcache_key)
    if cached_map is not None:
      return json.loads(cached_map)
    else:
      school_map = collections.defaultdict(list)
      schools = getSchoolsFromReader(blobstore.BlobReader(program.schools))
      for school in schools:
        school_map[school.country].append(school.name)

      memcache.set(memcache_key, json.dumps(school_map))
      return school_map
  else:
    return {}
