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

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import logging
import time

from django.template import loader
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import dicts
from soc.tasks import mailer
from soc.views.helper.access_checker import isSet


DEF_INVITATION_MSG_FMT = ugettext(
    '[%(group)s] Invitation to become a %(role_verbose)s.')

DEF_NEW_REQUEST_MSG_FMT = ugettext(
    '[%(group)s] New request from %(requester)s to become a %(role_verbose)s')

DEF_NEW_ORG_MSG_FMT = ugettext(
    '[%(group)s] Your organization application has been accepted.')

DEF_NEW_PROPOSAL_SUBJECT_FMT = ugettext(
    '[%(group)s] New proposal by %(proposer_name)s: %(proposal_name)s')

DEF_UPDATED_PROPOSAL_SUBJECT_FMT = ugettext(
    '[%(group)s] Update by %(proposer_name)s to proposal: %(proposal_name)s')

DEF_NEW_REVIEW_SUBJECT_FMT = ugettext(
    '[%(group)s] New %(review_visibility)s review on %(reviewed_name)s '
    '(%(proposer_name)s) by %(reviewer_name)s')

DEF_HANDLED_REQUEST_SUBJECT_FMT = ugettext(
    '[%(group)s] Request to become a %(role_verbose)s has been %(action)s')

DEF_HANDLED_INVITE_SUBJECT_FMT = ugettext(
    '[%(group)s] Invitation to become a %(role_verbose)s has been %(action)s')

DEF_GROUP_INVITE_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/invitation.html'

DEF_NEW_REQUEST_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/new_request.html'

DEF_NEW_PROPOSAL_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/new_proposal.html'

DEF_UPDATED_PROPOSAL_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/updated_proposal.html'

DEF_NEW_REVIEW_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/new_review.html'

DEF_NEW_ORG_TEMPLATE = \
    'v2/soc/notifications/org_accepted.html'

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

  message_properties = {
      'role_verbose' : invite.roleName(),
      'group': invite.group.name,
      'invitation_url': invitation_url,
  }

  subject = DEF_INVITATION_MSG_FMT % message_properties

  template = DEF_GROUP_INVITE_NOTIFICATION_TEMPLATE

  to_email = data.invite_profile.email

  return getContext(data, [to_email], message_properties, subject, template)


def requestContext(data, request, admin_emails):
  """Sends out a notification to the persons who can process this Request.

  Args:
    request_entity: an instance of Request model
  """

  assert isSet(data.organization)

  from soc.logic.helper import notifications

  # get the users who should get the notification
  to_users = []

  request_url = data.redirect.request(request).url(full=True)

  message_properties = {
      'requester': data.profile.name(),
      'role_verbose': request.roleName(),
      'group': request.group.name,
      'request_url': request_url,
      }

  subject = DEF_NEW_REQUEST_MSG_FMT % message_properties

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

  message_properties = {
      'role_verbose' : data.request_entity.roleName(),
      'group': data.request_entity.group.name,
      'action': status,
      }

  subject = DEF_HANDLED_REQUEST_SUBJECT_FMT % message_properties

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

  logging.warning("hIC:enter")

  # do not send notifications if the user has opted out
  if not data.invited_profile.notify_invite_handled:
    logging.warning("hIC:abort")
    return {}

  status = data.invite.status
  action = 'resubmitted' if status == 'pending' else status

  message_properties = {
      'role_verbose' : data.invite.roleName(),
      'group': data.invite.group.name,
      'action': action,
      }

  subject = DEF_HANDLED_INVITE_SUBJECT_FMT % message_properties

  template = DEF_HANDLED_INVITE_NOTIFICATION_TEMPLATE

  to_email = data.invited_profile.email

  # from user set to None to not leak who rejected it.
  return getContext(data, [to_email], message_properties, subject, template)


