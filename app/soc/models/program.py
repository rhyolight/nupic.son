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

"""This module contains the Program Model.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.document
import soc.models.presence
import soc.models.timeline


class Program(soc.models.presence.Presence):
  """The Program model, representing a Program ran by a Sponsor.
  """

  #: Required field storing name of the group.
  name = db.StringProperty(required=True,
      verbose_name=ugettext('Name'))
  name.help_text = ugettext('Complete, formal name of the program.')

  #: Required field storing short name of the group.
  #: It can be used for displaying group as sidebar menu item.
  short_name = db.StringProperty(required=True,
      verbose_name=ugettext('Short name'))
  short_name.help_text = ugettext('Short name used for sidebar menu')

  #: Optional field used to relate it to other programs
  #: For example, GSoC would be a group label for GSoC2008/GSoC2009
  group_label = db.StringProperty(
      verbose_name=ugettext('Group label'))
  group_label.help_text = ugettext(
      'Optional name used to relate this program to others.')

  #: Required field storing description of the group.
  description = db.TextProperty(required=True,
      verbose_name=ugettext('Description'))
  description.help_text = ugettext(
      '<small><i>for example:</i></small><br>'
      '<tt><b>GSoC 2009</b> is the <i>Google Summer of Code</i>,'
      ' but in <u>2009</u>!</tt><br><br>'
      '<small><i>(rich text formatting is supported)</i></small>')

  #: Number of accepted organizations
  nr_accepted_orgs = db.IntegerProperty(
      required=False, verbose_name=ugettext('#accepted orgs'))
  nr_accepted_orgs.help_text = ugettext(
      'The number of accepted organizations.')

  #: Property that contains the minimum age of a student allowed to
  #: participate
  student_min_age = db.IntegerProperty(
      required=False, verbose_name=ugettext('Student minimum age'))
  student_min_age.group = ugettext('Age Requirements')
  student_min_age.help_text = ugettext(
      'Minimum age (in years) of the student participate.')

  # TODO(nathaniel): In the offseason, fix this to be the maximum
  # allowed age (rounded down to year) rather than user-unfriendly
  # "youngest disallowed age".
  #: Property that contains the maximum age of a student allowed to
  #: participate
  student_max_age = db.IntegerProperty(default=100,
      required=False, verbose_name=ugettext('Student age ceiling'))
  student_max_age.group = ugettext('Age Requirements')
  student_max_age.help_text = ugettext(
      'Youngest disallowed age (in years).')

  #: Property that contains the date as of which above student
  #: minimum/maximum age requirement holds.
  student_min_age_as_of = db.DateProperty(
      required=False, verbose_name=ugettext('Minimum age as of'))
  student_min_age_as_of.group = ugettext('Age Requirements')
  student_min_age_as_of.help_text = ugettext(
      'Date as of which the student minimum age requirement '
      'should be reached.')

  #: Required 1:1 relationship indicating the Program the Timeline
  #: belongs to.
  timeline = db.ReferenceProperty(reference_class=soc.models.timeline.Timeline,
                                  required=True, collection_name="program",
                                  verbose_name=ugettext('Timeline'))

  #: Document reference property used for the Org Admin Agreement
  org_admin_agreement = db.ReferenceProperty(
    reference_class=soc.models.document.Document,
    verbose_name=ugettext('Organization Admin Agreement'),
    collection_name='org_admin_agreement')
  org_admin_agreement.help_text = ugettext(
      'Document containing optional Mentor Agreement for participating as a '
      'Organization admin.')

  #: Document reference property used for the Mentor Agreement
  mentor_agreement = db.ReferenceProperty(
    reference_class=soc.models.document.Document,
    verbose_name=ugettext('Mentor Agreement'),
    collection_name='mentor_agreement')
  mentor_agreement.help_text = ugettext(
      'Document containing optional Mentor Agreement for participating as a '
      'Mentor.')

  #: Document reference property used for the Student Agreement
  student_agreement = db.ReferenceProperty(
    reference_class=soc.models.document.Document,
    verbose_name=ugettext('Student Agreement'),
    collection_name='student_agreement')
  student_agreement.help_text = ugettext(
      'Document containing optional Student Agreement for participating as a '
      'Student.')

  #: Status of the program
  #: Invisible: Program Stealth-Mode Visible to Hosts and Devs only
  #: Visible: Visible to everyone.
  #: Invalid: Not visible or editable by anyone
  status = db.StringProperty(required=True, default='invisible',
      verbose_name=ugettext('Program Status'),
      choices=['invisible', 'visible', 'invalid'])
  status.help_text = ugettext(
      '<tt>Invisible: Program Stealth-Mode Visible to Hosts and Devs only.<br/>'
      'Visible: Visible to everyone.<br/>'
      'Inactive: Not visible in sidebar, not editable.<br/>'
      'Invalid: Not visible or editable by anyone.</tt>')

  #: The document entity which contains the "About" page for the program
  about_page = db.ReferenceProperty(
      reference_class=soc.models.document.Document,
      verbose_name=ugettext('About page document'))
  about_page.collection_name = 'about_page'
  about_page.help_text = ugettext('The document with <b>About</b>')

  #: The document entity which contains "Events & Timeline" page
  #: for the program
  events_page = db.ReferenceProperty(
      reference_class=soc.models.document.Document,
      verbose_name=ugettext('Events page document'))
  events_page.collection_name = 'events_page'
  events_page.help_text = ugettext(
      'The document for the <b>Events & Timeline</b> page')

  #: The url which contains the "Events & Timeline" frame
  events_frame_url = db.LinkProperty(
      verbose_name=ugettext('Events page iframe url'))
  events_frame_url.help_text = ugettext(
      'The iframe url for the <b>Events & Timeline</b> page')

  #: The document entity which contains the "Connect With Us" page
  #: for the program
  connect_with_us_page = db.ReferenceProperty(
      reference_class=soc.models.document.Document,
      verbose_name=ugettext('Connect with us document'))
  connect_with_us_page.collection_name = 'connect_with_us_page'
  connect_with_us_page.help_text = ugettext(
      'The document for the <b>Connect With Us</b> page')

  #: The document entity which contains the "Help" page
  #: for the program
  help_page = db.ReferenceProperty(
      reference_class=soc.models.document.Document,
      verbose_name=ugettext('Help document'))
  help_page.collection_name = 'help_page'
  help_page.help_text = ugettext(
      'The document for the <b>Help</b> page')

  privacy_policy_url = db.LinkProperty(
      verbose_name=ugettext("Privacy Policy"))
  privacy_policy_url.help_text = ugettext(
      "The url for the <b>Privacy Policy</b>")

  blogger = db.LinkProperty(
      required=False, verbose_name=ugettext("Blogger URL"))
  blogger.help_text = ugettext("URL of the Blogger home page for the program")
  blogger.group = ugettext("1. Public Info")

  gplus = db.LinkProperty(
      required=False, verbose_name=ugettext("Google+ URL"))
  gplus.help_text = ugettext("URL of the Google+ home page for the program")
  gplus.group = ugettext("1. Public Info")

  email = db.EmailProperty(
      required=False, verbose_name=ugettext("Program email"))
  email.help_text = ugettext("Contact email address for the program")
  email.group = ugettext("1. Public Info")

  irc = db.EmailProperty(
      required=False, verbose_name=ugettext("IRC URL"))
  irc.help_text = ugettext("URL of the irc channel for the program in "
                           "the format irc://<channel>@server")
  irc.group = ugettext("1. Public Info")

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
      verbose_name=ugettext('Accepted Organizations Message'))

  #: Message sent to the organizations that are rejected for the program.
  rejected_orgs_msg = db.TextProperty(required=False,
      verbose_name=ugettext('Rejected Organizations Message'))

  #: Message sent to a mentor/org admin the first time they join the program.
  mentor_welcome_msg = db.TextProperty(required=False,
      verbose_name=ugettext('Mentor Welcome Message'))
