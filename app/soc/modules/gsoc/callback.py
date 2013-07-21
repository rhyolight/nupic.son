# Copyright 2009 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the GSoC Callback."""

from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.tasks import grading_survey_group as grading_survey_group_tasks
from soc.modules.gsoc.tasks import accept_proposals as accept_proposals_tasks
from soc.modules.gsoc.tasks import proposal_duplicates as proposal_duplicates_tasks
from soc.modules.gsoc.tasks import survey_reminders as survey_reminders_tasks
from soc.modules.gsoc.views import accept_proposals
from soc.modules.gsoc.views import accept_withdraw_projects
from soc.modules.gsoc.views import accepted_orgs
from soc.modules.gsoc.views import admin
from soc.modules.gsoc.views import connection
from soc.modules.gsoc.views import dashboard
from soc.modules.gsoc.views import document
from soc.modules.gsoc.views import duplicates
from soc.modules.gsoc.views import grading_record_details
from soc.modules.gsoc.views import homepage
from soc.modules.gsoc.views import mentor_evaluation
from soc.modules.gsoc.views import org_app
from soc.modules.gsoc.views import org_home
from soc.modules.gsoc.views import org_profile
from soc.modules.gsoc.views import profile
from soc.modules.gsoc.views import profile_show
from soc.modules.gsoc.views import program
from soc.modules.gsoc.views import project_details
from soc.modules.gsoc.views import projects_list
from soc.modules.gsoc.views import proposal
from soc.modules.gsoc.views import proposal_review
from soc.modules.gsoc.views import search
from soc.modules.gsoc.views import slot_allocation
from soc.modules.gsoc.views import slot_transfer
from soc.modules.gsoc.views import slot_transfer_admin
from soc.modules.gsoc.views import student_evaluation
from soc.modules.gsoc.views import student_forms
from soc.modules.gsoc.views import oauth


