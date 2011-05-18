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

"""Module containing the GSoC Callback.
"""

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com>',
    '"Leo (Chong Liu)" <HiddenPython@gmail.com>',
    '"Sverre Rabbelier" <sverre@rabbelier.nl>',
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


class Callback(object):
  """Callback object that handles interaction between the core.
  """

  API_VERSION = 1

  def __init__(self, core):
    """Initializes a new Callback object for the specified core.
    """

    self.core = core
    self.views = []

  def registerViews(self):
    """Instantiates all view objects.
    """
    from soc.modules.gsoc.views import accepted_orgs
    from soc.modules.gsoc.views import admin
    from soc.modules.gsoc.views import dashboard
    from soc.modules.gsoc.views import document
    from soc.modules.gsoc.views import duplicates
    from soc.modules.gsoc.views import homepage
    from soc.modules.gsoc.views import invite
    #from soc.modules.gsoc.views import org_app
    from soc.modules.gsoc.views import org_home
    from soc.modules.gsoc.views import org_profile
    from soc.modules.gsoc.views import profile
    from soc.modules.gsoc.views import profile_show
    from soc.modules.gsoc.views import program
    from soc.modules.gsoc.views import project_details
    from soc.modules.gsoc.views import project_evaluation
    from soc.modules.gsoc.views import projects_list
    from soc.modules.gsoc.views import proposal
    from soc.modules.gsoc.views import proposal_review
    from soc.modules.gsoc.views import request
    from soc.modules.gsoc.views import search
    from soc.modules.gsoc.views import slot_transfer
    from soc.modules.gsoc.views import slot_transfer_admin
    from soc.modules.gsoc.views import student_forms

    self.views.append(accepted_orgs.AcceptedOrgsPage())
    self.views.append(admin.DashboardPage())
    self.views.append(admin.LookupLinkIdPage())
    self.views.append(admin.SlotsPage())
    self.views.append(dashboard.Dashboard())
    self.views.append(document.DocumentPage())
    self.views.append(document.EditDocumentPage())
    self.views.append(document.EventsPage())
    self.views.append(duplicates.DuplicatesPage())
    self.views.append(homepage.Homepage())
    self.views.append(invite.InvitePage())
    self.views.append(invite.ShowInvite())
    #self.views.append(org_app.OrgApp())
    self.views.append(org_home.OrgHome())
    self.views.append(org_profile.OrgProfilePage())
    self.views.append(profile.ProfilePage())
    self.views.append(profile_show.ProfileAdminPage())
    self.views.append(profile_show.ProfileShowPage())
    self.views.append(program.ProgramPage())
    self.views.append(program.TimelinePage())
    self.views.append(project_details.AssignMentor())
    self.views.append(project_details.FeaturedProject())
    self.views.append(project_details.ProjectDetails())
    self.views.append(project_details.ProjectDetailsUpdate())
    self.views.append(project_evaluation.SurveyEditPage())
    self.views.append(project_evaluation.SurveyTakePage())
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
    self.views.append(request.RequestPage())
    self.views.append(request.ShowRequest())
    self.views.append(search.SearchGsocPage())
    self.views.append(slot_transfer_admin.SlotsTransferAdminPage())
    self.views.append(slot_transfer.SlotTransferPage())
    self.views.append(slot_transfer.UpdateSlotTransferPage())
    self.views.append(student_forms.DownloadEnrollmentForm())
    self.views.append(student_forms.DownloadTaxForm())
    self.views.append(student_forms.EnrollmentFormPage())
    self.views.append(student_forms.TaxFormPage())

    # Appengine Task related views
    from soc.modules.gsoc.tasks.accept_proposals import \
        ProposalAcceptanceTask
    from soc.modules.gsoc.tasks.proposal_duplicates import \
        ProposalDuplicatesTask
    from soc.modules.gsoc.tasks.survey_reminders import \
        SurveyReminderTask
    self.views.append(ProposalAcceptanceTask())
    self.views.append(ProposalDuplicatesTask())
    self.views.append(SurveyReminderTask())

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered.
    """

    self.core.requireUniqueService('registerWithSitemap')

    # Redesigned view registration
    for view in self.views:
      self.core.registerSitemapEntry(view.djangoURLPatterns())

  def registerWithProgramMap(self):
    """Called by the server when program_map entries should be registered.
    """

    self.core.requireUniqueService('registerWithProgramMap')

    from soc.modules.gsoc.models.program import GSoCProgram
    program_entities = GSoCProgram.all().fetch(1000)
    map = ('GSoC Programs', [
        (str(e.key()), e.name) for e in program_entities])

    self.core.registerProgramEntry(map)
