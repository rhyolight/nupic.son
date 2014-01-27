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


from google.appengine.ext import db
from google.appengine.ext import ndb

from soc.tasks import mailer

from soc.modules.gci.logic.helper import notifications
from soc.modules.gci.models import comment as comment_model


def storeAndNotify(comment):
  """Stores and notifies those that are subscribed about a comment on a task.

  Args:
    comment: A GCIComment instance
  """
  db.run_in_transaction(storeAndNotifyTxn(comment))


def storeAndNotifyTxn(comment, task=None):
  """Returns a method to be run in a transaction to notify subscribers.

  Args:
    comment: A GCIComment instance
    task: optional GCITask instance that is the parent of the specified comment
  """
  if not task:
    task = comment.parent()
  elif task.key() != comment.parent_key():
    raise ValueError("The specified task must be the parent of the comment")

  author_key = ndb.Key.from_old_key(
      comment_model.GCIComment.created_by.get_value_for_datastore(comment))
  to_emails = []
  profiles = ndb.get_multi(map(ndb.Key.from_old_key, task.subscribers))
  for profile in profiles:
    if profile and ((not author_key) or profile.key.parent() != author_key):
      to_emails.append(profile.contact.email)

  # Send out an email to an entire organization when set.
  org = task.org
  if org.notification_mailing_list:
    to_emails.append(org.notification_mailing_list)

  context = notifications.getTaskCommentContext(task, comment, to_emails)
  sub_txn = mailer.getSpawnMailTaskTxn(context, parent=task)
  def txn():
    sub_txn()
    comment.put()

  return txn
