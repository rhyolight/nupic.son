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

"""This module contains the Role Model."""


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.models import countries

import soc.models.linkable
import soc.models.program
import soc.models.user


PUBLIC_INFO_GROUP = ugettext(
    "1. Public Info")
CONTACT_INFO_GROUP = (
    "2. Contact Info (Private)")
SHIPPING_INFO_GROUP = ugettext(
    "3. Shipping Info (if different from above)")
PRIVATE_INFO_GROUP = ugettext(
    "4. Private Info")
EDUCATION_GROUP = ugettext(
    "5. Education")
NOTIFICATION_SETTINGS_GROUP = ugettext(
    "6. Notification settings")
TERMS_OF_SERVICE_GROUP = ugettext(
    "99. Terms of Service")


class StudentInfo(db.Model):
  """The model which contains some detailed information which are necessary
  only when the user has a student role. 

  Parent:
    soc.models.role.Profile
  """

  school_name = db.StringProperty(required=True, 
      verbose_name=ugettext('School Name'))
  school_name.group = EDUCATION_GROUP
  school_name.help_text = ugettext(
      'Please enter the full name of your school, college or university in'
      ' this field. Please use the complete formal name of your school, e.g.'
      ' University of California at Berkeley, instead of Cal or UCB. It would'
      ' be most wonderful if you could provide your school\'s name in English,'
      ' as all the program administrators speak English as their first'
      ' language and it will make it much easier for us to assemble program'
      ' statistics, etc., later if we can easily read the name of your school.'
      ' Also, please try to select your school\'s name from the dropdown. If'
      ' your school is not listed, just enter it manually.')

  school_country = db.StringProperty(required=True,
      verbose_name=ugettext('School Country/Territory'),
      choices=countries.COUNTRIES_AND_TERRITORIES)
  school_country.group = EDUCATION_GROUP

  #: School type can be only High school for GCI and can be University
  #: for GSoC.
  school_type = db.StringProperty(required=False,
                                  verbose_name=ugettext('School Type'),
                                  choices=['University', 'High School'])
  school_type.group = EDUCATION_GROUP

  major = db.StringProperty(required=False,
      verbose_name=ugettext('Major Subject'))
  major.group = EDUCATION_GROUP

  degree = db.StringProperty(required=False,
      verbose_name=ugettext('Degree'),
      choices=['Undergraduate', 'Master', 'PhD'])
  degree.group = EDUCATION_GROUP

  expected_graduation = db.IntegerProperty(required=True,
      verbose_name=ugettext('Expected Graduation Year'))
  expected_graduation.help_text = ugettext("Pick your expected graduation year")
  expected_graduation.group = EDUCATION_GROUP

  #: Property containing the Grade of the student if the school type
  #: is High School.
  grade = db.IntegerProperty(required=False,
      verbose_name=ugettext('Grade'))
  grade.group = EDUCATION_GROUP
  grade.help_text = ugettext(
      'Please enter your grade in the school, e.g. 8 if you are in 8th'
      ' grade. In some parts of the world it is called as, e.g. 8th'
      ' Standard')

  #: Program that the entity has been created for
  program = db.ReferenceProperty(
      reference_class=soc.models.program.Program,
      required=False, collection_name='student_infos')


