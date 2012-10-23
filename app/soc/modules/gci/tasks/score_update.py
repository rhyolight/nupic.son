#!/usr/bin/env python2.5
#
# Copyright 2010 the Melange authors.
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

"""Appengine Tasks related to GCI scores.
"""


import logging

from google.appengine.api import taskqueue
from google.appengine.ext import db

from django.conf.urls.defaults import url

from soc.tasks import responses
from soc.views.helper import url_patterns

from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.task import GCITask


def studentIterator(func):
  """Wrapper that iterates through all the students participating in the
  GCIProgram which is specified in the task's POST parameters.

  Args in POST dict:
    cursor: Query cursor to figure out where we need to start processing
  """

  def wrapper(self, request, *args, **kwargs):
    key_name = '%s/%s' % (kwargs['sponsor'], kwargs['program'])
    cursor = request.POST.get('cursor')

    program = GCIProgram.get_by_key_name(key_name)
    if not program:
      logging.warning(
          'Enqueued recalculate ranking task for non-existing '
          'program: %s' %key_name)
      return responses.terminateTask()

    # Retrieve the students for the program
    q = GCIProfile.all()
    q.filter('scope', program)
    q.filter('is_student', True)

    if cursor:
      q.with_cursor(cursor)

    profiles = q.fetch(25)

    for profile in profiles:
      func(self, request, profile, *args, **kwargs)

    if profiles:
      # schedule task to do the rest of the students
      params = {
          'cursor': q.cursor(),
          }
      taskqueue.add(queue_name='gci-update', url=request.path, params=params)

    return responses.terminateTask()

  return wrapper


class ScoreUpdate(object):
  """Appengine tasks for updating the scores for GCI program.
  """

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module.
    """
    patterns = [
        url(r'^tasks/gci/scores/clear/%s$' % url_patterns.PROGRAM,
            self.clearScore, name='task_clear_gci_scores'),
        url(r'^tasks/gci/scores/calculate/%s$' % url_patterns.PROGRAM,
            self.calculateScore, name='task_calculate_gci_scores')]
    return patterns  

  @studentIterator
  def clearScore(self, request, profile, *args, **kwargs):
    """Clears all GCIOrgScore entities associated with 
    the specified GCIProfile.
    """
    if not self.profile.is_student:
      raise ValueError("The specified GCIProfile does not belong to a student")

    student_info = profile_logic.queryStudentInfoForParent(profile).get()
    db.run_in_transaction(profile_logic.clearOrgScoresTxn(student_info))

  @studentIterator
  def calculateScore(self, request, profile, *args, **kwargs):
    """Calculates score for the student associated with the specified
    GCIProfile.
    """
    # get all the tasks that the student has completed
    query = GCITask.all()
    query.filter('student', profile)
    query.filter('status', 'Closed')

    tasks = query.fetch(1000)

    # calculate org score with all the tasks
    db.run_in_transaction(org_score_logic.updateOrgScoresTxn(tasks))
