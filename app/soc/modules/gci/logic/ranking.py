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

"""GCIStudentRanking logic methods.
"""


import logging
import re

from google.appengine.ext import db

from django.utils.datastructures import SortedDict

from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.models.score import GCIScore
from soc.modules.gci.models.task import POINTS
from soc.modules.gci.views import forms
from soc.modules.gci.views.helper import url_names


def get(profile):
  """Gets the score entity associated with the specified profile.

  Args:
    profile: GCIProfile entity to retrieve a score for
  """
  query = GCIScore.all().ancestor(profile)
  return query.get()


def updateScore(task):
  """Updates score for a student who worked on the specified task.

  Args:
    task: GCITask that has been completed and should be taken into account in
          the score.
  """
  logging.info("updateScore starts for task %s" % task.key().id())
  if task.status != 'Closed':
    logging.warning('Trying to update score for a task that is not closed.')

  student = task.student
  program = task.program
  task_key = task.key()

  def update_ranking_txn():
    logging.info("updateScore txn starts for task %s" % task_key.id())
    query = GCIScore.all().ancestor(student)
    score = query.get()

    # create a new GCIStore entity if one does not exist yet
    if not score:
      score = GCIScore(parent=student, program=program)

    # check if the task has been included in the score
    if task_key not in score.tasks:
      if not task.points_invalidated:
        score.points += POINTS[task.difficulty_level]
      score.tasks.append(task_key)

    score.put()

    query = GCIStudentInfo.all().ancestor(student)
    student_info = query.get()

    # set in student info that the student has completed a task
    if not student_info.task_closed:
      student_info.task_closed = True
      student_info.put()

  db.run_in_transaction(update_ranking_txn)


def updateRankingWithTask(task):
  """Updates ranking with the specified task.

  Args:
    task: GCITask that has been completed and should be taken into account in
          the ranking.
  """

  # get current ranking for the student if it is not specified
  ranking = getOrCreateForStudent(task.student)

  # check if the task has not been considered
  if task.key() not in ranking.tasks:
    #: update total number of points with number of points for this task
    ranking.points = ranking.points + POINTS[task.difficulty_level]
    ranking.tasks.append(task.key())
    ranking.put()

  return ranking


def calculateRankingForStudent(student, tasks):
  """Calculates ranking for the specified student with the specified
  list of tasks.

  It is assumed that all the tasks from the list belong to the student. Any
  existing ranking for this student will be overwritten.

  Args:
    student: GCIProfile entity representing the student
    tasks: List of GCITasks that have been completed by the student
  """
  ranking = getOrCreateForStudent(student)

  points = 0
  for task in tasks:
    points += POINTS[task.difficulty_level]

  ranking.points = points
  ranking.tasks = [task.key() for task in tasks]
  ranking.put()

  return ranking


def calculateScore(student, tasks, program):
  """Calculates score for the specified student with the specified
  list of tasks.

  It is assumed that all the tasks from the list belong to the student. Any
  existing score for this student will be overwritten.

  Args:
    student: GCIProfile entity representing the student
    tasks: List of GCITasks that have been completed by the student
    program: GCIProgram entity that all the tasks refer to
  """
  # do not calculate score for students who have not completed any tasks
  if not tasks:
    return None

  points = 0
  for task in tasks:
    if not task.points_invalidated:
      points += POINTS[task.difficulty_level]

  def calculate_score_txn():
    query = GCIScore.all().ancestor(student)
    score = query.get()

    # create a new GCIStore entity if one does not exist yet
    if not score:
      score = GCIScore(parent=student, program=program)

    score.points = points
    score.tasks = [task.key() for task in tasks]
    score.put()

    # set that the student closed a task in GCIStudentInfo
    query = GCIStudentInfo.all().ancestor(student)
    student_info = query.get()
    student_info.task_closed = True
    student_info.put()

  return db.run_in_transaction(calculate_score_txn)


def allScoresForProgramQuery(program):
  """Returns the query to fetch all the scores for the specified program.

  Args:
    program: GCIProgram entity for which the query should filter the program
  """
  return GCIScore.all().filter('program =', program)

def winnersForProgram(data):
  """Returns the winners for the program.

  The number of winners chosen is configurable from the program edit page. The
  return datastructure is a dictionary with profile keys of winners as keys
  with values as dictionaries containing the name, number of task and the
  points scored.

  Args:
    data: The RequestData object.
  """
  program = data.program

  q = GCIScore.all()
  q.filter('program', program)
  q.filter('points >', 0)
  q.order('-points')
  scores = q.fetch(program.nr_winners)

  profile_keys = [s.parent_key() for s in scores]
  profiles = db.get(profile_keys)

  winners = SortedDict()
  for score in scores:
    winners[score.parent_key()] = {
        'score': score,
        }

  for profile in profiles:
    winner = winners[profile.key()]
    winner['profile'] = profile
    winner['completed_tasks_link'] = data.redirect.profile(
        profile.link_id).urlOf(url_names.GCI_STUDENT_TASKS)

    if profile.avatar:
      avatar_groups = re.findall(forms.RE_AVATAR_COLOR, profile.avatar)
      # Being a bit pessimistic
      if avatar_groups:
        # We only want the first match, so pick group[0]
        name, prefix = avatar_groups[0]
        winner['avatar_name'] = '%s-%s.jpg' % (name, prefix)
        winner['avatar_prefix'] = prefix

  return winners