class Profile(soc.models.linkable.Linkable):
  """Per-program user information.

  Parent:
    soc.models.user.User
  """

  #: A required many:1 relationship that ties (possibly multiple
  #: entities of) Role details to a unique User. A Role cannot
  #: exist unassociated from a login identity and credentials. The
  #: back-reference in the User model is a Query named 'roles'.
  user = db.ReferenceProperty(reference_class=soc.models.user.User,
                              required=True, collection_name='roles')

  #: Required field storing publicly-displayed name.  Can be a real name
  #: (though this is not recommended), or a nick name or some other public
  #: alias.  Public names can be any valid UTF-8 text.
  public_name = db.StringProperty(
      required=True, verbose_name=ugettext('Public name'))
  public_name.help_text = ugettext(
      'Human-readable name (UTF-8) that will be displayed publicly on the'
      ' site.')
  public_name.group = PUBLIC_INFO_GROUP

  #====================================================================
  #  (public) name information
  #====================================================================

  #: Required field storing the parts of the Role's name
  #: corresponding to the field names; displayed publicly.
  #: given_name can only be ASCII, not UTF-8 text, because it is
  #: used, for example, as part of the shipping (mailing) address.
  given_name = db.StringProperty(required=True,
      verbose_name=ugettext('First (given) name'))
  given_name.help_text = ugettext('only A-z, 0-9 and whitespace characters')
  given_name.group = PUBLIC_INFO_GROUP

  #: Required field storing the parts of the Role's name
  #: corresponding to the field names; displayed publicly.
  #: Surname can only be ASCII, not UTF-8 text, because it is
  #: used, for example, as part of the shipping (mailing) address.
  surname = db.StringProperty(
      required=True,
      verbose_name=ugettext('Last (family) name'))
  surname.help_text = ugettext('only A-z, 0-9 and whitespace characters')
  surname.group = PUBLIC_INFO_GROUP

  #: Optional field used as a display name, such as for awards
  #: certificates. Should be the entire name in the format
  #: the Role would like it displayed (could be surname followed by
  #: given name in some cultures, for example). Display names can be
  #: any valid UTF-8 text.
  name_on_documents = db.StringProperty(
      verbose_name=ugettext('Legal name'))
  name_on_documents.help_text = ugettext(
      'Optional field used as a display name, such as for documents like '
      'awards certificates. Should be the entire name in the format '
      'the person would like it displayed (could be family name followed '
      'by given name in some cultures, for example). Legal name can be '
      'any valid UTF-8 text.')
  name_on_documents.group = PUBLIC_INFO_GROUP

  #====================================================================
  #  (public) contact information
  #====================================================================

  #: Optional field storing Instant Messaging network; displayed publicly.
  im_network = db.StringProperty(
      verbose_name=ugettext('IM Network'))
  im_network.help_text = ugettext(
      'examples: irc:irc.freenode.net xmpp:gmail.com/Home')
  im_network.group = PUBLIC_INFO_GROUP

  #: Optional field storing Instant Messaging handle; displayed publicly.
  im_handle = db.StringProperty(
      verbose_name=ugettext('IM Handle'))
  im_handle.help_text = ugettext(
      'personal identifier, such as: screen name, IRC nick, user name')
  im_handle.group = PUBLIC_INFO_GROUP

  #: Optional field storing a home page URL; displayed publicly.
  home_page = db.LinkProperty(
      verbose_name=ugettext('Home Page URL'))
  home_page.group = PUBLIC_INFO_GROUP

  #: Optional field storing a blog URL; displayed publicly.
  blog = db.LinkProperty(
      verbose_name=ugettext('Blog URL'))
  blog.group = PUBLIC_INFO_GROUP

  #: Optional field storing a URL to an image, expected to be a
  #: personal photo (or cartoon avatar, perhaps); displayed publicly.
  photo_url = db.LinkProperty(
      verbose_name=ugettext('Thumbnail Photo URL'))
  photo_url.help_text = ugettext(
      'URL of 64x64 pixel thumbnail image')
  photo_url.group = PUBLIC_INFO_GROUP

  #====================================================================
  # (private) contact information
  #====================================================================

  #: Required field used as the contact mechanism for the program
  #: Role (for example the address the system sends emails to).
  email = db.EmailProperty(
      required=True,
      verbose_name=ugettext('Email Address'))
  email.group = CONTACT_INFO_GROUP
  email.help_text = ugettext("This is the address we send all notifications to.")

  #: Required field containing residence street address; kept private.
  #: Residence street address can only be ASCII, not UTF-8 text, because
  #: it may be used as a shipping address.
  res_street = db.StringProperty(required=True,
      verbose_name=ugettext('Street Address 1'))
  res_street.help_text = ugettext(
      'street number and name, '
      'only A-z, 0-9 and whitespace characters')
  res_street.group = CONTACT_INFO_GROUP

  #: Optional field containing the 2nd line for the residence street address;
  #: kept private.
  #: Can only be ASCII, not UTF-8 text, because
  #: it may be used as a shipping address.
  res_street_extra = db.StringProperty(required=False,
      verbose_name=ugettext('Street Address 2'))
  res_street_extra.help_text = ugettext(
      '2nd address line usually for apartment numbers. '
      'only A-z, 0-9 and whitespace characters')
  res_street_extra.group = CONTACT_INFO_GROUP

  #: Required field containing residence address city; kept private.
  #: Residence city can only be ASCII, not UTF-8 text, because it
  #: may be used as a shipping address.
  res_city = db.StringProperty(required=True,
      verbose_name=ugettext('City'))
  res_city.help_text = ugettext(
      'only A-z, 0-9 and whitespace characters')
  res_city.group = CONTACT_INFO_GROUP

  #: Optional field containing residence address state or province; kept
  #: private.  Residence state/province can only be ASCII, not UTF-8
  #: text, because it may be used as a shipping address.
  res_state = db.StringProperty(
      verbose_name=ugettext('State/Province'))
  res_state.help_text = ugettext(
      'optional if country/territory does not have states or provinces, '
      'only A-z, 0-9 and whitespace characters')
  res_state.group = CONTACT_INFO_GROUP

  #: Required field containing residence address country or territory; kept
  #: private.
  res_country = db.StringProperty(required=True,
      verbose_name=ugettext('Country/Territory'),
      choices=countries.COUNTRIES_AND_TERRITORIES)
  res_country.group = CONTACT_INFO_GROUP

  #: Required field containing residence address postal code (ZIP code in
  #: the United States); kept private.  Residence postal code can only be
  #: ASCII, not UTF-8 text, because it may be used as a shipping address.
  res_postalcode = db.StringProperty(required=True,
      verbose_name=ugettext('ZIP/Postal Code'))
  res_postalcode.help_text = ugettext(
      'only A-z, 0-9 and whitespace characters')
  res_postalcode.group = CONTACT_INFO_GROUP

  #: Required field containing a phone number that will be used to
  #: contact the user, also supplied to shippers; kept private.
  phone = db.PhoneNumberProperty(
      required=True,
      verbose_name=ugettext('Phone Number'))
  phone.help_text = ugettext(
      'include complete international calling number with country code, '
      'use numbers only')
  phone.group = CONTACT_INFO_GROUP

  #: Optional field containing a separate recipient name; kept
  #: private. Recipient name can only be ASCII, not UTF-8 text
  ship_name = db.StringProperty(
      verbose_name=ugettext('Full Recipient Name'))
  ship_name.help_text = ugettext(
      'Fill in the name of the person who should be receiving your packages.')
  ship_name.group = SHIPPING_INFO_GROUP

  #: Optional field containing a separate shipping street address; kept
  #: private.  If shipping address is not present in its entirety, the
  #: residence address will be used instead.  Shipping street address can only
  #: be ASCII, not UTF-8 text, because, if supplied, it is used as a
  #: shipping address.
  ship_street = db.StringProperty(
      verbose_name=ugettext('Shipping Street Address 1'))
  ship_street.help_text = ugettext(
      'Street number and name, only A-z, 0-9 and whitespace characters.')
  ship_street.group = SHIPPING_INFO_GROUP

  #: Optional field containing a 2nd line for the shipping street address; kept
  #: private. If shipping address is not present in its entirety, the
  #: residence address will be used instead.  Shipping street address can only
  #: be ASCII, not UTF-8 text, because, if supplied, it is used as a
  #: shipping address.
  ship_street_extra = db.StringProperty(
      verbose_name=ugettext('Shipping Street Address 2'))
  ship_street_extra.help_text = ugettext(
      '2nd address line usually used for apartment numbers, '
      'only A-z, 0-9 and whitespace characters.')
  ship_street_extra.group = SHIPPING_INFO_GROUP

  #: Optional field containing shipping address city; kept private.
  #: Shipping city can only be ASCII, not UTF-8 text, because, if
  #: supplied, it is used as a shipping address.
  ship_city = db.StringProperty(
      verbose_name=ugettext('Shipping City'))
  ship_city.help_text = ugettext(
      'Only A-z, 0-9 and whitespace characters.')
  ship_city.group = SHIPPING_INFO_GROUP

  #: Optional field containing shipping address state or province; kept
  #: private.  Shipping state/province can only be ASCII, not UTF-8
  #: text, because, if supplied, it is used as a shipping address.
  ship_state = db.StringProperty(
      verbose_name=ugettext('Shipping State/Province'))
  ship_state.help_text = ugettext(
      'Optional if country/territory does not have states or provinces, '
      'Only A-z, 0-9 and whitespace characters.')
  ship_state.group = SHIPPING_INFO_GROUP

  #: Optional field containing shipping address country or territory; kept
  #: private.
  ship_country = db.StringProperty(
      verbose_name=ugettext('Shipping Country/Territory'),
      choices=countries.COUNTRIES_AND_TERRITORIES)
  ship_country.help_text = ugettext(
      'Only A-z, 0-9 and whitespace characters.')
  ship_country.group = SHIPPING_INFO_GROUP

  #: Optional field containing shipping address postal code (ZIP code in
  #: the United States); kept private.  Shipping postal code can only be
  #: ASCII, not UTF-8 text, because, if supplied, it is used as a
  #: shipping address.
  ship_postalcode = db.StringProperty(
      verbose_name=ugettext('Shipping ZIP/Postal Code'))
  ship_postalcode.help_text = ugettext(
      'Only A-z, 0-9 and whitespace characters')
  ship_postalcode.group = SHIPPING_INFO_GROUP

  #====================================================================
  # (private) personal information
  #====================================================================

  #: Required field containing the Role's birthdate (for
  #: determining Program participation eligibility); kept private.
  birth_date = db.DateProperty(
      required=True,
      verbose_name=ugettext('Birth Date'))
  birth_date.help_text = ugettext(
      'format YYYY-MM-DD, required for determining program eligibility')
  birth_date.group = PRIVATE_INFO_GROUP

  #: Optional field indicating choice of t-shirt fit; kept private.
  tshirt_style = db.StringProperty(
      verbose_name=ugettext('T-shirt Style'),
      choices=('male', 'female'))
  tshirt_style.group = PRIVATE_INFO_GROUP

  #: Optional field indicating choice of t-shirt, from XXS to XXXL;
  #: kept private.
  tshirt_size = db.StringProperty(
      verbose_name=ugettext('T-shirt Size'),
      choices=('XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'))
  tshirt_size.group = PRIVATE_INFO_GROUP
  tshirt_size.help_text = ugettext('See also '
      '<a href="http://bit.ly/ayGxJk" target="_blank"> for women</a> and '
      '<a href="http://bit.ly/8ZrywF" target="_blank">for men</a>.')

  #: Optional field indicating gender;
  #: kept private.
  gender = db.StringProperty(
      verbose_name=ugettext('Gender'),
      choices=('male', 'female', 'other'))
  gender.group = PRIVATE_INFO_GROUP

  #: Property to gain insight into where students heard about this program
  program_knowledge = db.TextProperty(required=False, verbose_name=ugettext(
      "How did you hear about this program?"))
  program_knowledge.help_text = ugettext("Please be as "
      "specific as possible, e.g. blog post (include URL if possible), mailing "
      "list (please include list address), information session (please include "
      "location and speakers if you can), etc.")
  program_knowledge.group = PRIVATE_INFO_GROUP

  #: field storing wheter the User has agreed to the site-wide Terms of Service.
  #: (Not a required field because the Terms of Service might not be present
  #: when the first User profile is created when bootstrapping the site.)
  agreed_to_tos = db.BooleanProperty(required=False, default=False,
      verbose_name=ugettext('I Agree to the Terms of Service'))
  agreed_to_tos.help_text = ugettext(
      'Indicates whether the user agreed to this role Terms of Service.')
  agreed_to_tos.group = TERMS_OF_SERVICE_GROUP

  #: field storing when the User has agreed to the site-wide Terms of Service.
  #: (Not a required field because the Terms of Service might not be present
  #: when the first User profile is created when bootstrapping the site.)
  agreed_to_tos_on = db.DateTimeProperty(required=False, default=None,
      verbose_name=ugettext('Has agreed to the Terms of Service on'))
  agreed_to_tos_on.help_text = ugettext(
      'Indicates when the user agreed to this role Terms of Service.')
  agreed_to_tos.group = TERMS_OF_SERVICE_GROUP

  #: field storing the status of this role
  #: Active means that this role can exercise all it's privileges.
  #: Invalid means that a role should not be able to excercise any
  #: priviliges.
  status = db.StringProperty(default='active',
      choices=['active','invalid'],
      verbose_name=ugettext('Status of this Role'))
  status.help_text = ugettext('Indicates the status of the role '
      'concerning which privileges may be used.')

  #====================================================================
  #notification settings
  #====================================================================

  notify_new_requests = db.BooleanProperty(required=False, default=True,
      verbose_name=ugettext('Notify of new requests'))
  notify_new_requests.help_text = ugettext(
      'Whether to send an email notification when new requests are submitted.')
  notify_new_requests.group = NOTIFICATION_SETTINGS_GROUP

  notify_invite_handled = db.BooleanProperty(required=False, default=True,
      verbose_name=ugettext('Notify of handled invitations'))
  notify_invite_handled.help_text = ugettext(
      'Whether to send an email notification when an invite is handled.')
  notify_invite_handled.group = NOTIFICATION_SETTINGS_GROUP

  notify_request_handled = db.BooleanProperty(required=False, default=True,
      verbose_name=ugettext('Notify of handled requests'))
  notify_request_handled.help_text = ugettext(
      'Whether to send an email notification when your request is handled.')
  notify_request_handled.group = NOTIFICATION_SETTINGS_GROUP

  notify_new_invites = db.BooleanProperty(required=False, default=True,
      verbose_name=ugettext('Notify of new invites'))
  notify_new_invites.help_text = ugettext(
      'Whether to send an email notification when you receive a new invite.')
  notify_new_invites.group = NOTIFICATION_SETTINGS_GROUP

  #====================================================================
  #specific roles information
  #====================================================================

  #: field storing whether the User is a student
  is_student = db.BooleanProperty(required=False, default=False,
      verbose_name=ugettext('Is student'))

  #: field storing whether the User is a mentor
  is_mentor = db.BooleanProperty(required=False, default=False,
      verbose_name=ugettext('Is Mentor'))

  #: field storing whether the User is an org amdin
  is_org_admin = db.BooleanProperty(required=False, default=False,
      verbose_name=ugettext('Is Organization Administrator'))

  #: List of organizations that the user with the role is a mentor for
  mentor_for = db.ListProperty(item_type=db.Key, default=[])
  mentor_for.help_text = ugettext('List of organizations for which the user '
      'is a mentor.')

  #: List of organizations that the user with the role is an org admin for
  org_admin_for = db.ListProperty(item_type=db.Key, default=[])
  org_admin_for.help_text = ugettext('List of organizations for which '
      'the user is an organization admin.')

  #: Points to student specific information if the user has a student role
  student_info = db.ReferenceProperty(required=False, default=None,
      reference_class=StudentInfo)

  created_on = db.DateTimeProperty(auto_now_add=True)

  modified_on = db.DateTimeProperty(auto_now=True)

  def _fix_name(self, commit=True):
    """Retrieves the name property from the parent user.
    """
    pass

  def name(self):
    """Property as 'name' for use in common templates.
    """
    return self.public_name

  def document_name(self):
    """Property as 'document_name' used on for example award certificates.
    """
    if self.name_on_documents:
      return self.name_on_documents
    else:
      return self.name()

  def full_name(self):
    """Property which returns given name followed by surname and separated
    by a single space character.
    """
    return '%s %s' % (self.given_name, self.surname)

  def shipping_name(self):
    """Property recipient_name that returns shipping name if shipping
    address is set else the given name and surname.
    """
    return self.ship_name if self.hasShippingAddress() else self.given_name + " " + self.surname

  def shipping_street(self):
    """Property shipping_street that returns shipping street if
    shipping address is set else the residential street.
    """
    return self.ship_street if self.hasShippingAddress() else self.res_street

  def shipping_street_extra(self):
    """Property shipping_street_extra that returns the 2nd shipping address line
    if shipping address is set else the residential 2nd address line.
    """
    return self.ship_street_extra if self.hasShippingAddress() else \
        self.res_street_extra

  def shipping_city(self):
    """Property shipping_city that returns shipping city if
    shipping address is set else the residential city.
    """
    return self.ship_city if self.hasShippingAddress() else self.res_city

  def shipping_state(self):
    """Property shipping_state that returns shipping state if
    shipping address is set else the residential state.
    """
    return self.ship_state if self.hasShippingAddress() else self.res_state

  def shipping_country(self):
    """Property shipping_country that returns shipping country if
    shipping address is set else the residential country.
    """
    return self.ship_country if self.hasShippingAddress() else self.res_country

  def shipping_postalcode(self):
    """Property shipping_postalcode that returns the shipping postal code if
    shipping address set else the residential postal code.
    """
    return self.ship_postalcode if self.hasShippingAddress() else \
        self.res_postalcode

  def hasShippingAddress(self):
    """Checks if the required fields for the shipping address are set.
    """
    return self.ship_city and self.ship_country and self.ship_postalcode and \
        self.ship_street

  def ccTld(self):
    """Property as 'ccTld' for use in Maps.
    """
    return countries.COUNTRIES_TO_CCTLD[self.res_country]
