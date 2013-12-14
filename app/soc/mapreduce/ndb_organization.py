#!/usr/bin/env python
#
# Copyright 2013 the Melange authors.
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

"""MapReduce scripts that convert reference properties to organizations
so that they point to 'SOCOrganization' type.
"""

from google.appengine.ext import db

from soc.modules.gsoc.models import grading_project_survey_record as grading_project_survey_record_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import project_survey_record as project_survey_record_model
from soc.modules.gsoc.models import proposal as proposal_model

from summerofcode.models import organization as org_model

@db.transactional
def convertProposalTxn(proposal_key):
  proposal = proposal_model.GSoCProposal.get(proposal_key)

  new_key = db.Key.from_path(
      org_model.SOCOrganization._get_kind(),
      proposal_model.GSoCProposal.org.get_value_for_datastore(proposal).name())

  proposal.org = new_key
  proposal.put()


@db.transactional
def convertProjectTxn(project_key):
  project = project_model.GSoCProject.get(project_key)

  new_key = db.Key.from_path(
      org_model.SOCOrganization._get_kind(),
      project_model.GSoCProject.org.get_value_for_datastore(project).name())

  project.org = new_key
  project.put()


@db.transactional
def convertProjectSurveyRecordTxn(project_survey_recod_key):
  project_survey_record = (project_survey_record_model.GSoCProjectSurveyRecord
      .get(project_survey_recod_key))

  new_key = db.Key.from_path(
      org_model.SOCOrganization._get_kind(),
      project_survey_record_model.GSoCProjectSurveyRecord.org
          .get_value_for_datastore(project_survey_record).name())

  project_survey_record.org = new_key
  project_survey_record.put()


@db.transactional
def convertGradingProjectSurveyRecordTxn(grading_project_survey_recod_key):
  grading_project_survey_record = (
      grading_project_survey_record_model.GSoCGradingProjectSurveyRecord
          .get(grading_project_survey_recod_key))

  new_key = db.Key.from_path(
      org_model.SOCOrganization._get_kind(),
      grading_project_survey_record_model.GSoCGradingProjectSurveyRecord.org
          .get_value_for_datastore(grading_project_survey_record).name())

  grading_project_survey_record.org = new_key
  grading_project_survey_record.put()
