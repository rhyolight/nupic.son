#!/usr/bin/python2.5
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

"""Map reduce to merge mentor and co-mentors properties in GSoCProject.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


import logging

from google.appengine.ext import db
from google.appengine.ext.mapreduce import operation

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.project import GSoCProject


def process(project):

  def update_project_txn():
    if not project:
      logging.error("Missing project '%s'." % project)
      return False

    mentor =  GSoCProject.mentor.get_value_for_datastore(project)
    mentors = [mentor]
    for am in project.additional_mentors:
      if am not in mentors:
        mentors.append(am)

    project.mentors = mentors
    project.put()
    return True

  if db.run_in_transaction(update_project_txn):
    yield operation.counters.Increment("projects_updated")
  else:
    yield operation.counters.Increment("missing_project")
