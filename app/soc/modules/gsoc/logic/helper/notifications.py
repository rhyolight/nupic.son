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

from google.appengine.ext import ndb

from django.utils.translation import ugettext

from melange.request import links

from soc.logic.helper.notifications import getContext
from soc.views.helper.access_checker import isSet
from soc.modules.gsoc.models import comment as comment_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.views.helper import url_names

from summerofcode.views.helper import urls


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

DEF_NEW_PROPOSAL_NOTIFICATION_TEMPLATE = \
    'soc/notification/new_proposal.html'

DEF_UPDATED_PROPOSAL_NOTIFICATION_TEMPLATE = \
    'soc/notification/updated_proposal.html'

DEF_SLOT_TRANSFER_NOTIFICATION_TEMPLATE = \
    'soc/notification/slot_transfer.html'

DEF_NEW_REVIEW_NOTIFICATION_TEMPLATE = \
    'soc/notification/new_review.html'


def newProposalContext(data, proposal, to_emails):
  """Sends out a notification to alert users of a new proposal.

  Args:
    data: a RequestData object.
    proposal: Newly created proposal entity.
    to_emails: List of email addresses of users who should
        receive notifications.
  """
  proposal_notification_url = links.ABSOLUTE_LINKER.userId(
      data.ndb_profile.key, proposal.key().id(), url_names.PROPOSAL_REVIEW)
  edit_profile_url = links.ABSOLUTE_LINKER.program(
      data.program, urls.UrlNames.PROFILE_EDIT, secure=True)

  org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(proposal)
  org = ndb.Key.from_old_key(org_key).get()

  message_properties = {
      'proposal_notification_url': proposal_notification_url,
      'proposer_name': data.ndb_profile.public_name,
      'proposal_name': proposal.title,
      'proposal_content': proposal.content,
      'org': org.name,
      'profile_edit_link': edit_profile_url,
  }

  # determine the subject
  subject = DEF_NEW_PROPOSAL_SUBJECT % message_properties

  template = DEF_NEW_PROPOSAL_NOTIFICATION_TEMPLATE

  return getContext(
      data.site, data.program, to_emails, message_properties, subject, template)


def updatedProposalContext(data, proposal, to_emails):
  """Sends out a notification to alert the user of an updated proposal.

  Args:
    data: a RequestData object
  """
  assert isSet(data.organization)

  proposal_notification_url = links.ABSOLUTE_LINKER.userId(
      data.ndb_profile.key, proposal.key().id(), url_names.PROPOSAL_REVIEW)
  edit_profile_url = links.ABSOLUTE_LINKER.program(
      data.program, urls.UrlNames.PROFILE_EDIT, secure=True)

  message_properties = {
      'proposal_notification_url': proposal_notification_url,
      'proposer_name': data.ndb_profile.public_name,
      'proposal_name': proposal.title,
      'proposal_content': proposal.content,
      'org': data.organization.name,
      'profile_edit_link': edit_profile_url,
  }

  # determine the subject
  subject = DEF_UPDATED_PROPOSAL_SUBJECT % message_properties

  template = DEF_UPDATED_PROPOSAL_NOTIFICATION_TEMPLATE

  return getContext(
      data.site, data.program, to_emails, message_properties, subject, template)


def newReviewContext(data, comment, to_emails):
  """Sends out a notification to alert the user of a new review.

  Args:
    data: a RequestData object
  """
  # TODO(daniel): the second part of this URL should probably be added by
  # a utility class
  review_notification_url = '%s#c%s' % (
      links.ABSOLUTE_LINKER.userId(
          data.url_ndb_profile.key, data.url_proposal.key().id(),
          url_names.PROPOSAL_REVIEW),
      comment.key().id())
  edit_profile_url = links.ABSOLUTE_LINKER.program(
      data.program, urls.UrlNames.PROFILE_EDIT, secure=True)

  review_type = 'private' if comment.is_private else 'public'
  reviewed_name = data.url_proposal.title

  org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(
      data.url_proposal)
  org = ndb.Key.from_old_key(org_key).get()

  author = ndb.Key.from_old_key(
      comment_model.GSoCComment.author.get_value_for_datastore(comment)).get()
  message_properties = {
      'review_notification_url': review_notification_url,
      'reviewer_name': author.public_name,
      'reviewed_name': reviewed_name,
      'review_content': comment.content,
      'review_visibility': review_type,
      'proposer_name': data.url_ndb_profile.public_name,
      'org': org.name,
      'profile_edit_link': edit_profile_url,
      }

  # determine the subject
  subject = DEF_NEW_REVIEW_SUBJECT % message_properties

  template = DEF_NEW_REVIEW_NOTIFICATION_TEMPLATE

  # TODO(daniel): notification settings
  if (data.url_ndb_profile.key != data.ndb_profile.key and
      not comment.is_private):
    to_emails.append(data.url_ndb_profile.email)

  return getContext(
      data.site, data.program, to_emails, message_properties, subject, template)


def createOrUpdateSlotTransferContext(data, slot_transfer,
                                      to_emails, update=False):
  """Mail context to be sent to program host upon slot transfer request

  Args:
    data: a RequestData object
    slot_transfer: entity that holds the slot transfer request information
    update: True if the request was updated, False if the new one was created
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

  return getContext(
      data.site, data.program, to_emails, message_properties, subject, template)
