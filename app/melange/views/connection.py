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
    data, profile_key, organization, conversation_updater, message=None,
    notification_context_provider=None, recipients=None,
    org_role=connection_model.NO_ROLE, user_role=connection_model.NO_ROLE,
    org_admin=None):
  """Creates a new Connection entity, attach any messages provided by the
  initiator and send a notification email to the recipient(s).

  Args:
    data: RequestData object for the current request.
    profile_key: Profile key with which to connect.
    organization: Organization with which to connect.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
    message: User-provided message for the connection.
    context: The notification context method.
    notification_context_provider: A provider to obtain context of the
      notification email.
    recipients: List of one or more recipients for the notification email.
    org_role: Org role for the connection.
    user_role: User role for the connection.
    org_admin: profile entity of organization administrator who started
      the connection. Should be supplied only if the connection was initialized
      by organization.

  Returns:
    The newly created Connection entity.
  """
  profile = profile_key.get()

  can_create = connection_logic.canCreateConnection(profile, organization.key)

  if not can_create:
    raise exception.BadRequest(message=can_create.extra)
  else:
    # create the new connection.
    connection = connection_logic.createConnection(
        profile, organization.key, user_role, org_role)

    # handle possible role assignment
    if connection.getRole() == connection_model.MENTOR_ROLE:
      profile_logic.assignMentorRoleForOrg(profile, organization.key)
    elif connection.getRole() == connection_model.ORG_ADMIN_ROLE:
      profile_logic.assignOrgAdminRoleForOrg(profile, organization.key)

    # auto-generate a message indicated that the connection has been started
    if org_admin:
      # connection has been initialized by organization
      connection_logic.generateMessageOnStartByOrg(connection, org_admin)
    else:
      # connection has been initialized by user
      connection_logic.generateMessageOnStartByUser(connection.key)

    # attach any user-provided messages to the connection.
    if message:
      connection_logic.createConnectionMessage(
          connection.key, message, author_key=profile.key).put()

    # dispatch an email to the users.
    if notification_context_provider and recipients:
      notification_context = notification_context_provider.getContext(
          recipients, organization, profile, data.program, data.site,
          connection.key(), message)
      sub_txn = mailer.getSpawnMailTaskTxn(
          notification_context, parent=connection)
      sub_txn()

    # spawn task to update this user's messages
    conversation_updater.updateConversationsForProfile(profile)

    return connection

@db.transactional
def createAnonymousConnectionTxn(data, organization, org_role, email, message):
  """Create an AnonymousConnection so that an unregistered user can join
  an organization and dispatch an email to the newly Connected user.

  Args:
    data: RequestData for the current request.
    organization: Organization with which to connect.
    org_role: Role offered to the user.
    email: Email address of the user to which to send the notification.
    message: Any message provided by the organization to the user(s).

  Returns:
    Newly created AnonymousConnection entity.
  """
  anonymous_connection = connection_logic.createAnonymousConnection(
      org=organization, org_role=org_role, email=email)

  notification = notifications.anonymousConnectionContext(
      data=data, connection=anonymous_connection, email=email, message=message)
  sub_txn = mailer.getSpawnMailTaskTxn(
      notification, parent=anonymous_connection)
  sub_txn()

  return anonymous_connection

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
  # connection is retrieved and stored in datastore so that its last_modified
  # property is automatically updated by AppEngine
  connection = db.get(connection_key)

  message = connection_logic.createConnectionMessage(
      connection_key, content, author_key=profile_key)

  db.put([connection, message])

  # TODO(daniel): emails should be enqueued
  return message


