# Copyright 2008 the Melange authors.
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

"""Logic related to handling deletion of user accounts."""

from google.appengine.api import mail
from google.appengine.ext import db

from melange.appengine import system
from soc.logic import accounts
from soc.logic import user as user_logic

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models import comment as comment_model
from soc.modules.gci.models import task as task_model

ADMIN_REQUEST_EMAIL_SUBJEST = """
User %(url_id)s has requested account deletion.
"""

ADMIN_REQUEST_EMAIL_BODY = """
Dear application admin,

User %(name)s (%(email)s), whose username is %(url_id)s, has
requested their account to be deleted.
"""


def request_account_deletion(user):
  """Requests deletion of user's account from application administrators
  by sending them an email.

  This is a temporary method, until we have an automated solution.
  """
  account = accounts.getCurrentAccount(normalize=False)
  sender = system.getApplicationNoReplyEmail()

  subject = ADMIN_REQUEST_EMAIL_SUBJEST % {
      'url_id': user.url_id
      }
  body = ADMIN_REQUEST_EMAIL_BODY % {
      'name': user.name,
      'email': account.email(),
      'url_id': user.url_id,
      }

  mail.send_mail_to_admins(sender, subject, body)


def confirm_delete(profile):
  """Deletes the given profile entity and also the user entity if possible.

  1. Deletes the profile.
  2. Deletes the user entity if no other profiles exist for the user.
  3. Removes the user from task notification subscription lists
  4. Replaces GCITask created_by, modified_by, student and GCIComment
     created_by properties with dummy "melange_deleted_user" profile or user
     entity.

  This method implements a giant XG transaction, but should not take a long
  time because experience has shown that there won't be too much data to
  modify or delete.

  Args:
    profile: GCIProfile entity of the user.
  """
  profile_key = profile.key()

  # Cannot delete the user entity if the user has other profiles, so set it
  # to False in that case.
  user_delete = not (profile_logic.hasOtherGCIProfiles(profile) or
                     profile_logic.hasOtherGCIProfiles(profile))

  task_sub_q = task_model.GCITask.all().filter('subscribers', profile)
  task_sub_remove_list = []
  for task in task_sub_q.run():
    task_sub_remove_list.append(task)

  tasks_created_by_q = task_model.GCITask.all().filter('created_by', profile)
  task_created_list = []
  for task in tasks_created_by_q.run():
    task_created_list.append(task)

  tasks_modified_by_q = task_model.GCITask.all().filter('modified_by', profile)
  task_modified_list = []
  for task in tasks_modified_by_q.run():
    task_modified_list.append(task)

  tasks_student_q = task_model.GCITask.all().filter('student', profile)
  task_student_list = []
  for task in tasks_student_q.run():
    task_student_list.append(task)

  comments_created_by_q = comment_model.GCIComment.all().filter(
      'created_by', profile.user)
  comments_created_by_list = []
  for comment in comments_created_by_q.run():
    comments_created_by_list.append(comment)

  dummy_user = user_logic.getOrCreateDummyMelangeDeletedUser()
  dummy_profile = profile_logic.getOrCreateDummyMelangeDeletedProfile(
      profile.program)

  options = db.create_transaction_options(xg=True)

  def delete_account_txn():
    entities_to_save = set([])
    entities_to_del = set([])

    # The batch size for query.run() is 20, in most of the cases we have
    # seen so far the user had a few tasks with subscriptions, created_by,
    # modified_by etc., so this should still be single datastore hits per
    # loop. Also, by running the query outside the transaction we may run
    # into situations of user subscribing to the task or creating or modifying
    # tasks or performing another activity after this batch fetch. However,
    # the chances of that happening is very low and can be traded-off for
    # the bigger problem of half run transactions.
    for task in task_sub_remove_list:
      task.subscribers.remove(profile_key)
      entities_to_save.add(task)

    for task in task_created_list:
      task.created_by = dummy_profile
      entities_to_save.add(task)

    for task in task_modified_list:
      task.modified_by = dummy_profile
      entities_to_save.add(task)

    for task in task_student_list:
      task.student = dummy_profile
      entities_to_save.add(task)

    for comment in comments_created_by_list:
      comment.created_by = dummy_user
      entities_to_save.add(comment)

    if profile.student_info:
      entities_to_del.add(profile.student_info)
      entities_to_del.add(profile)

    if user_delete:
      entities_to_del.add(profile.parent())

    db.put(entities_to_save)
    db.delete(entities_to_del)

  db.run_in_transaction_options(options, delete_account_txn)
