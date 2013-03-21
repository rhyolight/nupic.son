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

"""Helper functions for sending out notifications.
"""


from django.template import loader
from django.utils.translation import ugettext

from soc.logic import mail_dispatcher
from soc.logic.accounts import denormalizeAccount
from soc.tasks import mailer
from soc.views.helper.access_checker import isSet


DEF_INVITATION = ugettext(
    '[%(org)s] Invitation to become a %(role_verbose)s.')

DEF_NEW_REQUEST = ugettext(
    '[%(org)s] New request from %(requester)s to become a %(role_verbose)s')

DEF_NEW_CONNECTION = ugettext(
  'New connection to %(org)s' )

DEF_NEW_ANONYMOUS_CONNECTION = ugettext(
  'New Google Summer of Code Connection')

DEF_ACCEPTED_ORG = ugettext(
    '[%(org)s] Your organization application has been accepted.')

DEF_REJECTED_ORG = ugettext(
    '[%(org)s] Your organization application has been rejected.')

DEF_HANDLED_REQUEST_SUBJECT = ugettext(
    '[%(org)s] Request to become a %(role_verbose)s has been %(action)s')

DEF_HANDLED_INVITE_SUBJECT = ugettext(
    '[%(org)s] Invitation to become a %(role_verbose)s has been %(action)s')

DEF_MENTOR_WELCOME_MAIL_SUBJECT = ugettext('Welcome to %s')

DEF_ORG_INVITE_NOTIFICATION_TEMPLATE = \
    'soc/notification/invitation.html'

#TODO(dcrodman): This needs to be removed once connection is stable.
DEF_NEW_REQUEST_NOTIFICATION_TEMPLATE = \
    'soc/notification/new_request.html'

DEF_NEW_CONNECTION_NOTIFICATION_TEMPLATE = \
    'v2/modules/gsoc/notification/initiated_connection.html'

DEF_NEW_ANONYMOUS_CONNECTION_NOTIFICATION_TEMPLATE = \
    'v2/modules/gsoc/notification/anonymous_connection.html'

DEF_ACCEPTED_ORG_TEMPLATE = \
    'soc/notification/org_accepted.html'

DEF_REJECTED_ORG_TEMPLATE = \
    'soc/notification/org_rejected.html'

DEF_HANDLED_REQUEST_NOTIFICATION_TEMPLATE = \
    'soc/notification/handled_request.html'

DEF_HANDLED_INVITE_NOTIFICATION_TEMPLATE = \
    'soc/notification/handled_invite.html'

DEF_MENTOR_WELCOME_MAIL_TEMPLATE = \
    'soc/notification/mentor_welcome_mail.html'

def connectionContext(data, connection, receivers, message, is_user=False):
  """Sends out a notification email to all individuals involved in the newly 
  created connection.

  Args: 
    data: RequestData object with organization and user set
    connection: An instance of GSoCConnection.
    receivers: The email(s) of the org or user who is will be "receiving"
        the connection. should be the opposite of sender.
    message: The contents of the message field from the connection form.
    is_user: True if a user is the one who initiated the connection.
  Returns:
    A dictionary containing a context for the mail message to be sent to
    the receiver(s) regarding a new connection.
  """

  subject = DEF_NEW_CONNECTION % {'org' : connection.organization.name}
  request_url = data.redirect.show_connection(connection.parent(),
      connection).url(full=True)
 
  message_properties = {
      'org' : connection.organization.name, 
      'request_url' : request_url,
      'is_user' : is_user,
      'message' : message
  }
  template = DEF_NEW_CONNECTION_NOTIFICATION_TEMPLATE
  return getContext(data, receivers, message_properties, subject, template)

def anonymousConnectionContext(data, email, role, connection_hash, message):
  """Sends out a notification email to users who have neither user nor 
  profile entities alerting them that an org admin has attempted to 
  initiate a connection with them. 

  Args:
    data: A RequestData object for the connection views.
    email: Email address of the user meeting the above criteria.
    role: A string role ('mentor' or 'org_admin') to grant the
        user when they register.
    connection_hash: Hash of the AnonymousConnection object.
    message: The contents of the message field from the connection form.
  Returns:
    A dictionary containing a context for the mail message to be sent to
    the receiver(s) regarding a new anonymous connection.
  """

  assert isSet(data.profile)
  assert isSet(data.organization)

  url = data.redirect.profile_anonymous_connection(role, 
      connection_hash).url(full=True)

  message_properties = {
      'requester' : data.profile.link_id,
      'org' : data.organization.name,
      'role' : role,
      'url' : url,
      'message' : message
  }

  subject = DEF_NEW_ANONYMOUS_CONNECTION
  template = DEF_NEW_ANONYMOUS_CONNECTION_NOTIFICATION_TEMPLATE

  return getContext(data, email, message_properties, subject, template)