class Callback(object):
  """Callback object that handles interaction between the core."""

  # This constant is required by soc.modules.core module. If its values
  # does not match the one defined there, the callback is rejected.
  API_VERSION = 1

  def __init__(self, core):
    """Initializes a new Callback object for the specified core."""

    self.core = core
    self.views = []

  def registerViews(self):
    """Instantiates all view objects."""
    self.views.append(accept_proposals.AcceptProposalsPage())
    self.views.append(accept_withdraw_projects.AcceptProposals())
    self.views.append(accept_withdraw_projects.WithdrawProjects())
    self.views.append(accepted_orgs.AcceptedOrgsPublicPage())
    self.views.append(accepted_orgs.AcceptedOrgsAdminPage())
    self.views.append(admin.DashboardPage())
    self.views.append(admin.LookupLinkIdPage())
    self.views.append(admin.ManageProjectsListPage())
    self.views.append(admin.ProjectsPage())
    self.views.append(admin.ProjectsListPage())
    self.views.append(admin.ProposalsPage())
    self.views.append(admin.StudentsListPage())
    self.views.append(admin.SurveyReminderPage())
    self.views.append(connection.OrgConnectionPage())
    self.views.append(connection.UserConnectionPage())
    self.views.append(connection.ShowConnection())
    self.views.append(connection.SubmitConnectionMessagePost())
    self.views.append(dashboard.DashboardPage())
    self.views.append(document.DocumentPage())
    self.views.append(document.DocumentListPage())
    self.views.append(document.EditDocumentPage())
    self.views.append(document.EventsPage())
    self.views.append(duplicates.DuplicatesPage())
    self.views.append(grading_record_details.GradingGroupCreate())
    self.views.append(grading_record_details.GradingRecordDetails())
    self.views.append(grading_record_details.GradingRecordsOverview())
    self.views.append(homepage.Homepage())
    self.views.append(mentor_evaluation.GSoCMentorEvaluationEditPage())
    self.views.append(mentor_evaluation.GSoCMentorEvaluationPreviewPage())
    self.views.append(mentor_evaluation.GSoCMentorEvaluationRecordsList())
    self.views.append(mentor_evaluation.GSoCMentorEvaluationShowPage())
    self.views.append(mentor_evaluation.GSoCMentorEvaluationTakePage())
    self.views.append(org_app.GSoCOrgAppEditPage())
    self.views.append(org_app.GSoCOrgAppPreviewPage())
    self.views.append(org_app.GSoCOrgAppRecordsList())
    self.views.append(org_app.GSoCOrgAppShowPage())
    self.views.append(org_app.GSoCOrgAppTakePage())
    self.views.append(org_home.OrgHome())
    self.views.append(org_home.GSoCBanOrgPost())
    self.views.append(org_profile.OrgProfilePage())
    self.views.append(profile.GSoCProfilePage())
    self.views.append(profile_show.GSoCBanProfilePost())
    self.views.append(profile_show.GSoCProfileAdminPage())
    self.views.append(profile_show.GSoCProfileShowPage())
    self.views.append(program.GSoCCreateProgramPage())
    self.views.append(program.GSoCEditProgramPage())
    self.views.append(program.GSoCProgramMessagesPage())
    self.views.append(program.TimelinePage())
    self.views.append(project_details.AssignMentors())
    self.views.append(project_details.CodeSampleDeleteFilePost())
    self.views.append(project_details.CodeSampleDownloadFileGet())
    self.views.append(project_details.CodeSampleUploadFilePost())
    self.views.append(project_details.FeaturedProject())
    self.views.append(project_details.ProjectDetails())
    self.views.append(project_details.ProjectDetailsUpdate())
    self.views.append(projects_list.ListProjects())
    self.views.append(proposal.ProposalPage())
    self.views.append(proposal_review.AcceptProposal())
    self.views.append(proposal_review.AssignMentor())
    self.views.append(proposal_review.IgnoreProposal())
    self.views.append(proposal_review.PostComment())
    self.views.append(proposal_review.PostScore())
    self.views.append(proposal_review.ProposalModificationPostDeadline())
    self.views.append(proposal_review.ProposalPubliclyVisible())
    self.views.append(proposal_review.ReviewProposal())
    self.views.append(proposal_review.WishToMentor())
    self.views.append(proposal_review.WithdrawProposal())
    self.views.append(proposal.UpdateProposal())
    self.views.append(search.SearchGsocPage())
    self.views.append(slot_allocation.SlotsPage())
    self.views.append(slot_transfer_admin.SlotsTransferAdminPage())
    self.views.append(slot_transfer.SlotTransferPage())
    self.views.append(slot_transfer.UpdateSlotTransferPage())
    self.views.append(student_evaluation.GSoCStudentEvaluationEditPage())
    self.views.append(student_evaluation.GSoCStudentEvaluationPreviewPage())
    self.views.append(student_evaluation.GSoCStudentEvaluationRecordsList())
    self.views.append(student_evaluation.GSoCStudentEvaluationShowPage())
    self.views.append(student_evaluation.GSoCStudentEvaluationTakePage())
    self.views.append(student_forms.DownloadForm())
    self.views.append(student_forms.FormPage())
    self.views.append(oauth.OAuthRedirectPage())
    self.views.append(oauth.OAuthVerifyToken())

    # Appengine Task related views
    self.views.append(grading_survey_group_tasks.GradingRecordTasks())
    self.views.append(accept_proposals_tasks.ProposalAcceptanceTask())
    self.views.append(proposal_duplicates_tasks.ProposalDuplicatesTask())
    self.views.append(survey_reminders_tasks.SurveyReminderTask())

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered."""
    self.core.requireUniqueService('registerWithSitemap')

    # Redesigned view registration
    for view in self.views:
      self.core.registerSitemapEntry(view.djangoURLPatterns())

  def registerWithProgramMap(self):
    """Called by the server when program_map entries should be registered."""
    self.core.requireUniqueService('registerWithProgramMap')

    program_entities = program_model.GSoCProgram.all().fetch(1000)
    program_map = ('GSoC Programs', [
        (str(e.key()), e.name) for e in program_entities])

    self.core.registerProgramEntry(program_map)
