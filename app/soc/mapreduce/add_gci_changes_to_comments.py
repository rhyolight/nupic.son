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


"""MapReduce to populate the changes property to the action comments for
GCI 2011 comments.
"""


from google.appengine.ext.mapreduce import context
from google.appengine.ext.mapreduce import operation

from django.utils.translation import ugettext

from soc.modules.gci.models.program import GCIProgram


ACTION_TITLES = {
    'Task Claimed': [ugettext('User-Student'),
                     ugettext('Action-Claim Requested'),
                     ugettext('Status-ClaimRequested')],
    'Task Assigned': [ugettext('User-Mentor'),
                      ugettext('Action-Claim Accepted'),
                      ugettext('Status-Claimed')],
    'Claim Removed': [ugettext('User-Student'),
                      ugettext('Action-Withdrawn'),
                      ugettext('Status-Reopened')],
    'Ready for review': [ugettext('User-Student'),
                         ugettext('Action-Submitted work'),
                         ugettext('Status-NeedsReview')],
    'Task Needs More Work': [ugettext('User-Mentor'),
                             ugettext('Action-Requested more work'),
                             ugettext('Status-NeedsWork')],
    'Initial Deadline passed': [ugettext('User-MelangeAutomatic'),
                                ugettext('Action-Warned for action'),
                                ugettext('Status-ActionNeeded')],
    'No more Work can be submitted': [ugettext('User-MelangeAutomatic'),
                                      ugettext('Action-Deadline passed'),
                                      ugettext('Status-NeedsReview')],
    'Task Closed': [ugettext('User-Mentor'),
                    ugettext('Action-Closed the task'),
                    ugettext('Status-Closed')],
    'Deadline extended': [ugettext('User-Mentor'),
                          ugettext('Action-Deadline extended'),
                          ugettext('Status-Not Inferable')
                          ],
    # User can be either mentor or melange automatic system
    # Action can be one of Claim Rejected from ClaimRequested/Reopened
    # from other states/Forcibly Reopened from NeedsWork and Claimed
    'Task Reopened': [ugettext('User-Mentor'),
                      ugettext('Action-Task Reopened'),
                      ugettext('Status-Not Inferable')
                      ]
    }


def process(comment):
  ctx = context.get()
  params = ctx.mapreduce_spec.mapper.params
  program_key = params['program_key']

  program = GCIProgram.get_by_key_name(program_key)

  if comment.parent().program.key() != program.key():
    yield operation.counters.Increment("prev_program_comment_not_converted")
    return

  if comment.title not in ACTION_TITLES:
    yield operation.counters.Increment("user_comment_not_converted")
    return

  comment.changes = ACTION_TITLES[comment.title]

  yield operation.db.Put(comment)
  yield operation.counters.Increment("action_comment_converted")
