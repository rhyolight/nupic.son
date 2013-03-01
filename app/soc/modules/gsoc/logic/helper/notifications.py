# Copyright 2012 the Melange authors.
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

"""Notifications for the GSoC module."""

from django.utils.translation import ugettext

from soc.logic.helper.notifications import getContext
from soc.views.helper.access_checker import isSet

DEF_NEW_PROPOSAL_SUBJECT = ugettext(
    '[%(org)s] New proposal by %(proposer_name)s: %(proposal_name)s')

DEF_UPDATED_PROPOSAL_SUBJECT = ugettext(
    '[%(org)s] Update by %(proposer_name)s to proposal: %(proposal_name)s')

DEF_NEW_SLOT_TRANSFER_SUBJECT = ugettext(
    '[%(org)s] New slot transfer request by %(org_name)s.')

DEF_UPDATE_SLOT_TRANSFER_SUBJECT = ugettext(
    '[%(org)s] Slot transfer request updated by %(org_name)s.')

DEF_NEW_REVIEW_SUBJECT = ugettext(
    '[%(org)s] New %(review_visibility)s review on %(reviewed_name)s '
    '(%(proposer_name)s)')

DEF_NEW_CONNECTION_MESSAGE_SUBJECT = ugettext(
    '[%(org)s] New message on connection.')

DEF_NEW_PROPOSAL_NOTIFICATION_TEMPLATE = \
    'soc/notification/new_proposal.html'

DEF_UPDATED_PROPOSAL_NOTIFICATION_TEMPLATE = \
    'soc/notification/updated_proposal.html'

DEF_SLOT_TRANSFER_NOTIFICATION_TEMPLATE = \
    'soc/notification/slot_transfer.html'

DEF_NEW_REVIEW_NOTIFICATION_TEMPLATE = \
    'soc/notification/new_review.html'

DEF_NEW_CONNECTION_MESSAGE_NOTIFICATION_TEMPLATE = \
    'v2/soc/notification/new_connection_message.html'


def newProposalContext(data, proposal, to_emails):
  """Sends out a notification to alert the user of a new comment.

  Args:
    data: a RequestData object.
  """
  data.redirect.review(proposal.key().id(), data.user.link_id)
  proposal_notification_url = data.redirect.urlOf('review_gsoc_proposal', full=True)
  edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'proposal_notification_url': proposal_notification_url,
      'proposer_name': data.profile.name(),
      'proposal_name': proposal.title,
      'proposal_content': proposal.content,
      'org': proposal.org.name,
      'profile_edit_link': edit_link,
  }

  # determine the subject
  subject = DEF_NEW_PROPOSAL_SUBJECT % message_properties

  template = DEF_NEW_PROPOSAL_NOTIFICATION_TEMPLATE

  return getContext(data, to_emails, message_properties, subject, template)


def updatedProposalContext(data, proposal, to_emails):
  """Sends out a notification to alert the user of an updated proposal.

  Args:
    data: a RequestData object.
  """
  assert isSet(data.organization)

  data.redirect.review(proposal.key().id(), data.user.link_id)
  proposal_notification_url = data.redirect.urlOf('review_gsoc_proposal', full=True)
  edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'proposal_notification_url': proposal_notification_url,
      'proposer_name': data.profile.name(),
      'proposal_name': proposal.title,
      'proposal_content': proposal.content,
      'org': data.organization.name,
      'profile_edit_link': edit_link,
  }

  # determine the subject
  subject = DEF_UPDATED_PROPOSAL_SUBJECT % message_properties

  template = DEF_UPDATED_PROPOSAL_NOTIFICATION_TEMPLATE

  return getContext(data, to_emails, message_properties, subject, template)


def newReviewContext(data, comment, to_emails):
  """Sends out a notification to alert the user of a new review.

  Args:
    data: a RequestData object.
  """
  assert isSet(data.proposal)
  assert isSet(data.proposer)

  review_notification_url = data.redirect.comment(comment, full=True)
  edit_link = data.redirect.editProfile().url(full=True)

  review_type = 'private' if comment.is_private else 'public'
  reviewed_name = data.proposal.title

  message_properties = {
      'review_notification_url': review_notification_url,
      'reviewer_name': comment.author.name(),
      'reviewed_name': reviewed_name,
      'review_content': comment.content,
      'review_visibility': review_type,
      'proposer_name': data.proposer.name(),
      'org': data.proposal.org.name,
      'profile_edit_link': edit_link,
      }

  # determine the subject
  subject = DEF_NEW_REVIEW_SUBJECT % message_properties

  template = DEF_NEW_REVIEW_NOTIFICATION_TEMPLATE

  if (data.proposer.key() != data.profile.key() and
      data.proposer.notify_public_comments and not comment.is_private):
    to_emails.append(data.proposer.email)

  return getContext(data, to_emails, message_properties, subject, template)


def newConnectionMessageContext(data, message, to_emails):
  """Generate a mail context for a new message.
  
  Args:
    data: A RequestData object.
    message: GSoCConnectionMessage object that represent the new message.
    to_emails: List of e-mails to which a notification should be sent.
  Returns:
    A context for a notification email that should be sent out, when new
    message is submitted for a connection.
  """
  assert isSet(data.connection)

  view_connection_url = data.redirect.connection_comment(
      message, full=True)

  profile_edit_link = data.redirect.editProfile().url(full=True)

  message_properties = {
      'view_connection_url': view_connection_url,
      'message_sender': message.author.name(),
      'message_content': message.content,
      'org': data.connection.organization.name,
      'profile_edit_link': profile_edit_link,
      }

  subject = DEF_NEW_CONNECTION_MESSAGE_SUBJECT % message_properties

  template = DEF_NEW_CONNECTION_MESSAGE_NOTIFICATION_TEMPLATE

  return getContext(data, to_emails, message_properties, subject, template)


def createOrUpdateSlotTransferContext(data, slot_transfer,
                                      to_emails, update=False):
  """Mail context to be sent to program host upon slot transfer request

  Args:
    data: a RequestData object.
    slot_transfer: entity that holds the slot transfer request information.
    update: True if the request was updated, False if the new one was created.
  """
  # TODO(nathaniel): make unnecessary this .program() call.
  data.redirect.program()

  slot_transfer_admin_url = data.redirect.urlOf(
      'gsoc_admin_slots_transfer', full=True)

  message_properties = {
      'org': slot_transfer.program.short_name,
      'slot_transfer_admin_url': slot_transfer_admin_url,
      'slot_transfer': slot_transfer,
      'org_name': slot_transfer.parent().name,
      'remarks': slot_transfer.remarks,
      'update': update,
      }

  # determine the subject
  if update:
    subject = DEF_UPDATE_SLOT_TRANSFER_SUBJECT % message_properties
  else:
    subject = DEF_NEW_SLOT_TRANSFER_SUBJECT % message_properties

  template = DEF_SLOT_TRANSFER_NOTIFICATION_TEMPLATE

  return getContext(data, to_emails, message_properties, subject, template)
