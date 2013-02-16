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

from soc.models import survey_record

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import project as project_model


class GSoCProjectSurveyRecord(survey_record.SurveyRecord):
  """Record linked to a GSoCProject, enabling to store which
  projects have had their Survey done.
  """

  #: Reference to the GSoCProject that this record belongs to.
  project = db.ReferenceProperty(
      reference_class=project_model.GSoCProject,
      required=True, collection_name='gsoc_survey_records')

  #: A many:1 relationship associating GSoCProjectSurveyRecords 
  #: with specific GSoCOrganization.
  org = db.ReferenceProperty(
      reference_class=org_model.GSoCOrganization, 
      required=False, collection_name='gsoc_survey_records')
