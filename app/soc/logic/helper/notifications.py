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

"""Helper functions for sending out notifications."""

from django.template import loader
from django.utils.translation import ugettext

from soc.logic import mail_dispatcher
from soc.logic.accounts import denormalizeAccount
from soc.tasks import mailer
from soc.views.helper.access_checker import isSet


DEF_NEW_USER_CONNECTION = ugettext(
    'New connection for %(org)s' )

DEF_NEW_ORG_CONNECTION = ugettext(
    'New connection from %(org)s')

DEF_NEW_ANONYMOUS_CONNECTION = ugettext(
    'New Google Summer of Code Connection')

DEF_ACCEPTED_ORG = ugettext(
    '[%(org)s] Your organization application has been accepted.')

DEF_REJECTED_ORG = ugettext(
    '[%(org)s] Your organization application has been rejected.')

DEF_MENTOR_WELCOME_MAIL_SUBJECT = ugettext('Welcome to %s')

# TODO(nathaniel): "gsoc" reference outside of app/soc/modules/gsoc.
DEF_NEW_USER_CONNECTION_NOTIFICATION_TEMPLATE = \
    'modules/gsoc/notification/initiated_user_connection.html'

# TODO(nathaniel): "gsoc" reference outside of app/soc/modules/gsoc.
DEF_NEW_ORG_CONNECTION_NOTIFICATION_TEMPLATE = \
    'modules/gsoc/notification/initiated_org_connection.html'

# TODO(nathaniel): "gsoc" reference outside of app/soc/modules/gsoc.
DEF_NEW_ANONYMOUS_CONNECTION_NOTIFICATION_TEMPLATE = \
    'modules/gsoc/notification/anonymous_connection.html'

DEF_ACCEPTED_ORG_TEMPLATE = \
    'soc/notification/org_accepted.html'

DEF_REJECTED_ORG_TEMPLATE = \
    'soc/notification/org_rejected.html'

DEF_MENTOR_WELCOME_MAIL_TEMPLATE = \
    'soc/notification/mentor_welcome_mail.html'

def getContext(data, receivers, message_properties, subject, template):
  """Sends out a notification to the specified user.

  Args:
    receivers: Email addresses to which the notification should be sent.
    message_properties: Message properties.
    subject: Subject of notification email.
    template: Template used for generating notification.
  Returns:
    A dictionary containing the context for a message to be sent to one
    or more recipients.
  """
  message_properties['sender_name'] = 'The %s Team' % (data.site.site_name)
  message_properties['program_name'] = data.program.name

  body = loader.render_to_string(template, dictionary=message_properties)

  # TODO(nathaniel): "to" can be a list of email addresses or a single
  # email address? Is that right? The documentation of mailer.getMailContext
  # affords no answer.
  if len(receivers) == 1:
    to = receivers[0]
    bcc = []
  else:
    to = []
    bcc = receivers

  return mailer.getMailContext(to, subject, body, bcc=bcc)

def getDefaultContext(request_data, emails, subject, extra_context=None):
  """Generate a dictionary with a default context.

  Returns:
    A dictionary with the default context for the emails that are sent
    in this module.
  """
  default_context  = {}
  default_context['sender_name'] = 'The %s Team' % (
      request_data.site.site_name)
  default_context['program_name'] = request_data.program.name
  default_context['subject'] = subject

  sender_name, sender = mail_dispatcher.getDefaultMailSender()
  default_context['sender_name'] = sender_name
  default_context['sender'] = sender

  if len(emails) == 1:
    default_context['to'] = emails[0]
  else:
    default_context['bcc'] = emails

  if extra_context:
    default_context.update(extra_context)

  return default_context


class StartConnectionByUserContextProvider(object):
  """Provider of notification email content to be sent after a new connection
  has been started by a user.
  """

  def __init__(self, linker, url_names):
    """Initializes a new instance of this class.

    Args:
      linker: links.Linker to be used to generate URLs.
      url_names: urls.UrlNames object containing registered names of URLs.
    """
    self._linker = linker
    self._url_names = url_names

  def getContext(
      self, emails, data, org, profile, connection_key, message):
    """Provides notification context of an email to send out when a new
    connection is started by a user.

    Args:
      emails: List of email addresses to which the notification should be sent.
      data: request_data.RequestData for the current request.
      org: Organization entity.
      profile: Profile entity.
      connection_id: Numerical identifier of the newly started connection.
      message: Optional message to be sent along with the connection.

    Returns:
      A dictionary containing the context for a message to be sent.
    """
    subject = DEF_NEW_USER_CONNECTION % {'org': org.name}
    connection_url = self._linker.userId(
        profile, connection_key.id(), self._url_names.CONNECTION_MANAGE_AS_ORG)

    message_properties = {
        'connection_url': connection_url,
        'name': profile.name(),
        'org_name': org.name,
        'message': message,
        }

    template = DEF_NEW_USER_CONNECTION_NOTIFICATION_TEMPLATE
    return getContext(data, emails, message_properties, subject, template)