#TODO(dcrodman): This needs to be removed once connection is stable.
def inviteContext(data, invite):
  """Sends out an invite notification to the user the request is for.

  Args:
    data: a RequestData object with 'invite' and 'invite_profile' set.
  """

  assert isSet(data.invite_profile)

  # do not send notifications if the user has opted out
  if not data.invite_profile.notify_new_invites:
    return {}

  invitation_url = data.redirect.request(invite).url(full=True)

  edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'role_verbose' : invite.roleName(),
      'org': invite.org.name,
      'invitation_url': invitation_url,
      'profile_edit_link': edit_link,
  }

  subject = DEF_INVITATION % message_properties

  template = DEF_ORG_INVITE_NOTIFICATION_TEMPLATE

  to_email = data.invite_profile.email

  return getContext(data, [to_email], message_properties, subject, template)


#TODO(dcrodman): This needs to be removed once connection is stable.
def requestContext(data, request, admin_emails):
  """Sends out a notification to the persons who can process this Request.

  Args:
    request_entity: an instance of Request model.
  """

  assert isSet(data.organization)

  request_url = data.redirect.request(request).url(full=True)
  edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'requester': data.profile.name(),
      'role_verbose': request.roleName(),
      'org': request.org.name,
      'request_url': request_url,
      'profile_edit_link': edit_link,
      }

  subject = DEF_NEW_REQUEST % message_properties

  template = DEF_NEW_REQUEST_NOTIFICATION_TEMPLATE

  return getContext(data, admin_emails, message_properties, subject, template)


#TODO(dcrodman): This needs to be removed once connection is stable.
def handledRequestContext(data, status):
  """Sends a message that the request to get a role has been handled.

  Args:
    data: a RequestData object.
  """
  assert isSet(data.request_entity)
  assert isSet(data.requester_profile)

  # do not send notifications if the user has opted out
  if not data.requester_profile.notify_request_handled:
    return {}

  edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'role_verbose' : data.request_entity.roleName(),
      'org': data.request_entity.org.name,
      'action': status,
      'profile_edit_link': edit_link,
      }

  subject = DEF_HANDLED_REQUEST_SUBJECT % message_properties

  template = DEF_HANDLED_REQUEST_NOTIFICATION_TEMPLATE

  to_email = data.requester_profile.email

  # from user set to None to not leak who rejected it.
  return getContext(data, [to_email], message_properties, subject, template)


#TODO(dcrodman): This needs to be removed once connection is stable.
def handledInviteContext(data):
  """Sends a message that the invite to obtain a role has been handled.

  Args:
    data: a RequestData object.
  """

  assert isSet(data.invite)
  assert isSet(data.invited_profile)

  # do not send notifications if the user has opted out
  if not data.invited_profile.notify_invite_handled:
    return {}

  status = data.invite.status
  action = 'resubmitted' if status == 'pending' else status
  edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'role_verbose' : data.invite.roleName(),
      'org': data.invite.org.name,
      'action': action,
      'profile_edit_link': edit_link,
      }

  subject = DEF_HANDLED_INVITE_SUBJECT % message_properties

  template = DEF_HANDLED_INVITE_NOTIFICATION_TEMPLATE

  to_email = data.invited_profile.email

  # from user set to None to not leak who rejected it.
  return getContext(data, [to_email], message_properties, subject, template)


def getMentorWelcomeMailContext(profile, data, messages):
  """Sends a welcome email to mentors/org admins.

  Args:
    profile: Profile of the user to who will receive the welcome email.
    data: RequestData object.
    messages: ProgramMessages instance containing the message to be sent.

  Returns:
    Context that can be given to the mailer. If the context is empty no message
    was defined.
  """
  to = profile.email
  subject = DEF_MENTOR_WELCOME_MAIL_SUBJECT % (data.program.name)
  message = messages.mentor_welcome_msg

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


def getContext(data, receivers, message_properties, subject, template):
  """Sends out a notification to the specified user.

  Args:
    receivers: Email addresses to which the notification should be sent.
    message_properties : Message properties.
    subject : Subject of notification email.
    template : Template used for generating notification.
  Returns:
    A dictionary containing the context for a message to be sent to one
    or more recipients.
  """
  message_properties['sender_name'] = 'The %s Team' % (data.site.site_name)
  message_properties['program_name'] = data.program.name

  body = loader.render_to_string(template, dictionary=message_properties)

  if len(receivers) == 1:
    to = receivers[0]
    bcc = []
  else:
    to = []
    bcc = receivers

  return mailer.getMailContext(to, subject, body, bcc=bcc)
