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

"""Appengine Tasks related to GCI scores."""

import logging

from google.appengine.api import taskqueue
from google.appengine.ext import db

from django.conf.urls import defaults

from soc.tasks import responses
from soc.views.helper import url_patterns

from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import program as program_model
from soc.modules.gci.models import task as task_model


def clearScore(profile):
  """Clears all GCIOrgScore entities associated with a GCIProfile.

  Args:
    profile: A GCIProfile associated with some student.
  """
  if profile.is_student:
    db.run_in_transaction(org_score_logic.clearOrgScoresTxn(profile.key()))
  else:
    raise ValueError('The specified GCIProfile does not belong to a student!')


def calculateScore(profile):
  """Calculates the score for the student associated with a GCIProfile.

  Args:
    profile: A GCIProfile associated with some student.
  """
  # TODO(nathaniel): The string literals in this function should be constants
  # declared somewhere sensible.
  # Get all the tasks that the student has completed.
  query = task_model.GCITask.all()
  query.filter('student', profile)
  query.filter('status', 'Closed')

  tasks = query.fetch(1000)

  # Calculate org score with all the tasks.
  db.run_in_transaction(org_score_logic.updateOrgScoresTxn(tasks))


def studentIterator(student_profile_function, request, **kwargs):
  """Applies a function to every student profile in a program.

  Args:
    student_profile_function: A function that accepts a single
      student profile_model.GCIProfile as an argument.
    request: A RequestData object.
    **kwargs: Keyword arguments associated with the request.

  Returns:
    An HttpResponse object.
  """
  # TODO(nathaniel): Call a utility function for this key_name.
  key_name = '%s/%s' % (kwargs['sponsor'], kwargs['program'])
  cursor = request.POST.get('cursor')

  program = program_model.GCIProgram.get_by_key_name(key_name)
  if not program:
    logging.warning('Enqueued task for nonexistant program %s' % key_name)
    return responses.terminateTask()

  # Retrieve the students for the program.
  query = profile_model.GCIProfile.all()
  # TODO(nathaniel): These string literals should be constants somewhere.
  query.filter('program', program)
  query.filter('is_student', True)
  if cursor:
    query.with_cursor(cursor)

  student_profiles = query.fetch(25)

  for student_profile in student_profiles:
    student_profile_function(student_profile)

  if student_profiles:
    # Schedule task to do the rest of the students.
    params = {'cursor': query.cursor()}
    taskqueue.add(queue_name='gci-update', url=request.path, params=params)

  return responses.terminateTask()


# TODO(nathaniel): Fit this into the RequestHandler family of classes?
class ScoreUpdate(object):
  """Appengine tasks for updating the scores for GCI program."""

  def _clearScores(self, request, *args, **kwargs):
    """Clears the scores of all students in a program."""
    return studentIterator(clearScore, request, **kwargs)

  def _calculateScores(self, request, *args, **kwargs):
    """Calculates the scores of all students in a program."""
    return studentIterator(calculateScore, request, **kwargs)

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module."""
    return [
        defaults.url(
            r'^tasks/gci/scores/clear/%s$' % url_patterns.PROGRAM,
            self._clearScores, name='task_clear_gci_scores'),
        defaults.url(
            r'^tasks/gci/scores/calculate/%s$' % url_patterns.PROGRAM,
            self._calculateScores, name='task_calculate_gci_scores'),
        ]
