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

"""Module containing the GCI Callback."""

from soc.modules.gci.models import program as gci_program_model
from soc.modules.gci.tasks import bulk_create as bulk_create_tasks
from soc.modules.gci.tasks import ranking_update as ranking_update_tasks
from soc.modules.gci.tasks import score_update as score_update_tasks
from soc.modules.gci.tasks import task_update as task_update_tasks
from soc.modules.gci.views import accepted_orgs
from soc.modules.gci.views import admin
from soc.modules.gci.views import age_check
from soc.modules.gci.views import all_tasks
from soc.modules.gci.views import bulk_create
from soc.modules.gci.views import dashboard
from soc.modules.gci.views import delete_account
from soc.modules.gci.views import document
from soc.modules.gci.views import homepage
from soc.modules.gci.views import invite
from soc.modules.gci.views import leaderboard
from soc.modules.gci.views import moderate_delete_account
from soc.modules.gci.views import org_app
from soc.modules.gci.views import org_home
from soc.modules.gci.views import org_profile
from soc.modules.gci.views import org_score
from soc.modules.gci.views import participants
from soc.modules.gci.views import profile
from soc.modules.gci.views import profile_show
from soc.modules.gci.views import program
from soc.modules.gci.views import propose_winners
from soc.modules.gci.views import request
from soc.modules.gci.views import static_content
from soc.modules.gci.views import student_forms
from soc.modules.gci.views import students_info
from soc.modules.gci.views import task
from soc.modules.gci.views import task_list
from soc.modules.gci.views import task_create
from soc.modules.gci.views import subscribed_tasks
from soc.modules.gci.views import conversations
from soc.modules.gci.views import conversation
from soc.modules.gci.views import conversation_create


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
    self.views.append(accepted_orgs.AcceptedOrgsPage())
    self.views.append(accepted_orgs.AcceptedOrgsAdminPage())
    self.views.append(admin.DashboardPage())
    self.views.append(admin.LookupLinkIdPage())
    self.views.append(all_tasks.TaskListPage())
    self.views.append(age_check.AgeCheck())
    self.views.append(bulk_create.BulkCreate())
    self.views.append(dashboard.DashboardPage())
    self.views.append(delete_account.DeleteAccountPage())
    self.views.append(document.DocumentPage())
    self.views.append(document.EditDocumentPage())
    self.views.append(document.EventsPage())
    self.views.append(document.DocumentListPage())
    self.views.append(homepage.Homepage())
    self.views.append(invite.InvitePage())
    self.views.append(invite.ManageInvite())
    self.views.append(invite.RespondInvite())
    self.views.append(invite.ListUserInvitesPage())
    self.views.append(leaderboard.LeaderboardPage())
    self.views.append(leaderboard.StudentTasksPage())
    self.views.append(subscribed_tasks.SubscribedTasksPage())
    self.views.append(moderate_delete_account.ModerateDeleteAccountPage())
    self.views.append(org_app.GCIOrgAppEditPage())
    self.views.append(org_profile.OrgProfilePage())
    self.views.append(org_app.GCIOrgAppPreviewPage())
    self.views.append(org_app.GCIOrgAppRecordsList())
    self.views.append(org_app.GCIOrgAppShowPage())
    self.views.append(org_app.GCIOrgAppTakePage())
    self.views.append(org_home.GCIBanOrgPost())
    self.views.append(org_home.OrgHomepage())
    self.views.append(org_score.ChooseOrganizationForOrgScorePage())
    self.views.append(org_score.OrgScoresForOrgzanizationPage())
    self.views.append(participants.MentorsListAdminPage())
    self.views.append(profile.GCIProfilePage())
    self.views.append(profile_show.GCIProfileShowPage())
    self.views.append(profile_show.GCIProfileShowAdminPage())
    self.views.append(program.GCICreateProgramPage())
    self.views.append(program.GCIEditProgramPage())
    self.views.append(program.GCIProgramMessagesPage())
    self.views.append(program.TimelinePage())
    self.views.append(propose_winners.ProposeWinnersPage())
    self.views.append(
        propose_winners.ChooseOrganizationForProposeWinnersPage())
    self.views.append(propose_winners.ViewProposedWinnersPage())
    self.views.append(request.ListUserRequestsPage())
    self.views.append(request.SendRequestPage())
    self.views.append(request.ManageRequestPage())
    self.views.append(request.RespondRequestPage())
    self.views.append(static_content.StaticContentUpload())
    self.views.append(static_content.StaticContentDownload())
    self.views.append(student_forms.StudentFormUpload())
    self.views.append(student_forms.StudentFormDownload())
    self.views.append(students_info.StudentsInfoPage())
    self.views.append(task.TaskViewPage())
    self.views.append(task.WorkSubmissionDownload())
    self.views.append(task_list.AllOrganizationTasksPage())
    self.views.append(task_list.ChooseOrganizationPage())
    self.views.append(task_list.StudentTasksForOrganizationPage())
    self.views.append(task_list.TaskListPage())
    self.views.append(task_create.TaskCreatePage())
    self.views.append(conversations.ConversationsPage())
    self.views.append(conversation.ConversationPage())
    self.views.append(conversation.PostReply())
    self.views.append(conversation_create.ConversationCreatePage())

    # Google Appengine Tasks
    self.views.append(bulk_create_tasks.BulkCreateTask())
    self.views.append(ranking_update_tasks.RankingUpdater())
    self.views.append(task_update_tasks.TaskUpdate())
    self.views.append(score_update_tasks.ScoreUpdate())

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered."""
    self.core.requireUniqueService('registerWithSitemap')

    # Redesigned view registration
    for view in self.views:
      self.core.registerSitemapEntry(view.djangoURLPatterns())

  def registerWithProgramMap(self):
    """Called by the server when program_map entries should be registered."""
    self.core.requireUniqueService('registerWithProgramMap')

    program_entities = gci_program_model.GCIProgram.all().fetch(1000)
    program_map = ('GCI Programs', [
        (str(e.key()), e.name) for e in program_entities])

    self.core.registerProgramEntry(program_map)
