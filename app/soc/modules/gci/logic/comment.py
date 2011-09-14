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

"""GCIComment logic methods.
"""

__authors__ = [
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from google.appengine.ext import db


def storeAndNotify(comment):
  """Stores and notifies those that are subscribed about a comment on a task.

  Args:
    comment: A GCIComment instance
  """
  task = comment.parent()

  # TODO(ljvderijk): Only subscribers should be notified, maybe skip the user
  # who made the comment.
  to_emails = []

  #context = notifications.newCommentContext(data, comment, to_emails)
  #sub_txn = mailer.getSpawnMailTaskTxn(context, parent=comment)
  def create_comment_txn():
    #sub_txn()
    comment.put()
    return comment

  db.run_in_transaction(create_comment_txn)
