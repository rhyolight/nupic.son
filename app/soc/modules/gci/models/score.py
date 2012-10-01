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

"""This module contains the GCI specific Score Model.
"""


from google.appengine.ext import db

from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.program import GCIProgram


class GCIScore(db.Model):
  """GCIScore model.

  It is applicable to students in order to keep track on the points
  they earn by completing on the tasks. The corresponding GCIProfile
  model is a parent of an entity belonging to this model.

  Parent:
    soc.modules.gci.models.profile.GCIProfile (specifically student profiles).
  """

  #: Required reference to the program so we can query for all rankings
  #: in a single program at once.
  program = db.ReferenceProperty(reference_class=GCIProgram, required=True)

  #: total number of points that the student collected by working on tasks
  points = db.IntegerProperty(required=True, default=0)

  #: tasks that have been taken into account when calculating the score
  tasks = db.ListProperty(item_type=db.Key, default=[])


class GCIOrgScore(db.Model):
  """GCIOrgScore model.

  It describes the number of tasks that the specified student, whose
  GCIProfile is set as a parent of this entity, has completed for
  the specified organization.

  Parent:
    soc.modules.gci.models.profile.GCIProfile (specifically student profiles).
  """

  #: Organization to which the score refers
  org = db.ReferenceProperty(reference_class=GCIOrganization, required=True)

  #: Lists of tasks the student has completed for the organization
  tasks = db.ListProperty(item_type=db.Key, default=[])

  def numberOfTasks(self):
    """Returns the number of tasks that the student completed for
    the organization.
    """
    return len(self.tasks)
