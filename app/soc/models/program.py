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

"""This module contains the Program Model."""

from google.appengine.ext import db

from django.utils import translation

from soc.models import document as document_model
from soc.models import linkable as linkable_model
from soc.models import sponsor as sponsor_model
from soc.models import timeline as timeline_model

# Allowed values for program status.
STATUS_VISIBLE = 'visible'  # The program is visible to everyone.
STATUS_INVISIBLE = 'invisible'  # The program is visible to hosts and devs.
STATUS_INVALID = 'invalid'  # The program is not visible to anyone.
# TODO(nathaniel): Is STATUS_INVALID used or useful any more?

GENERAL_INFO_GROUP = translation.ugettext(
    '1. General Info')
CONTACT_INFO_GROUP = translation.ugettext(
    '2. Contact Info')
AGE_REQUIREMENTS_GROUP = translation.ugettext(
    '3. Age Requirements')
PROGRAM_DOCUMENTS_GROUP = translation.ugettext(
    '4. Program Documents')


# TODO(daniel): drop inheritance from Linkable
class Program(linkable_model.Linkable):
  """The Program model, representing a Program ran by a Sponsor."""

  #: Identifier of the program which is be the last part of its unique key name
  program_id = db.StringProperty(required=True,
      verbose_name=translation.ugettext('Program ID'))
  program_id.help_text = translation.ugettext(
      'Used as part of various URL links throughout the site.')

  #: Reference to the sponsor of the program. Its key_name is used as the first
  #: part of program's unique key name
  sponsor = db.ReferenceProperty(required=True,
      reference_class=sponsor_model.Sponsor, collection_name='programs',
      verbose_name=translation.ugettext('Sponsor'))

  #: Required field storing name of the group.
  name = db.StringProperty(required=True,
      verbose_name=translation.ugettext('Name'))
  name.group = GENERAL_INFO_GROUP
  name.help_text = translation.ugettext(
      'Complete, formal name of the program.')

  #: Required field storing short name of the group.
  #: It can be used for displaying group as sidebar menu item.
  short_name = db.StringProperty(required=True,
      verbose_name=translation.ugettext('Short name'))
  short_name.group = GENERAL_INFO_GROUP
  short_name.help_text = translation.ugettext(
      'Short name used for sidebar menu')

  #: Optional field used to relate it to other programs
  #: For example, GSoC would be a group label for GSoC2008/GSoC2009
  group_label = db.StringProperty(
      verbose_name=translation.ugettext('Group label'))
  group_label.group = GENERAL_INFO_GROUP
  group_label.help_text = translation.ugettext(
      'Optional name used to relate this program to others.')

  #: Required field storing description of the group.
  description = db.TextProperty(required=True,
      verbose_name=translation.ugettext('Description'))
  description.group = GENERAL_INFO_GROUP
  description.help_text = translation.ugettext(
      '<small><i>for example:</i></small><br>'
      '<tt><b>GSoC 2009</b> is the <i>Google Summer of Code</i>,'
      ' but in <u>2009</u>!</tt><br><br>'
      '<small><i>(rich text formatting is supported)</i></small>')

  #: Number of accepted organizations
  nr_accepted_orgs = db.IntegerProperty(
      required=False, verbose_name=translation.ugettext('#accepted orgs'))
  nr_accepted_orgs.group = GENERAL_INFO_GROUP
  nr_accepted_orgs.help_text = translation.ugettext(
      'The number of accepted organizations.')

  #: Property that contains the minimum age of a student allowed to
  #: participate
  student_min_age = db.IntegerProperty(
      required=False, verbose_name=translation.ugettext('Student minimum age'))
  student_min_age.group = AGE_REQUIREMENTS_GROUP
  student_min_age.help_text = translation.ugettext(
      'Minimum age of students.')

  #: Property that contains the maximum age of a student allowed to
  #: participate
  student_max_age = db.IntegerProperty(default=200,
      required=False, verbose_name=translation.ugettext('Student maximum age'))
  student_max_age.group = AGE_REQUIREMENTS_GROUP
  student_max_age.help_text = translation.ugettext(
      'Maximum whole-year age of students.')

  #: Property that contains the date as of which above student
  #: minimum/maximum age requirement holds.
  student_min_age_as_of = db.DateProperty(
      required=False, verbose_name=translation.ugettext('Age as of'))
  student_min_age_as_of.group = AGE_REQUIREMENTS_GROUP
  student_min_age_as_of.help_text = translation.ugettext(
      'Date on which students must satisfy age requirements.')

  #: Required 1:1 relationship indicating the Program the Timeline
  #: belongs to.
  timeline = db.ReferenceProperty(
      reference_class=timeline_model.Timeline,
      required=True, collection_name="program",
      verbose_name=translation.ugettext('Timeline'))

  #: Document reference property used for the Org Admin Agreement
  org_admin_agreement = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('Organization Admin Agreement'),
      collection_name='org_admin_agreement')
  org_admin_agreement.group = PROGRAM_DOCUMENTS_GROUP
  org_admin_agreement.help_text = translation.ugettext(
      'Document containing optional Mentor Agreement for participating as a '
      'Organization admin.')

  #: Document reference property used for the Mentor Agreement
  mentor_agreement = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('Mentor Agreement'),
      collection_name='mentor_agreement')
  mentor_agreement.group = PROGRAM_DOCUMENTS_GROUP
  mentor_agreement.help_text = translation.ugettext(
      'Document containing optional Mentor Agreement for participating as a '
      'Mentor.')

  #: Document reference property used for the Student Agreement
  student_agreement = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('Student Agreement'),
      collection_name='student_agreement')
  student_agreement.group = PROGRAM_DOCUMENTS_GROUP
  student_agreement.help_text = translation.ugettext(
      'Document containing optional Student Agreement for participating as a '
      'Student.')

  #: Status of the program
  status = db.StringProperty(required=True, default=STATUS_INVISIBLE,
      verbose_name=translation.ugettext('Program Status'),
      choices=[STATUS_INVISIBLE, STATUS_VISIBLE, STATUS_INVALID])
  status.group = GENERAL_INFO_GROUP
  status.help_text = translation.ugettext(
      # TODO(nathaniel): Someone got their HTML in this Python.
      '<tt>%s: Program Stealth-Mode Visible to Hosts and Devs only.<br/>'
      '%s: Visible to everyone.<br/>'
      'Inactive: Not visible in sidebar, not editable.<br/>'
      '%s: Not visible or editable by anyone.</tt>' % (
          STATUS_INVISIBLE, STATUS_VISIBLE, STATUS_INVALID))

  #: The document entity which contains the "About" page for the program
  about_page = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('About page document'),
      collection_name = 'about_page')
  about_page.group = PROGRAM_DOCUMENTS_GROUP
  about_page.help_text = translation.ugettext('The document with <b>About</b>')

  #: The document entity which contains "Events & Timeline" page
  #: for the program
  events_page = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('Events page document'),
      collection_name = 'events_page')
  events_page.group = PROGRAM_DOCUMENTS_GROUP
  events_page.help_text = translation.ugettext(
      'The document for the <b>Events & Timeline</b> page')

  #: The url which contains the "Events & Timeline" frame
  events_frame_url = db.LinkProperty(
      verbose_name=translation.ugettext('Events page iframe url'))
  events_frame_url.group = GENERAL_INFO_GROUP
  events_frame_url.help_text = translation.ugettext(
      'The iframe url for the <b>Events & Timeline</b> page')

  #: The document entity which contains the "Connect With Us" page
  #: for the program
  connect_with_us_page = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('Connect with us document'),
      collection_name = 'connect_with_us_page')
  connect_with_us_page.group = PROGRAM_DOCUMENTS_GROUP
  connect_with_us_page.help_text = translation.ugettext(
      'The document for the <b>Connect With Us</b> page')

  #: The document entity which contains the "Help" page
  #: for the program
  help_page = db.ReferenceProperty(
      reference_class=document_model.Document,
      verbose_name=translation.ugettext('Help document'),
      collection_name = 'help_page')
  help_page.group = PROGRAM_DOCUMENTS_GROUP
  help_page.help_text = translation.ugettext(
      'The document for the <b>Help</b> page')

  privacy_policy_url = db.LinkProperty(
      verbose_name=translation.ugettext("Privacy Policy"))
  privacy_policy_url.group = GENERAL_INFO_GROUP
  privacy_policy_url.help_text = translation.ugettext(
      "The url for the <b>Privacy Policy</b>")

  #: ATOM or RSS feed URL. Feed entries are shown on the site
  #: page using Google's JavaScript blog widget
  feed_url = db.LinkProperty(verbose_name=translation.ugettext('Feed URL'))
  feed_url.group = CONTACT_INFO_GROUP
  feed_url.help_text = translation.ugettext(
      'The URL should be a valid ATOM or RSS feed. '
      'Feed entries are shown on the program home page.')

  blogger = db.LinkProperty(
      required=False, verbose_name=translation.ugettext("Blogger URL"))
  blogger.group = CONTACT_INFO_GROUP
  blogger.help_text = translation.ugettext(
      "URL of the Blogger home page for the program")

  gplus = db.LinkProperty(
      required=False, verbose_name=translation.ugettext("Google+ URL"))
  gplus.group = CONTACT_INFO_GROUP
  gplus.help_text = translation.ugettext(
      "URL of the Google+ home page for the program")

  email = db.EmailProperty(
      required=False, verbose_name=translation.ugettext("Program email"))
  email.group = CONTACT_INFO_GROUP
  email.help_text = translation.ugettext(
      "Contact email address for the program")

  irc = db.EmailProperty(
      required=False, verbose_name=translation.ugettext("IRC URL"))
  irc.group = CONTACT_INFO_GROUP
  irc.help_text = translation.ugettext(
      "URL of the irc channel for the program in "
      "the format irc://<channel>@server")

  #: Whether the messaging system is enabled
  messaging_enabled = db.BooleanProperty(default=False,
      verbose_name=translation.ugettext('Messaging Enabled'))
  messaging_enabled.group = GENERAL_INFO_GROUP
  messaging_enabled.help_text = translation.ugettext(
      'Indicates if the messaging system should be enabled.')

  def getProgramMessages(self):
    def get_or_create_txn():
      entity = type(self)._messages_model.all().ancestor(self).get()

      if not entity:
        entity = self._messages_model(parent=self)
        entity.put()
      return entity

    return db.run_in_transaction(get_or_create_txn)


class ProgramMessages(db.Model):
  """The ProgramMessages model.

  This model contains the specific messages whose content may be customized
  by program administrators and which may be sent because of various reasons
  throughout the program.
  """

  #: Message sent to the organizations that are accepted for the program.
  accepted_orgs_msg = db.TextProperty(required=False,
      verbose_name=translation.ugettext('Accepted Organizations Message'))

  #: Message sent to the organizations that are rejected for the program.
  rejected_orgs_msg = db.TextProperty(required=False,
      verbose_name=translation.ugettext('Rejected Organizations Message'))

  #: Message sent to a mentor/org admin the first time they join the program.
  mentor_welcome_msg = db.TextProperty(required=False,
      verbose_name=translation.ugettext('Mentor Welcome Message'))
