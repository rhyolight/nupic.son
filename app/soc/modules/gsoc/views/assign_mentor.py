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

"""Module containing the views for assigning mentors to GSoC Proposals
and Projects.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from google.appengine.ext import db

from soc.views.template import Template


def getMentorsChoicesToAssign(mentors, current_mentor=None):
  """Returns a list of tuple containing the mentor key and mentor name.

  Args:
    mentors: List of potential mentor entities whose Django style choices
        must be returned
    current_mentor: Currently assigned mentor entity in this list
    
  """

  # construct a choice list for all the mentors in possible mentors list
  mentors_choices = []
  for m in mentors:
    m_key = m.key()
    choice = {
        'key': m_key,
        'name': m.name(),
        }
    if current_mentor and m_key == current_mentor.key():
      choice['selected'] = True

    mentors_choices.append(choice)

  return mentors_choices

class AssignMentorFields(Template):
  """Template to render the fields necessary to assign a mentor to a proposal.
  """

  def __init__(self, data, current_mentor, action,
               all_mentors=None, possible_mentors=None):
    """Instantiates the template for Assign mentor buttons for org admin.

    data: The request data object
    current_mentor: Currently assigned mentor entity
    action: The form action URL to which the form should be posted
    all_mentors: Set of all the mentors that can be assigned to this entity
    possible_mentors: List of possible mentors that can be assigned to
        this entity.
    """
    super(AssignMentorFields, self).__init__(data)
    self.current_mentor = current_mentor
    self.action = action
    self.all_mentors = all_mentors
    self.possible_mentors = possible_mentors

  def context(self):
    context = {
        'action': self.action,
        }

    if self.possible_mentors:
      possible_mentors = db.get(self.possible_mentors)
      possible_mentor_choices = getMentorsChoicesToAssign(
          possible_mentors, self.current_mentor)
      context['possible_mentors'] = sorted(possible_mentor_choices)

    if self.all_mentors:
      if self.possible_mentors:
        self.all_mentors = set(self.all_mentors) - set(self.possible_mentors)
      all_mentors = db.get(self.all_mentors)
      all_mentor_choices = getMentorsChoicesToAssign(
          all_mentors, self.current_mentor)
      context['all_mentors'] = sorted(all_mentor_choices)

    return context

  def templatePath(self):
    return 'v2/modules/gsoc/_assign_mentor/base.html'
