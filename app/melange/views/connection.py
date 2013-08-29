# Copyright 2013 the Melange authors.
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

"""Module with Code In specific connection views."""

from google.appengine.ext import db

from melange.logic import connection as connection_logic
from melange.logic import profile as profile_logic
from melange.models import connection as connection_model
from melange.request import exception

from soc.logic.helper import notifications
from soc.tasks import mailer


def sendMentorWelcomeMail(data, profile, message):
  """Send out a welcome email to new mentors.

  Args:
    data: RequestData object for the current request.
    profile: profile entity to which to send emails.
    messages: message to be sent.
  """
  mentor_mail = notifications.getMentorWelcomeMailContext(
      profile, data, message)
  if mentor_mail:
    mailer.getSpawnMailTaskTxn(mentor_mail, parent=profile)()


@db.transactional
def createConnectionTxn(
    data, profile, organization, message, context, recipients,
    org_role=connection_model.NO_ROLE, user_role=connection_model.NO_ROLE):
  """Creates a new Connection entity, attach any messages provided by the
  initiator and send a notification email to the recipient(s).

  Args:
    data: RequestData object for the current request.
    profile: Profile with which to connect.
    organization: Organization with which to connect.
    message: User-provided message for the connection.
    context: The notification context method.
    recipients: List of one or more recipients for the notification email.
    org_state: Org state for the connection.
    user_state: User state for the connection.

  Returns:
    The newly created Connection entity.
  """
  if connection_logic.connectionExists(profile.parent(), organization):
    raise exception.Forbidden(
        message=connection_logic.CONNECTION_EXISTS_ERROR %
        (profile.name, organization.name))

  # create the new connection.
  new_connection = connection_logic.createConnection(
      profile=profile, org=organization,
      org_role=org_role, user_role=user_role)
  # attach any user-provided messages to the connection.
  if message:
    connection_logic.createConnectionMessage(
        connection=new_connection, author=profile, content=message)
  # dispatch an email to the user.
  notification = context(data=data, connection=new_connection,
      recipients=recipients, message=message)
  sub_txn = mailer.getSpawnMailTaskTxn(notification, parent=new_connection)
  sub_txn()

  return new_connection

@db.transactional
def createConnectionMessageTxn(connection_key, profile_key, content):
  """Creates a new connection message with the specified content
  for the specified connection.

  Args:
    connection_key: connection key.
    profile_key: profile key of a user who is an author of the comment.
    content: a string containing content of the message.

  Returns:
    a newly created ConnectionMessage entity.
  """
  message = connection_logic.createConnectionMessage(
      connection_key, profile_key, content)

  # TODO(daniel): emails should be enqueued
  return message

@db.transactional
def handleUserNoRoleSelectionTxn(connection):
  """Updates user role of the specified connection and all corresponding
  entities with connection_model.NO_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
  """
  connection = db.get(connection.key())
  connection.user_role = connection_model.NO_ROLE
  connection.put()

  profile = db.get(connection.parent_key())
  org_key = connection_model.Connection.organization.get_value_for_datastore(
      connection)
  profile_logic.assignNoRoleForOrg(profile, org_key)

  # TODO(daniel): generate connection message
