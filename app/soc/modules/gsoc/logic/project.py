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

"""Logic for project."""

import datetime

from google.appengine.api import memcache
from google.appengine.ext import db

from soc.modules.gsoc.models import project as project_model


NUMBER_OF_EVALUATIONS = 2


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
    query = project_model.GSoCProject.all()
    query.filter('is_featured', True)
    query.filter('program', program)
    if current_timeline == 'coding_period':
      project_status = project_model.STATUS_ACCEPTED
    else:
      project_status = 'completed'
    query.filter('status', project_status)
    return query

  q = queryForProject()

  # the cache stores a 3-tuple in the order student_project entity,
  # cursor and the last time the cache was updated
  fsp_cache = memcache.get('featured_gsoc_project' + program.key().name())

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


def getProjectsQuery(keys_only=False, ancestor=None, **properties):
  """Returns project_model.GSoCProject query object for the given set
  of properties.

  Args:
    ancestor: The student for which the accepted projects must be fetched.
    properties: keyword arguments containing the properties for which the
        query must be constructed.
  """
  q = db.Query(project_model.GSoCProject, keys_only=keys_only)

  if ancestor:
    q.ancestor(ancestor)

  for k, v in properties.items():
    q.filter(k, v)

  return q


def getAcceptedProjectsQuery(keys_only=False, ancestor=None, **properties):
  """Returns project_model.GSoCProject query object for the given
  set of properties for accepted projects.

  Args:
    ancestor: The student for which the accepted projects must be fetched.
    properties: keyword arguments containing the properties for which the
        query must be constructed.
  """
  q = getProjectsQuery(keys_only, ancestor, **properties)
  q.filter('status', project_model.STATUS_ACCEPTED)

  return q


def getAcceptedProjectsForOrg(org, limit=1000):
  """Returns all the accepted projects for a given organization.

  Args:
    org: The organization entity for which the accepted projects are accepted.
  """
  q = getAcceptedProjectsQuery(org=org)
  return q.fetch(limit)

def getAcceptedProjectsForStudent(student, limit=1000):
  """Returns all the accepted projects for a given student.

  Args:
    student: The student for whom the projects should be retrieved.
  """
  q = getAcceptedProjectsQuery(ancestor=student)
  return q.fetch(limit)

def getProjectsQueryForOrgs(org_keys):
  """Returns the query corresponding to projects for the given organization(s).

  Args:
    org_keys: The list of organization keys for which the projects
      should be queried.
  """
  query = getProjectsQuery()
  query.filter('org IN', org_keys)
  return query


def getProjectsQueryForEval(keys_only=False, ancestor=None, **properties):
  """Returns the query corresponding to projects to be evaluated.

  This is a special query needed to build evaluation lists.
  """
  q = getProjectsQuery(keys_only, ancestor, **properties)
  q.filter('status IN', [project_model.STATUS_ACCEPTED, 'failed', 'completed'])
  return q


def getProjectsQueryForEvalForOrgs(org_keys):
  """Returns the query corresponding to projects for the given organization(s).

  This is a special query needed to build evaluation lists.

  Args:
    org_keys: The list of organization keys for which the projects
        should be queried.
  """
  query = getProjectsQueryForOrgs(org_keys)
  query.filter(
      'status IN', [project_model.STATUS_ACCEPTED, 'failed', 'completed'])
  return query


def getProjectsForOrgs(org_keys, limit=1000):
  """Returns all the projects for the given organization(s).

  Unlike getAcceptedProjectsForOrg function, this returns all the projects
  for all the orgs listed

  Args:
    org_keys: The list of organization keys for which the projects
        should be queried.
  """
  q = getProjectsQueryForOrgs(org_keys)
  return q.fetch(limit)


def hasMentorProjectAssigned(profile, org_key=None):
  """Checks whether the specified profile has a project assigned. It also
  accepts an optional argument to pass a specific organization to which
  the project should belong.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: the specified GSoCProfile entity or its db.Key
    org_key: optional organization key

  Returns:
    True, if the profile has at least one project assigned; False otherwise.
  """
  query = project_model.GSoCProject.all()
  query.filter('mentors', profile.key.to_old_key())

  if org_key:
    query.filter('org', org_key.to_old_key())

  return query.count() > 0