def newOrganizationContext(data):
  """Sends out an invite notification to the applicant of the Organization.

  Args:
    data: a RequestData object
  """

  url = data.redirect.survey().urlOf('gsoc_org_app_apply', full=True)

  message_properties = {
      'url': url,
      'program_name': data.program.name,
      'group': data.organization.name,
  }

  subject = DEF_NEW_ORG_MSG_FMT % message_properties

  template = DEF_NEW_ORG_TEMPLATE

  roles = [entity.main_admin, entity.backup_admin]

  emails = [i.email for i in roles if i]

  return getContext(data, emails, message_properties, subject, template)


def newProposalContext(data, proposal, to_emails):
  """Sends out a notification to alert the user of a new comment.

  Args:
    data: a RequestData object
  """
  data.redirect.review(proposal.key().id(), data.user.link_id)
  proposal_notification_url = data.redirect.urlOf('review_gsoc_proposal', full=True)
  
  proposal_name = proposal.title

  message_properties = {
      'proposal_notification_url': proposal_notification_url,
      'proposer_name': data.profile.name(),
      'proposal_name': proposal.title,
      'proposal_content': proposal.content,
      'group': proposal.org.name,
  }

  # determine the subject
  subject = DEF_NEW_PROPOSAL_SUBJECT_FMT % message_properties

  template = DEF_NEW_PROPOSAL_NOTIFICATION_TEMPLATE

  return getContext(data, to_emails, message_properties, subject, template)


def updatedProposalContext(data, proposal, to_emails):
  """Sends out a notification to alert the user of an updated proposal.

  Args:
    data: a RequestData object
  """
  assert isSet(data.organization)

  data.redirect.review(proposal.key().id(), data.user.link_id)
  proposal_notification_url = data.redirect.urlOf('review_gsoc_proposal', full=True)

  proposal_name = proposal.title

  message_properties = {
      'proposal_notification_url': proposal_notification_url,
      'proposer_name': data.profile.name(),
      'proposal_name': proposal.title,
      'proposal_content': proposal.content,
      'group': data.organization.name,
  }

  # determine the subject
  subject = DEF_UPDATED_PROPOSAL_SUBJECT_FMT % message_properties

  template = DEF_UPDATED_PROPOSAL_NOTIFICATION_TEMPLATE

  return getContext(data, to_emails, message_properties, subject, template)


def newCommentContext(data, comment, to_emails):
  """Sends out a notification to alert the user of a new comment.

  Args:
    data: a RequestData object
  """
  assert isSet(data.proposal)
  assert isSet(data.proposer)

  review_notification_url = data.redirect.comment(comment, full=True)
  
  review_type = 'private' if comment.is_private else 'public'
  reviewed_name = data.proposal.title

  message_properties = {
      'review_notification_url': review_notification_url,
      'reviewer_name': comment.author.name(),
      'reviewed_name': reviewed_name,
      'review_content': comment.content,
      'review_visibility': review_type,
      'proposer_name': data.proposer.name(),
      'group': data.proposal.org.name,
      }

  # determine the subject
  subject = DEF_NEW_REVIEW_SUBJECT_FMT % message_properties

  template = DEF_NEW_REVIEW_NOTIFICATION_TEMPLATE

  if data.proposer.notify_public_comments and not comment.is_private:
    to_emails.append(data.proposer.email)

  return getContext(data, to_emails, message_properties, subject, template)


def getContext(data, receivers, message_properties, subject, template):
  """Sends out a notification to the specified user.

  Args:
    receivers: email addresses to which the notification should be sent
    message_properties : message properties
    subject : subject of notification email
    template : template used for generating notification
  """

  edit_link = data.redirect.program().urlOf('edit_gsoc_profile', full=True)

  message_properties['sender_name'] = 'The %s Team' % (data.site.site_name)
  message_properties['program_name'] = data.program.name
  message_properties['profile_edit_link'] = edit_link

  body = loader.render_to_string(template, dictionary=message_properties)

  if len(receivers) == 1:
    to = receivers[0]
    bcc = []
  else:
    to = []
    bcc = receivers

  return mailer.getMailContext(to, subject, body, bcc=bcc)
