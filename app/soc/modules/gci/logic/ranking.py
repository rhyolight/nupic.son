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

"""GCIStudentRanking logic methods.
"""


from soc.modules.gci.models.student_ranking import GCIStudentRanking


def getOrCreateForStudent(student):
  """Gets or creates the ranking object for the student.

  Args:
    student: GCIProfile entity representing the student.
  """
  q = GCIStudentRanking.all()
  q.filter('student', student)
  ranking = q.get()

  if not ranking:
    # create a new one
    ranking = GCIStudentRanking(program=student.scope, student=student)
    ranking.put()

  return ranking

def updateRankingWithTask(task, prefetched_difficulties=None):
  """Updates ranking with the specified task.

  Args:
    task: GCITask that has been completed and should be taken into account in
          the ranking.
    prefetched_difficulties: optional, list of prefetched TaskDifficultyTags
  """
  # get current ranking for the student if it is not specified
  ranking = getOrCreateForStudent(task.student)

  # check if the task has not been considered
  if task.key() not in ranking.tasks:
    #: update total number of points with number of points for this task
    task_value = task.taskDifficulty(prefetched_difficulties).value
    ranking.points = ranking.points + task_value
    ranking.tasks.append(task.key())
    ranking.put()

  return ranking

def calculateRankingForStudent(student, tasks, prefetched_difficulties=None):
  """Calculates ranking for the specified student with the specified
  list of tasks.

  It is assumed that all the tasks from the list belong to the student. Any
  existing ranking for this student will be overwritten.

  Args:
    student: GCIProfile entity representing the student
    tasks: List of GCITasks that have been completed by the student
    prefetched_difficulties: optional, list of prefetched TaskDifficultyTags
  """
  ranking = getOrCreateForStudent(student)

  points = 0
  for task in tasks:
    points += task.taskDifficulty(prefetched_difficulties).value

  ranking.points = points
  ranking.tasks = [task.key() for task in tasks]
  ranking.put()

  return ranking
