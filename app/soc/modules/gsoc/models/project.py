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

"""This module contains the GSoCProject Model."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django.utils.translation import ugettext

from soc.modules.gsoc.models import code_sample as code_sample_model

import soc.modules.gsoc.models.proposal
import soc.models.program
import soc.models.organization

# constants with possible statuses of projects

# the project has been accepted into the program
STATUS_ACCEPTED = 'accepted'

# the project has failed one of evaluations
STATUS_FAILED = 'failed'

# the project has been withdrawn
STATUS_WITHDRAWN = 'withdrawn'

# the project has been marked as invalid
STATUS_INVALID = 'invalid'


class GSoCProject(db.Model):
  """Model for a GSoC project used in the GSoC workflow.

  Parent:
    soc.modules.gsoc.models.profile.Profile
  """

  #: Required field indicating the "title" of the project
  title = db.StringProperty(required=True,
      verbose_name=ugettext('Title'))
  title.help_text = ugettext('Title of the project')

  #: Required, text field describing the project
  abstract = db.TextProperty(
      required=True, verbose_name=ugettext('Project abstract'))
  abstract.help_text = ugettext(
      'Short abstract, summary, or snippet;'
      ' 500 characters or less, plain text displayed publicly')

  #: Text field containing all kinds of information about this project
  public_info = db.TextProperty(
      required=False, default='',
      verbose_name=ugettext('Additional information'))
  public_info.help_text = ugettext(
      'Additional information about this project to be shown publicly')

  #: Optional, URL which can give more information about this project
  additional_info = db.URLProperty(
      required=False, verbose_name=ugettext('External resource URL'))
  additional_info.help_text = ugettext(
      'Link to a resource containing more information about this project.')

  #: Optional field storing a feed URL; displayed publicly
  feed_url = db.LinkProperty(
      verbose_name=ugettext('Project Feed URL'))
  feed_url.help_text = ugettext(
      'The URL should be a valid ATOM or RSS feed. '
      'Feed entries are shown on the public page.')

  #: The project can be marked to be featured on program home page.
  is_featured = db.BooleanProperty(default=False, required=True,
                                   verbose_name=ugettext('Featured'))
  is_featured.help_text = ugettext(
      'Should this project be featured on the program homepage.')

  #: A property containing a list of Mentors assigned for this project
  mentors = db.ListProperty(item_type=db.Key, default=[], required=True)

  def getMentors(self):
    """Returns a list of profile_model.GSoCProfile entities which
    are mentors for this project.

    Returns:
      list of mentors for this project
    """
    mentor_ndb_keys = map(ndb.Key.from_old_key, self.mentors)
    return [mentor for mentor in ndb.get_multi(mentor_ndb_keys) if mentor]

  #: The status of this project
  status = db.StringProperty(required=True, default=STATUS_ACCEPTED,
      choices=[STATUS_ACCEPTED, STATUS_FAILED,
          STATUS_WITHDRAWN, STATUS_INVALID])

  #: List of all processed GradingRecords which state a pass for this project.
  #: This property can be used to determine how many evaluations someone has
  #: passed. And is also used to ensure that a GradingRecord has been
  #: processed.
  passed_evaluations = db.ListProperty(item_type=db.Key, default=[])

  #: List of all processed GradingRecords which state a fail for this project.
  #: This is a ListProperty to ensure that the system keeps functioning when
  #: manual changes in GradingRecords occur.
  failed_evaluations = db.ListProperty(item_type=db.Key, default=[])

  #: Organization which this project is in
  org = db.ReferenceProperty(
      reference_class=soc.models.organization.Organization,
      required=True, collection_name='student_projects')

  #: Program in which this project has been created
  program = db.ReferenceProperty(
      reference_class=soc.models.program.Program, required=True,
      collection_name='projects')

  #: Proposal to which this project corresponds to
  proposal = db.ReferenceProperty(
      reference_class=soc.modules.gsoc.models.proposal.GSoCProposal,
      required=False,
      collection_name='projects')

  #: Whether the student has submitted their code samples or not
  code_samples_submitted = db.BooleanProperty(default=False)

  def codeSamples(self):
    """Returns code_sample.GSoCCodeSample entities uploaded for this project.

    Returns:
      code sample entities for this project
    """
    query = code_sample_model.GSoCCodeSample.all()
    query.ancestor(self)
    return query.fetch(1000)

  def countCodeSamples(self):
    """Returns number of code_sample.GSoCCodeSample entities uploaded
    for this project.

    Returns:
      number of code samples uploaded for this project
    """
    query = code_sample_model.GSoCCodeSample.all(keys_only=True)
    query.ancestor(self)
    return query.count()