class StartConnectionByOrgContextProvider(object):
  """Provider of notification email content to be sent after a new connection
  has been started by an organization.
  """

  def __init__(self, linker, url_names):
    """Initializes a new instance of this class.

    Args:
      linker: links.Linker to be used to generate URLs.
      url_names: urls.UrlNames object containing registered names of URLs.
    """
    self._linker = linker
    self._url_names = url_names

  def getContext(
      self, emails, data, org, profile, connection_key, message):
    """Provides notification context of an email to send out when a new
    connection is started by an organization.

    Args:
      emails: List of email addresses to which the notification should be sent.
      data: request_data.RequestData for the current request.
      org: Organization entity.
      profile: Profile entity.
      connection_id: Numerical identifier of the newly started connection.
      message: Optional message to be sent along with the connection.

    Returns:
      A dictionary containing the context for a message to be sent.
    """
    subject = DEF_NEW_ORG_CONNECTION % {'org': org.name}
    connection_url = self._linker.userId(
        profile, connection_key.id(),
        self._url_names.CONNECTION_MANAGE_AS_USER)

    message_properties = {
        'connection_url': connection_url,
        'name': profile.name(),
        'org_name': org.name,
        'message': message,
        }

    template = DEF_NEW_ORG_CONNECTION_NOTIFICATION_TEMPLATE
    return getContext(data, emails, message_properties, subject, template)


def userConnectionContext(data, connection, recipients, message):
  """Send out a notification email to the organization administrators for the
  given org when a user opens a connection with the organization.

  Args:
    data: RequestData object with organization and user set.
    connection: The new instance of Connection.
    recipients: The email(s) of the org admins for the org.
    message: The contents of the message field from the connection form.
  Returns:
    A dictionary containing a context for the mail message to be sent to
    the recipients regarding a new connection.
  """

  subject = DEF_NEW_USER_CONNECTION % {'org' : connection.organization.name}

  # TODO(daniel): add actual connection URL
  # connection_url = data.redirect.show_user_connection(connection).url(full=True)

  message_properties = {
      'connection_url' : '',
      'name' : connection.parent().name(),
      'org_name' : connection.organization.name,
      'message' : message,
      }
  template = DEF_NEW_USER_CONNECTION_NOTIFICATION_TEMPLATE
  return getContext(data, recipients, message_properties, subject, template)

def orgConnectionContext(data, connection, recipients, message):
  """Send out a notification email to a user with whom an org admin opened
  a new connection.

  Args:
    data: RequestData object with organization and user set.
    connection: The new instance of Connection.
    recipients: List containing the email address of the user. This is a list
      because in the connection view module in either program receives this
      or userConnectionContext as an argument and the other must receive a
      list of recipients rather than a string.
    message: The contents of the message field from the connection form.
  Returns:
    A dictionary containing a context for the mail message to be sent to
    the recipient regarding a new connection.
  """

  subject = DEF_NEW_ORG_CONNECTION % {'org' : connection.organization.name}
  connection_url = data.redirect.show_org_connection(connection).url(full=True)

  message_properties = {
      'connection_url' : connection_url,
      'name' : connection.parent().name(),
      'org_name' : connection.organization.name,
      'role' : connection.getRole(),
      'message' : message
      }
  template = DEF_NEW_ORG_CONNECTION_NOTIFICATION_TEMPLATE
  return getContext(data, recipients, message_properties, subject, template)

def anonymousConnectionContext(data, email, connection, message):
  """Sends out a notification email to users who have neither user nor
  profile entities alerting them that an org admin has attempted to
  initiate a connection with them.

  Args:
    data: A RequestData object for the connection views.
    email: Email address of the user meeting the above criteria.
    connection: A AnonymousConnection placeholder object.
    message: The contents of the message field from the connection form.
  Returns:
    A dictionary containing a context for the mail message to be sent to
    the receiver(s) regarding a new anonymous connection.
  """
  url = data.redirect.profile_anonymous_connection(
      role=connection.org_role, token=connection.token).url(full=True)

  message_properties = {
      'org_name' : connection.parent().name,
      'role' : connection.getRole(),
      'message' : message,
      'url' : url
      }

  subject = DEF_NEW_ANONYMOUS_CONNECTION
  template = DEF_NEW_ANONYMOUS_CONNECTION_NOTIFICATION_TEMPLATE

  return getContext(data, email, message_properties, subject, template)


def getMentorWelcomeMailContext(profile, data, message):
  """Sends a welcome email to mentors/org admins.

  Args:
    profile: Profile of the user to who will receive the welcome email.
    data: RequestData object.
    messages: message to be sent.

  Returns:
    Context that can be given to the mailer. If the context is empty no message
    was defined.
  """
  to = profile.email
  subject = DEF_MENTOR_WELCOME_MAIL_SUBJECT % (data.program.name)

  if not message:
    return {}

  context = {
    'msg_content': message
  }

  template = DEF_MENTOR_WELCOME_MAIL_TEMPLATE

  return getContext(data, [to], context, subject, template)


def orgAppContext(data, record, new_status, apply_url):
  """Sends out an invite notification to the applicant of the Organization.

  Args:
    data: a RequestData object.
    record: an OrgAppRecord.
    new_status: the new status that should be assigned to the record.
    apply_url: Full URL to the org profile create page for accepted orgs.
  """

  context = {
      'url': apply_url + '?org_id=' + record.org_id,
      'org': record.name,
      }

  messages = data.program.getProgramMessages()

  if new_status == 'accepted':
    subject = DEF_ACCEPTED_ORG % context
    template_string = messages.accepted_orgs_msg
  else:
    subject = DEF_REJECTED_ORG % context
    template_string = messages.rejected_orgs_msg
  context['template_string'] = template_string

  roles = [record.main_admin, record.backup_admin]
  emails = [denormalizeAccount(i.account).email() for i in roles if i]

  context = getDefaultContext(data, emails, subject, context)

  return context
