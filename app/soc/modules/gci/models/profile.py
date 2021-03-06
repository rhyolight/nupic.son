# Copyright 2011 the Melange authors.
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

"""This module contains the  GCIProfile Model."""

from google.appengine.ext import db
from google.appengine.ext import blobstore

from django.utils.translation import ugettext

from soc.models import profile


class GCIProfile(profile.Profile):
  """GCIProfile Model.
  """
  automatic_task_subscription = db.BooleanProperty(
      required=False, default=True,
      verbose_name=ugettext('Automatic task subscription'))
  automatic_task_subscription.help_text = ugettext(
      'Whether to subscribe to tasks of interest automatically. These are '
      'tasks which you have claimed or are mentoring.')
  automatic_task_subscription.group = profile.NOTIFICATION_SETTINGS_GROUP

  # Avatar figure chosen by student and mentor
  avatar = db.StringProperty(
      required=False, verbose_name=ugettext('Avatar'))
  avatar.group = profile.PUBLIC_INFO_GROUP


class GCIStudentInfo(profile.StudentInfo):
  """GCIStudentInfo Model.

  Parent:
    soc.modules.gci.models.profile.GCIProfile
  """

  #: number of tasks completed by the student
  number_of_completed_tasks = db.IntegerProperty(default=0)

  #: Property determining whether the student has closed at least one task
  task_closed = db.BooleanProperty(default=False)

  #: Set to True if the reminder mail to upload parental consent
  #: form is sent to students
  parental_form_mail = db.BooleanProperty(default=False)

  #: Property pointing to the consent form
  consent_form = blobstore.BlobReferenceProperty(
      required=False, verbose_name=ugettext('Parental Consent Form'))
  consent_form.help_text = ugettext(
      'A signed Parental Consent Form from your legal parent or guardian')

  #: Stores whether the consent form is verified by the program host.
  consent_form_verified = db.BooleanProperty(default=False)

  #: Property pointing to the second page of the consent form
  #: (Deprecated since GCI2011)
  consent_form_two = blobstore.BlobReferenceProperty(
      required=False, verbose_name=ugettext('Parental Consent Form (page 2)'))
  consent_form_two.help_text = ugettext(
      'Page two of the Parental Consent Form (if applicable)')

  #: Property pointing to the student id form
  student_id_form = blobstore.BlobReferenceProperty(
      required=False, verbose_name=ugettext('Enrollment Form'))

  #: Stores whether the student id form is verified by the program host.
  student_id_form_verified = db.BooleanProperty(default=False)

  #: GCIOrganiztion for which the student is a winner
  winner_for = db.ReferenceProperty(
      required=False, collection_name='winners')

  #: Whether the student is a grand prize winner of the program
  is_winner = db.BooleanProperty(default=False, required=False)
