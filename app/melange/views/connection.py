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
from melange.models import connection as connection_model
from melange.request import exception

from soc.tasks import mailer


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
