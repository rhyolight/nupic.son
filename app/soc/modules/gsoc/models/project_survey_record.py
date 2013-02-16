#!/usr/bin/env python2.5
#
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

"""GSoCProjectSurveyRecord allows linking two result sets by GSoCProject.
"""

from google.appengine.ext import db

from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.project import GSoCProject


class GSoCProjectSurveyRecord(SurveyRecord):
  """Record linked to a Project, enabling to store which Projects had their
  Survey done.
  """

  #: Reference to the Project that this record belongs to.
  project = db.ReferenceProperty(
      reference_class=GSoCProject,
      required=True, collection_name='gsoc_survey_records')

  #: A many:1 relationship associating ProjectSurveyRecords 
  #: with specific GSoCOrganization.
  org = db.ReferenceProperty(
      reference_class=GSoCOrganization, 
      required=False, collection_name='gsoc_survey_records')
