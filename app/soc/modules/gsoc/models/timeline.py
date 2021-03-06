# Copyright 2009 the Melange authors.
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

"""This module contains the GSoC specific Timeline Model.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.timeline


class GSoCTimeline(soc.models.timeline.Timeline):
  """GSoC Timeline model extends the basic Program Timeline model."""

  application_review_deadline = db.DateTimeProperty(
      verbose_name=ugettext(
          'Organizations Review Student Applications Deadline'))

  student_application_matched_deadline = db.DateTimeProperty(
      verbose_name=ugettext('Students Matched to Mentors Deadline'))

  accepted_students_announced_deadline = db.DateTimeProperty(
      verbose_name=ugettext('Accepted Students Announced Deadline'))

  form_submission_start = db.DateTimeProperty(
      verbose_name=ugettext('Students Start Submitting Their Forms'))

  bonding_start = db.DateTimeProperty(
      verbose_name=ugettext('Community Bonding Period Start date'))

  bonding_end = db.DateTimeProperty(
      verbose_name=ugettext('Community Bonding Period End date'))

  coding_start = db.DateTimeProperty(
      verbose_name=ugettext('Coding Start date'))

  coding_end = db.DateTimeProperty(
      verbose_name=ugettext('Coding End date'))

  suggested_coding_deadline = db.DateTimeProperty(
      verbose_name=ugettext('Suggested Coding Deadline'))

  mentor_summit_start = db.DateTimeProperty(
      verbose_name=ugettext('Mentor Summit Start date'))

  mentor_summit_end = db.DateTimeProperty(
      verbose_name=ugettext('Mentor Summit End date'))
