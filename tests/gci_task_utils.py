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


"""Utils for manipulating GCI task data.
"""


import datetime

from soc.modules.gci.models import task as task_model
from soc.modules.gci.models.work_submission import GCIWorkSubmission

from soc.modules.seeder.logic.seeder import logic as seeder_logic


def seedTask(program, org, mentors, student=None, **kwargs):
  """Seeds a new task.

  Args:
    program: Program to which the task belongs.
    org: Organization to which the task belongs.
    mentors: List of mentor profile keys assigned to the task.
    student: Profile entity of the student assigned to the task.

  Returns:
    A newly seeded task entity.
  """
  properties = {
      'program': program,
      'org': org,
      'status': task_model.OPEN,
      'task_type': program.task_types[0],
      'mentors': mentors,
      'student': student,
      'user': student.parent_key() if student else None,
      'created_by': mentors[0] if mentors else None,
      'modified_by': mentors[0] if mentors else None,
      'created_on': datetime.datetime.now() - datetime.timedelta(20),
      'modified_on': datetime.datetime.now() - datetime.timedelta(10)
      }
  properties.update(**kwargs)
  return seeder_logic.seed(task_model.GCITask, properties,
      auto_seed_optional_properties=False)


class GCITaskHelper(object):
  """Helper class to aid in manipulating GCI task data.
  """

  def __init__(self, program):
    """Initializes the GCITaskHelper.

    Args:
      program: a GCI program
    """
    self.program = program

  def seed(self, model, properties,
           auto_seed_optional_properties=False):
    return seeder_logic.seed(model, properties, recurse=False,
        auto_seed_optional_properties=auto_seed_optional_properties)

  def createTaskWithMentors(self, status, org, mentors, student=None, override={}):
    """Creates a GCI task with mentors.

    Args:
      status: the status of the task
      org: the org under which the task is created
      mentors: mentors for the task
      student: student who claimed the task
    """
    return seedTask(
        self.program, org, mentors=[mentor.key() for mentor in mentors],
        student=student, status=status, **override)

  def createWorkSubmission(self, task, student, url='http://www.example.com/'):
    """Creates a GCIWorkSubmission.

    Args:
      task: The task to create a worksubmission for.
      student: The student whose work it is.
      url: The url to the work.
    """
    work = GCIWorkSubmission(
        parent=task, program=task.program, org=task.org, user=student.user,
        url_to_work=url)
    work.put()
    return work
