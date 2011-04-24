#!/usr/bin/env python2.5
#
# Copyright 2011 the Melange authors.
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

"""Logic for GSoC Project Model.
"""

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com>',
    ]


import datetime

from google.appengine.api import memcache

from soc.modules.gsoc.models.project import GSoCProject


def getFeaturedProject(current_timeline, program):
  """Return a featured project for a given program.

  Args:
    current_timeline: where we are currently on the program timeline
    program: entity representing the program from which the featured
        projects should be fetched
  """
  # expiry time to fetch the new featured project entity
  # the current expiry time is 2 hours.
  expiry_time = datetime.timedelta(seconds=7200)

  def queryForProject():
    query = GSoCProject.all()
    query.filter('is_featured', True)
    query.filter('program', program)
    if current_timeline == 'coding_period':
      project_status = 'accepted'
    else:
      project_status = 'completed'
    query.filter('status', project_status)
    return query

  q = queryForProject()

  # the cache stores a 3-tuple in the order student_project entity,
  # cursor and the last time the cache was updated
  fsp_cache = memcache.get('featured_gsoc_project')

  if fsp_cache:
    cached_project, cached_cursor, cache_expiry_time = fsp_cache
    if not datetime.datetime.now() > cache_expiry_time + expiry_time:
      return cached_project
    else:
      q.with_cursor(cached_cursor)
      if q.count() == 0:
        q = queryForProject()

  new_project = q.get()
  new_cursor = q.cursor()
  memcache.set(
    key='featured_gsoc_project',
    value=(new_project, new_cursor, datetime.datetime.now()))

  return new_project


def getAcceptedProjectsQuery(ancestor=None, **properties):
  """Returns the Appengine query object for the given set of properties.

  Args:
    ancestor: The student for which the accepted projects must be fetched.
    properties: keyword arguments containing the properties for which the
        query must be constructed.
  """
  q = GSoCProject.all()

  if ancestor:
    q.ancestor(ancestor)

  q.filter('status', 'accepted')

  for k, v in properties.items():
    q.filter(k, v)

  return q
