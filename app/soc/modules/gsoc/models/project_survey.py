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

"""This module contains the ProjectSurvey model."""

from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.models import survey as survey_model


# type representing midterm student evaluations
MIDTERM_EVAL = 'midterm'
# type representing final student evaluations
FINAL_EVAL = 'final'

# list containing all survey types of this kind
SURVEY_TYPES = [MIDTERM_EVAL, FINAL_EVAL]


class ProjectSurvey(survey_model.Survey):
  """Survey for Students that have a project."""

  #: Required field storing "ID" used in URL links. ASCII characters,
  #: digits and underscores only.  Valid link IDs successfully match
  #: the LINK_ID_REGEX.
  # TODO(daniel): this sould be replaced by survey_type field, as this is
  # what actually link_id stands for here
  link_id = db.StringProperty(required=True,
      verbose_name=ugettext('Organization ID'))
  link_id.help_text = ugettext(
      'Organization ID is used as part of various URL links throughout the site.'
      ' <a href="http://en.wikipedia.org/wiki/ASCII">ASCII</a> '
      ' Unique Name, alphanumeric characters, digits, and underscores only.')

  @property
  def survey_type(self):
    """Returns type of the project survey.

    Returns:
      type of the project survey: one of MIDTERM_EVAL or FINAL_EVAL.
    """
    return self.link_id
