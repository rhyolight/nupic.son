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

"""Tests for GCIStudentRanking methods.
"""

__authors__ = [
    '"Praveen Kumar" <praveen97uma@gmail.com>',
    ]


import unittest

from soc.modules.gci.logic import ranking as ranking_logic
from soc.modules.gci.models.student_ranking import GCIStudentRanking

from tests.gci_task_utils import GCITaskHelper
from tests.profile_utils import GCIProfileHelper
from tests.program_utils import GCIProgramHelper


class RankingTest(unittest.TestCase):
  """Tests the ranking methods for students in GCI.
  """
  
  def setUp(self):
    self.gci_program_helper = GCIProgramHelper()
    self.program = self.gci_program_helper.createProgram()
    current_user_profile_helper = GCIProfileHelper(self.program, False)
    self.student = current_user_profile_helper.createStudent()
    self.task_helper = GCITaskHelper(self.program)

  def testGetOrCreateForStudent(self):
    """Tests if an appropriate ranking object is created for a student.
    """
    #There is no GCIStudentRanking object for self.student in the datastore.
    #Hence, a new entity should be created and returned.
    q = GCIStudentRanking.all()
    q.filter('student', self.student)
    ranking = q.get()
    
    self.assertEqual(ranking, None)
    
    actual_ranking = ranking_logic.getOrCreateForStudent(self.student)
    q = GCIStudentRanking.all()
    q.filter('student', self.student)
    expected_ranking = q.get()
    self.assertEqual(expected_ranking.key(), actual_ranking.key())
    
    #GCIStudentRanking object already exists for a student.
    student_profile_helper = GCIProfileHelper(self.program, False)
    student_profile_helper.createOtherUser('student@gmail.com')
    student = student_profile_helper.createStudent()
    ranking = GCIStudentRanking(program=student.scope, student=student)
    ranking.put()
    actual_ranking = ranking_logic.getOrCreateForStudent(student)
    
    self.assertEqual(ranking.key(), actual_ranking.key())
    
  def testUpdateRankingWithTask(self):
    """Tests if the ranking of a specified task is updated.
    """
    org = self.gci_program_helper.createOrg()
    
    mentor_profile_helper = GCIProfileHelper(self.program, False)
    mentor_profile_helper.createOtherUser('mentor@gmail.com')
    mentor = mentor_profile_helper.createMentor(org)
    
    task = self.task_helper.createTask('Closed', org, mentor, self.student)
    
    expected_value = task.taskDifficulty().value
    actual = ranking_logic.updateRankingWithTask(task)
    self.assertEqual(expected_value, actual.points)
    
    another_task = self.task_helper.createTask('Closed', org, 
                                               mentor, self.student)
    expected = expected_value + another_task.taskDifficulty().value
    actual = ranking_logic.updateRankingWithTask(another_task)
    self.assertEqual(expected, actual.points)
    
    #Test with an existing GCIStudentRanking object.
    student_profile_helper = GCIProfileHelper(self.program, False)
    student_profile_helper.createOtherUser('student@gmail.com')
    another_student = student_profile_helper.createStudent()
    
    ranking = GCIStudentRanking(program=self.program, student=another_student)
    ranking.points = 5
    ranking.put()
    gci_program_helper = GCIProgramHelper()
    org = gci_program_helper.createOrg()
    mentor_profile_helper = GCIProfileHelper(self.program, False)
    mentor_profile_helper.createOtherUser('men@g.com')
    mentor = mentor_profile_helper.createMentor(org)
    
    task = self.task_helper.createTask('Closed', org, mentor, another_student)
    
    expected_value = ranking.points + task.taskDifficulty().value
    actual = ranking_logic.updateRankingWithTask(task)
    self.assertEqual(expected_value, actual.points)

  def testCalculateRankingForStudent(self):
    """Tests if the ranking of a student is correctly calculated.
    """
    org = self.gci_program_helper.createOrg()
    mentor_profile_helper = GCIProfileHelper(self.program, False)
    mentor_profile_helper.createOtherUser('mentot@gmail.com')
    mentor = mentor_profile_helper.createMentor(org)
    createTask = self.task_helper.createTask
    tasks = [
        createTask('Closed', org, mentor, self.student) for _ in range(5)
    ]
    
    expected_value = 0
    for task in tasks:
      expected_value+=task.taskDifficulty().value
    actual = ranking_logic.calculateRankingForStudent(self.student, tasks)
    self.assertEquals(expected_value, actual.points)
    
    #Test with an already existing GCIStudentRanking object.
    student_profile_helper = GCIProfileHelper(self.program, False)
    student_profile_helper.createOtherUser('stud@c.com')
    another_student = student_profile_helper.createStudent()
    
    ranking = GCIStudentRanking(program=self.program, student=another_student)
    ranking.points = 5
    ranking.put()
    
    gci_program_helper = GCIProgramHelper()
    org = gci_program_helper.createOrg()
    mentor_profile_helper = GCIProfileHelper(self.program, False)
    mentor_profile_helper.createOtherUser('praveen@gm.com')
    mentor = mentor_profile_helper.createMentor(org)
    tasks = [
        createTask('Closed', org, mentor, another_student) for _ in range(5)
    ]
    expected_value = 0
    for task in tasks:
      expected_value += task.taskDifficulty().value
    actual = ranking_logic.calculateRankingForStudent(another_student, tasks)
    self.assertEquals(expected_value, actual.points)