@db.transactional
def handleUserNoRoleSelectionTxn(connection, conversation_updater):
  """Updates user role of the specified connection and all corresponding
  entities with connection_model.NO_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = db.get(connection.key())

  if connection.user_role != connection_model.NO_ROLE:
    old_user_role = connection.user_role

    connection.user_role = connection_model.NO_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.USER_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByUser(
        connection, old_user_role)

    db.put([connection, message])

    profile = db.get(connection.parent_key())
    org_key = connection_model.Connection.organization.get_value_for_datastore(
        connection)
    profile_logic.assignNoRoleForOrg(profile, org_key)

    conversation_updater.updateConversationsForProfile(profile)


@db.transactional
def handleUserRoleSelectionTxn(data, connection, conversation_updater):
  """Updates user role of the specified connection and all corresponding
  entities with connection_model.ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have a role for the organization prior to calling this function.

  Args:
    data: RequestData object for the current request.
    connection: connection entity.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = db.get(connection.key())

  if connection.user_role != connection_model.ROLE:
    old_user_role = connection.user_role

    connection.user_role = connection_model.ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.USER_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByUser(
        connection, old_user_role)

    db.put([connection, message])

    profile = db.get(connection.parent_key())
    org_key = connection_model.Connection.organization.get_value_for_datastore(
        connection)

    if connection.orgOfferedMentorRole():
      send_email = not profile.is_mentor
      profile_logic.assignMentorRoleForOrg(profile, org_key)
      # TODO(daniel): generate connection message
    elif connection.orgOfferedOrgAdminRole():
      send_email = not profile.is_mentor
      profile_logic.assignOrgAdminRoleForOrg(profile, org_key)
      # TODO(daniel): generate connection message
    else:
      # no role has been offered by organization
      send_email = False

    if send_email:
      message = 'TODO(daniel): supply actual message.'
      sendMentorWelcomeMail(data, profile, message)

    conversation_updater.updateConversationsForProfile(profile)


@db.transactional
def handleOrgNoRoleSelection(connection, org_admin, conversation_updater):
  """Updates organization role of the specified connection and all
  corresponding entities with connection_model.NO_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
    org_admin: profile entity of organization administrator who updates
               organization role for the connection.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = db.get(connection.key())

  if connection.org_role != connection_model.NO_ROLE:
    old_org_role = connection.org_role

    connection.org_role = connection_model.NO_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.ORG_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByOrg(
        connection, org_admin, old_org_role)

    db.put([connection, message])

    profile = db.get(connection.parent_key())
    org_key = connection_model.Connection.organization.get_value_for_datastore(
        connection)
    profile_logic.assignNoRoleForOrg(profile, org_key)

    conversation_updater.updateConversationsForProfile(profile)

    # TODO(daniel): generate connection message


@db.transactional
def handleMentorRoleSelection(connection, org_admin, conversation_updater):
  """Updates organization role of the specified connection and all
  corresponding entities with connection_model.MENTOR_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
    org_admin: profile entity of organization administrator who updates
               organization role for the connection.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """

  connection = db.get(connection.key())

  if connection.org_role != connection_model.MENTOR_ROLE:
    old_org_role = connection.org_role

    connection.org_role = connection_model.MENTOR_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.ORG_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByOrg(
        connection, org_admin, old_org_role)

    db.put([connection, message])

    if connection.userRequestedRole():
      profile = db.get(connection.parent_key())
      send_email = not profile.is_mentor

      org_key = (
          connection_model.Connection.organization.get_value_for_datastore(
              connection))
      profile_logic.assignMentorRoleForOrg(profile, org_key)

      conversation_updater.updateConversationsForProfile(profile)

      if send_email:
        pass
        # TODO(daniel): send actual welcome email


@db.transactional
def handleOrgAdminRoleSelection(connection, org_admin, conversation_updater):
  """Updates organization role of the specified connection and all
  corresponding entities with connection_model.ORG_ADMIN_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
    org_admin: profile entity of organization administrator who updates
               organization role for the connection.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = db.get(connection.key())

  if connection.org_role != connection_model.ORG_ADMIN_ROLE:
    old_org_role = connection.org_role

    connection.org_role = connection_model.ORG_ADMIN_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.ORG_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByOrg(
        connection, org_admin, old_org_role)

    db.put([connection, message])

    if connection.userRequestedRole():
      profile = db.get(connection.parent_key())
      send_email = not profile.is_mentor

      org_key = (
          connection_model.Connection.organization.get_value_for_datastore(
              connection))
      profile_logic.assignOrgAdminRoleForOrg(profile, org_key)

      conversation_updater.updateConversationsForProfile(profile)

      if send_email:
        pass
        # TODO(daniel): send actual welcome email


@db.transactional
def markConnectionAsSeenByOrg(connection_key):
  """Marks the specified connection as seen by organization.

  Args:
    connection: Connection key.
  """
  connection = db.get(connection_key)
  connection.seen_by_org = True
  connection.put()


@db.transactional
def markConnectionAsSeenByUser(connection_key):
  """Marks the specified connection as seen by organization.

  Args:
    connection: Connection key.
  """
  connection = db.get(connection_key)
  connection.seen_by_user = True
  connection.put()
