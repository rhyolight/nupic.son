#!/usr/bin/env python2.5
#
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
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext

from soc.logic import mail_dispatcher
from soc.logic.accounts import denormalizeAccount
from soc.tasks import mailer
from soc.views.helper.access_checker import isSet


DEF_INVITATION = ugettext(
    '[%(org)s] Invitation to become a %(role_verbose)s.')

DEF_NEW_REQUEST = ugettext(
    '[%(org)s] New request from %(requester)s to become a %(role_verbose)s')

DEF_ACCEPTED_ORG = ugettext(
    '[%(org)s] Your organization application has been accepted.')

DEF_REJECTED_ORG = ugettext(
    '[%(org)s] Your organization application has been rejected.')

DEF_HANDLED_REQUEST_SUBJECT = ugettext(
    '[%(org)s] Request to become a %(role_verbose)s has been %(action)s')

DEF_HANDLED_INVITE_SUBJECT = ugettext(
    '[%(org)s] Invitation to become a %(role_verbose)s has been %(action)s')

DEF_ORG_INVITE_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/invitation.html'

DEF_NEW_REQUEST_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/new_request.html'

DEF_ACCEPTED_ORG_TEMPLATE = \
    'v2/soc/notification/org_accepted.html'

DEF_REJECTED_ORG_TEMPLATE = \
    'v2/soc/notification/org_rejected.html'

DEF_HANDLED_REQUEST_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/handled_request.html'

DEF_HANDLED_INVITE_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/handled_invite.html'


def inviteContext(data, invite):
  """Sends out an invite notification to the user the request is for.

  Args:
    data: a RequestData object with 'invite' and 'invite_profile' set
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


def requestContext(data, request, admin_emails):
  """Sends out a notification to the persons who can process this Request.

  Args:
    request_entity: an instance of Request model
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


def handledRequestContext(data, status):
  """Sends a message that the request to get a role has been handled.

  Args:
    data: a RequestData object
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


def handledInviteContext(data):
  """Sends a message that the invite to obtain a role has been handled.

  Args:
    data: a RequestData object
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


def orgAppContext(data, record, new_status, apply_url):
  """Sends out an invite notification to the applicant of the Organization.

  Args:
    data: a RequestData object
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


def getContext(data, receivers, message_properties, subject, template):
  """Sends out a notification to the specified user.

  Args:
    receivers: email addresses to which the notification should be sent
    message_properties : message properties
    subject : subject of notification email
    template : template used for generating notification
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
