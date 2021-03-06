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

from google.appengine.ext import ndb

from soc.views import template


def getMentorsChoicesToAssign(mentors, current_mentor=None):
  """Returns a list of dictionaries containing the mentor key and mentor name.

  Args:
    mentors: List of potential mentor entities whose Django style choices
        must be returned
    current_mentor: Key of currently assigned mentor key

  Returns:
    A list of dictionaries containing the mentor key (at key "key") and
      mentor name (at key "name"). If a current_mentor is passed and
      matched among the mentors, its dictionary will have key "selected"
      mapped to True.
  """
  # construct a choice list for all the mentors in possible mentors list
  mentors_choices = []
  for mentor in mentors:
    choice = {
        'key': mentor.key,
        'name': mentor.public_name,
        }
    if current_mentor and mentor.key == current_mentor:
      choice['selected'] = True

    mentors_choices.append(choice)

  return mentors_choices

class AssignMentorFields(template.Template):
  """Template to render the fields needed to assign a mentor to a proposal."""

  def __init__(self, data, current_mentors, action,
               all_mentors=None, possible_mentors=None,
               mentor_required=False, allow_multiple=False):
    """Instantiates the template for Assign mentor buttons for org admin.

    data: The request data object
    current_mentors: List of Keys of currently assigned mentors to the project
    action: The form action URL to which the form should be posted
    all_mentors: Set of all the mentors that can be assigned to this entity
    possible_mentors: List of possible mentors that can be assigned to
        this entity.
    mentor_required: True if org admin is not allowed to unassign a mentor.
    allow_multiple: True if "Add new" link for assigning multiple mentors should
        be rendered.
    """
    super(AssignMentorFields, self).__init__(data)
    self.current_mentors = current_mentors
    self.action = action
    self.all_mentors = all_mentors
    self.possible_mentors = possible_mentors
    self.mentor_required = mentor_required
    self.allow_multiple = allow_multiple

  def _getMentorContext(self, current_mentor=None):
    """Returns the context for assigning mentors along with the current state.

    Args:
      current_mentor: Currently assigned mentor key to be set as initial value
    """
    mentor_context = {}
    if self.possible_mentors:
      possible_mentors = ndb.get_multi(
          map(ndb.Key.from_old_key, self.possible_mentors))
      possible_mentor_choices = getMentorsChoicesToAssign(
          possible_mentors, current_mentor=current_mentor)
      mentor_context['possible_mentors'] = sorted(
          possible_mentor_choices, key=lambda c: c.get('name', ''))

    if self.all_mentors:
      if self.possible_mentors:
        self.all_mentors = set(self.all_mentors) - set(self.possible_mentors)
      all_mentors = ndb.get_multi(self.all_mentors)
      all_mentor_choices = getMentorsChoicesToAssign(
          all_mentors, current_mentor=current_mentor)
      mentor_context['all_mentors'] = sorted(
          all_mentor_choices, key=lambda c: c.get('name', ''))

    return mentor_context

  def context(self):
    if self.current_mentors:
      # add a select drop down context for each assigned mentor with that
      # mentor set as initial value
      mentors = [self._getMentorContext(current_mentor=current_mentor)
                 for current_mentor in self.current_mentors]
    else:
      # if there are no mentors assigned at all render a single drop down
      # without any initial mentor set
      mentors = [self._getMentorContext()]

    return {
        'action': self.action,
        'mentor_required': self.mentor_required,
        'mentors': mentors,
        'allow_multiple': self.allow_multiple,
        }

  def templatePath(self):
    return 'modules/gsoc/_assign_mentor/base.html'
