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

"""Module for the GSoC proposal page."""

import httplib

from google.appengine.ext import db

from django import http
from django.core.urlresolvers import resolve
from django.core.urlresolvers import reverse
from django import forms as django_forms
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic import exceptions
from soc.views.helper import url as url_helper
from soc.views.helper.access_checker import isSet
from soc.views.template import Template
from soc.views.toggle_button import ToggleButtonTemplate
from soc.tasks import mailer

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.logic.helper import notifications
from soc.modules.gsoc.models.comment import GSoCComment
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.score import GSoCScore
from soc.modules.gsoc.views import assign_mentor
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


class CommentForm(GSoCModelForm):
  """Django form for the comment."""

  class Meta:
    model = GSoCComment
    #css_prefix = 'gsoc_comment'
    fields = ['content']

  def clean_content(self):
    field_name = 'content'
    wrapped_clean_html_content = cleaning.clean_html_content(field_name)
    content = wrapped_clean_html_content(self)
    if content:
      return content
    else:
      raise django_forms.ValidationError(
          ugettext('Comment content cannot be empty.'), code='invalid')

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/_comment_form.html'


class PrivateCommentForm(CommentForm):
  """Django form for the comment.
  """

  class Meta:
    model = GSoCComment
    fields = CommentForm.Meta.fields + ['is_private']


class Duplicate(Template):
  """Template for showing a duplicates to the org admin.
  """

  def __init__(self, data, duplicate):
    """Instantiates the template for rendering duplicates for a single
    proposal.

    Args:
      data: RequestData object
      duplicate: GSoCProposalDuplicate entity to render.
    """
    self.duplicate = duplicate
    super(Duplicate, self).__init__(data)

  def context(self):
    """The context for this template used in render()."""
    orgs = []
    for org in db.get(self.duplicate.orgs):
      admins = profile_logic.getOrgAdmins(org)

      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=org)

      data = {'name': org.name,
              'link': self.data.redirect.urlOf(url_names.GSOC_ORG_HOME),
              'admins': admins}

      orgs.append(data)

    context = {'orgs': orgs}

    return context

  def templatePath(self):
    return 'v2/modules/gsoc/duplicates/proposal_duplicate_review.html'


class UserActions(Template):
  """Template to render the left side user actions.
  """

  DEF_ACCEPT_PROPOSAL_HELP = ugettext(
      'Choosing Yes will mark this proposal as accepted. The proposal is '
      'accepted when Yes is displayed in bright orange.')

  DEF_IGNORE_PROPOSAL_HELP = ugettext(
      'Choosing Yes will mark this proposal as ignored. The student will be '
      'be able to see that this proposal is ignored when he/she visits this '
      'page. The proposal is ignored when Yes is displayed in bright orange.')

  DEF_IGNORE_PROPOSAL_NOTE = ugettext(
      'Please refresh this page after setting this preference.')

  DEF_PROPOSAL_MODIFICATION_HELP = ugettext(
      'Choosing Enabled allows the student to edit this proposal. The '
      'student can edit the proposal when Enabled is displayed in bright '
      'orange.')

  DEF_PUBLICLY_VISIBLE_HELP = ugettext(
      'Choosing Yes will make this proposal publicly visible. The proposal '
      'will be visible to even those who do not have a user account on this '
      'site. The proposal is publicly visible when Yes is displayed in '
      'bright orange')

  DEF_WISH_TO_MENTOR_HELP = ugettext(
      'Choosing Yes will add your name to the list of possible mentors to '
      'this proposal. You will be listed as a possible mentor when Yes is '
      'displayed in bright orange.')

  DEF_WITHDRAW_PROPOSAL_HELP = ugettext(
      'Choosing Yes, notifies your organization that you have withdrawn '
      'this proposal and no longer wish to participate in the program with '
      'this proposal. The proposal is withdrawn when the button displays '
      'Yes in bright orange.')

  def __init__(self, data, user_role):
    super(UserActions, self).__init__(data)
    self.user_role = user_role
    self.toggle_buttons = []

  def _mentorContext(self):
    """Construct the context needed for mentor actions.
    """
    r = self.data.redirect.review()

    wish_to_mentor = ToggleButtonTemplate(
        self.data, 'on_off', 'Wish to Mentor', 'wish-to-mentor',
        r.urlOf('gsoc_proposal_wish_to_mentor'),
        checked=self.data.isPossibleMentorForProposal(),
        help_text=self.DEF_WISH_TO_MENTOR_HELP,
        labels = {
            'checked': 'Yes',
            'unchecked': 'No'})
    self.toggle_buttons.append(wish_to_mentor)

    if self.data.timeline.afterStudentSignupEnd():
      proposal_modification_button = ToggleButtonTemplate(
          self.data, 'long', 'Proposal Modifications', 'proposal-modification',
          r.urlOf('gsoc_proposal_modification'),
          checked=self.data.proposal.is_editable_post_deadline,
          help_text=self.DEF_PROPOSAL_MODIFICATION_HELP,
          labels = {
            'checked': 'Enabled',
            'unchecked': 'Disabled'})
      self.toggle_buttons.append(proposal_modification_button)

    return {}

  def _orgAdminContext(self):
    """Construct the context needed for org admin actions.
    """
    context = {}
    r = self.data.redirect.review()

    ignore_button_checked = False
    if self.data.proposal.status == 'ignored':
      ignore_button_checked = True
    if self.data.proposal.status in ['pending', 'ignored']:
      ignore_proposal = ToggleButtonTemplate(
          self.data, 'on_off', 'Ignore Proposal', 'proposal-ignore',
          r.urlOf('gsoc_proposal_ignore'),
          checked=ignore_button_checked,
          help_text=self.DEF_IGNORE_PROPOSAL_HELP,
          note=self.DEF_IGNORE_PROPOSAL_NOTE,
          labels={
              'checked': 'Yes',
              'unchecked': 'No'})
      self.toggle_buttons.append(ignore_proposal)

    if not self.proposal_ignored:
      accept_proposal = ToggleButtonTemplate(
          self.data, 'on_off', 'Accept proposal', 'accept-proposal',
          r.urlOf('gsoc_proposal_accept'),
          checked=self.data.proposal.accept_as_project,
          help_text=self.DEF_ACCEPT_PROPOSAL_HELP,
          labels = {
              'checked': 'Yes',
              'unchecked': 'No',})
      self.toggle_buttons.append(accept_proposal)

      r = self.data.redirect
      possible_mentors_keys = self.data.proposal.possible_mentors
      all_mentors_keys = profile_logic.queryAllMentorsKeysForOrg(
          self.data.proposal_org) if self.data.proposal_org.list_all_mentors \
          else []

      current_mentors = []
      if self.data.proposal.mentor:
        current_mentors.append(self.data.proposal.mentor.key())

      context['assign_mentor'] = assign_mentor.AssignMentorFields(
          self.data, current_mentors,
          r.review().urlOf('gsoc_proposal_assign_mentor'),
          all_mentors_keys, possible_mentors_keys)

    return context

  def _proposerContext(self):
    """Construct the context needed for proposer actions.
    """
    r = self.data.redirect.review()

    publicly_visible = ToggleButtonTemplate(
        self.data, 'on_off', 'Publicly Visible', 'publicly-visible',
        r.urlOf('gsoc_proposal_publicly_visible'),
        checked=self.data.proposal.is_publicly_visible,
        help_text=self.DEF_PUBLICLY_VISIBLE_HELP,
        labels = {
            'checked': 'Yes',
            'unchecked': 'No',})
    self.toggle_buttons.append(publicly_visible)

    if self.data.proposal.status in ['pending', 'withdrawn']:
      if self.data.proposal.status == 'withdrawn':
        checked=True
      elif self.data.proposal.status == 'pending':
        checked=False
      withdraw_proposal = ToggleButtonTemplate(
          self.data, 'on_off', 'Withdraw Proposal', 'withdraw-proposal',
          r.urlOf('gsoc_proposal_withdraw'), checked=checked,
          help_text=self.DEF_WITHDRAW_PROPOSAL_HELP,
          labels = {
              'checked': 'Yes',
              'unchecked': 'No',})
      self.toggle_buttons.append(withdraw_proposal)

    return {}

  def context(self):
    assert isSet(self.data.proposal)

    context = {
        'title': 'Proposal Actions',
        }

    self.proposal_ignored = self.data.proposal.status == 'ignored'

    if self.user_role == 'mentor' and not self.proposal_ignored:
      context.update(self._mentorContext())

    if self.user_role == 'org_admin':
      context.update(self._orgAdminContext())
      # org admin is a mentor by default so add that context and buttons
      # as well.
      if not self.proposal_ignored:
        context.update(self._mentorContext())

    if self.user_role == 'proposer':
      context.update(self._proposerContext())

    context['toggle_buttons'] = self.toggle_buttons

    return context

  def templatePath(self):
    return "v2/modules/gsoc/proposal/_user_action.html"


class ReviewProposal(GSoCRequestHandler):
  """View for the Propsal Review page."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/review/%s$' % url_patterns.REVIEW,
         self, name='review_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    check.canAccessProposalEntity()
    mutator.commentVisible(data.proposal_org)

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/review.html'

  def getScores(self, data):
    """Gets all the scores for the proposal."""
    assert isSet(data.private_comments_visible)
    assert isSet(data.proposal_org)
    assert isSet(data.proposal)

    if not data.private_comments_visible:
      return None

    total = 0
    number = 0
    user_score = 0

    query = db.Query(GSoCScore).ancestor(data.proposal)
    for score in query:
      total += score.value
      number += 1

      author_key = GSoCScore.author.get_value_for_datastore(score)
      if author_key == data.profile.key():
        user_score = score.value

    return {
        'average': total / number if number else 0,
        'number': number,
        'total': total,
        'user_score': user_score,
        }

  def getComments(self, data, limit=1000):
    """Gets all the comments for the proposal visible by the current user."""
    assert isSet(data.private_comments_visible)
    assert isSet(data.proposal)

    public_comments = []
    private_comments = []

    query = db.Query(GSoCComment).ancestor(data.proposal)
    query.order('created')
    all_comments = query.fetch(limit=limit)

    for comment in all_comments:
      if not comment.is_private:
        public_comments.append(comment)
      elif data.private_comments_visible:
        private_comments.append(comment)

    return public_comments, private_comments

  def sanitizePossibleMentors(self, data, possible_mentors):
    """Removes possible mentors that are no longer mentors."""
    changed = False

    result = []

    for mentor in possible_mentors:
      if data.proposal_org.key() in mentor.mentor_for:
        result.append(mentor)
        continue

      changed = True
      data.proposal.possible_mentors.remove(mentor.key())

    if changed:
      data.proposal.put()

    return result

  def context(self, data, check, mutator):
    assert isSet(data.public_comments_visible)
    assert isSet(data.private_comments_visible)
    assert isSet(data.url_profile)
    assert isSet(data.url_user)
    assert isSet(data.proposal)

    context = {}

    user_role = None

    scores = self.getScores(data)

    # TODO: check if the scoring is not disabled
    score_action = reverse('score_gsoc_proposal', kwargs=data.kwargs)

    # get all the comments for the the proposal
    public_comments, private_comments = self.getComments(data)

    # TODO: check if it is possible to post a comment
    comment_action = reverse('comment_gsoc_proposal', kwargs=data.kwargs)

    if data.private_comments_visible:

      # only mentors and org admins can see that the proposal is ignored
      # TODO(daniel): replace status literals with constants
      context['proposal_ignored'] = data.proposal.status == 'ignored'

      form = PrivateCommentForm(data.POST or None)
      if data.orgAdminFor(data.proposal.org):
        user_role = 'org_admin'
      else:
        user_role = 'mentor'

    else:
      form = CommentForm(data.POST or None)

    comment_box = {
        'action': comment_action,
        'form': form,
    }

    # to keep the blocks as simple as possible, the if branches have
    # been broken down into several if blocks
    user_is_proposer = data.user and (data.user.key() == data.url_user.key())
    if user_is_proposer:
      user_role = 'proposer'

      # we will check if the student is allowed to modify the proposal
      # after the student proposal deadline
      is_editable = data.timeline.afterStudentSignupEnd() and \
          data.proposal.is_editable_post_deadline
      if data.timeline.studentSignup() or is_editable:
        data.redirect.proposal(
            id=data.proposal.key().id(), student=data.proposer.link_id)
        context['update_link'] = data.redirect.urlOf('update_gsoc_proposal')

    possible_mentors = db.get(data.proposal.possible_mentors)
    possible_mentors = self.sanitizePossibleMentors(data, possible_mentors)
    possible_mentors_names = ', '.join([m.name() for m in possible_mentors])

    scoring_visible = data.private_comments_visible and (
        not data.proposal_org.scoring_disabled)

    if data.orgAdminFor(data.proposal_org):
      scoring_visible = True

    duplicate = None
    if data.program.duplicates_visible and data.orgAdminFor(data.proposal_org):
      q = GSoCProposalDuplicate.all()
      q.filter('duplicates', data.proposal)
      q.filter('is_duplicate', True)
      dup_entity = q.get()
      duplicate = Duplicate(data, dup_entity) if dup_entity else None

    additional_info = data.proposal.additional_info

    if user_role:
      context['user_actions'] = UserActions(data, user_role)

    context.update({
        'additional_info': url_helper.trim_url_to(additional_info, 50),
        'additional_info_link': additional_info,
        'comment_box': comment_box,
        'duplicate': duplicate,
        'max_score': data.proposal_org.max_score,
        'mentor': data.proposal.mentor,
        'page_name': data.proposal.title,
        'possible_mentors': possible_mentors_names,
        'private_comments': private_comments,
        'private_comments_visible': data.private_comments_visible,
        'proposal': data.proposal,
        'public_comments': public_comments,
        'public_comments_visible': data.public_comments_visible,
        'score_action': score_action,
        'scores': scores,
        'scoring_visible': scoring_visible,
        'student_email': data.url_profile.email,
        'student_name': data.url_profile.name(),
        'user_role': user_role,
        })

    return context


class PostComment(GSoCRequestHandler):
  """View which handles publishing comments."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/comment/%s$' % url_patterns.REVIEW,
         self, name='comment_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.isProfileActive()
    mutator.proposalFromKwargs()
    mutator.commentVisible(data.organization)
    assert isSet(data.proposer)
    assert isSet(data.proposal_org)

    # check if the comment is given by the author of the proposal
    if data.proposer.key() == data.profile.key():
      data.public_only = True
      return

    data.public_only = False
    check.isMentorForOrganization(data.proposal_org)

  def createCommentFromForm(self, data):
    """Creates a new comment based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created comment entity or None
    """
    assert isSet(data.public_only)
    assert isSet(data.proposal)

    if data.public_only:
      comment_form = CommentForm(data.request.POST)
    else:
      # this form contains checkbox for indicating private/public comments
      comment_form = PrivateCommentForm(data.request.POST)

    if not comment_form.is_valid():
      return None

    if data.public_only:
      comment_form.cleaned_data['is_private'] = False
    comment_form.cleaned_data['author'] = data.profile

    q = GSoCProfile.all().filter('mentor_for', data.proposal.org)
    q = q.filter('status', 'active')
    if comment_form.cleaned_data.get('is_private'):
      q.filter('notify_private_comments', True)
    else:
      q.filter('notify_public_comments', True)
    mentors = q.fetch(1000)

    to_emails = [i.email for i in mentors if i.key() != data.profile.key()]

    def create_comment_txn():
      comment = comment_form.create(commit=True, parent=data.proposal)
      context = notifications.newReviewContext(data, comment, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=comment)
      sub_txn()
      return comment

    return db.run_in_transaction(create_comment_txn)

  def post(self, data, check, mutator):
    assert isSet(data.proposer)
    assert isSet(data.proposal)

    comment = self.createCommentFromForm(data)
    if comment:
      data.redirect.program()
      return data.redirect.to('gsoc_dashboard', anchor='proposals_submitted')
    else:
      # This is an insanely and absolutely hacky solution. We definitely
      # do not want any one to use this a model for writing code elsewhere
      # in Melange.
      # TODO (Madhu): Replace this in favor of PJAX for loading comments.
      data.redirect.review(data.proposal.key().id(), data.proposer.link_id)
      redirect_url = data.redirect.urlOf('review_gsoc_proposal')
      proposal_match = resolve(redirect_url)
      proposal_view = proposal_match[0]
      data.request.method = 'GET'
      return proposal_view(data.request, *data.args, **data.kwargs)

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class PostScore(GSoCRequestHandler):
  """View which handles posting scores."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/score/%s$' % url_patterns.REVIEW,
         self, name='score_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    assert isSet(data.proposal_org)

    org = data.proposal_org

    if not data.orgAdminFor(org) and org.scoring_disabled:
      raise exceptions.BadRequest('Scoring is disabled for this organization')

    check.isMentorForOrganization(org)

  def createOrUpdateScore(self, data, value):
    """Creates a new score or updates a score if there is already one
    posted by the current user.

    If the value passed in is 0 then the Score of the user will be removed and
    None will be returned.

    Args:
      data: A RequestData describing the current request.
      value: The value of the score the user gave as an integer.

    Returns:
      The score entity that was created/updated or None if value is 0.
    """
    assert isSet(data.proposal)
    assert isSet(data.proposal_org)

    max_score = data.proposal_org.max_score

    if value < 0 or value > max_score:
      raise exceptions.BadRequest(
          "Score must not be higher than %d" % max_score)

    query = db.Query(GSoCScore)
    query.filter('author = ', data.profile)
    query.ancestor(data.proposal)

    def update_score_trx():
      delta = 0

      # update score entity
      score = query.get()
      if not score:
        if not value:
          return
        old_value = 0
        score = GSoCScore(
            parent=data.proposal,
            author=data.profile,
            value=value)
        score.put()
        delta = 1
      else:
        old_value = score.value
        if not value:
          delta = -1
          score.delete()
        else:
          score.value = value
          score.put()

      # update total score for the proposal
      proposal = db.get(data.proposal.key())
      proposal.score += value - old_value
      proposal.nr_scores += delta
      proposal.put()

    db.run_in_transaction(update_score_trx)

  def post(self, data, check, mutator):
    value_str = data.POST.get('value', '')
    value = int(value_str) if value_str.isdigit() else None
    self.createOrUpdateScore(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class WishToMentor(GSoCRequestHandler):
  """View handling wishing to mentor requests."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/wish_to_mentor/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_wish_to_mentor'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    assert isSet(data.proposal_org)

    check.isMentorForOrganization(data.proposal_org)

  def addToPotentialMentors(self, data, value):
    """Toggles the user from the potential mentors list.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.profile)
    assert isSet(data.proposal)

    if value != 'checked' and value != 'unchecked':
      raise exceptions.BadRequest("Invalid post data.")

    if value == 'checked' and not data.isPossibleMentorForProposal():
      raise exceptions.BadRequest("Invalid post data.")
    if value == 'unchecked' and data.isPossibleMentorForProposal():
      raise exceptions.BadRequest("Invalid post data.")

    proposal_key = data.proposal.key()
    profile_key = data.profile.key()

    def update_possible_mentors_trx():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'unchecked':
        # we have already been added
        if profile_key in proposal.possible_mentors:
          return
        proposal.possible_mentors.append(profile_key)
      else:
        # we have already been removed
        if profile_key not in proposal.possible_mentors:
          return
        proposal.possible_mentors.remove(profile_key)
      db.put(proposal)

    db.run_in_transaction(update_possible_mentors_trx)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.addToPotentialMentors(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class AssignMentor(GSoCRequestHandler):
  """View which handles assigning mentor to a proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/assign_mentor/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_assign_mentor'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    assert isSet(data.proposal_org)
    check.isOrgAdminForOrganization(data.proposal_org)

  def assignMentor(self, data, mentor_entity):
    """Assigns the mentor to the proposal.

    Args:
      data: A RequestData describing the current request.
      mentor_entity: The entity of the mentor profile which needs to assigned
          to the proposal.
    """
    assert isSet(data.proposal)

    proposal_key = data.proposal.key()

    def assign_mentor_txn():
      proposal = db.get(proposal_key)

      proposal.mentor = mentor_entity
      proposal.has_mentor = True

      db.put(proposal)

    db.run_in_transaction(assign_mentor_txn)

  def unassignMentor(self, data):
    """Removes the mentor assigned to the proposal.

    Args:
      data: A RequestData describing the current request.
    """
    assert isSet(data.proposal)

    proposal_key = data.proposal.key()

    def unassign_mentor_txn():
      proposal = db.get(proposal_key)
      proposal.mentor = None
      proposal.has_mentor = False
      db.put(proposal)

    db.run_in_transaction(unassign_mentor_txn)

  def validate(self, data):
    mentor_key = data.POST.get('assign_mentor')
    if mentor_key:
      mentor_entity = db.get(mentor_key)
      org = data.proposal.org

      if mentor_entity and data.isPossibleMentorForProposal(
          mentor_entity) or (org.list_all_mentors
          and db.Key(mentor_key) in profile_logic.queryAllMentorsKeysForOrg(
          org)):
        return mentor_entity
      else:
        raise exceptions.BadRequest("Invalid post data.")

    return None

  def post(self, data, check, mutator):
    assert isSet(data.proposal)

    mentor_entity= self.validate(data)
    if mentor_entity:
      self.assignMentor(data, mentor_entity)
    else:
      self.unassignMentor(data)

    data.proposer = data.proposal.parent()

    data.redirect.review(data.proposal.key().id(), data.proposer.link_id)
    return data.redirect.to('review_gsoc_proposal')

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class IgnoreProposal(GSoCRequestHandler):
  """View which allows org admins to ignore a proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/ignore/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_ignore'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    assert isSet(data.proposal_org)
    check.isOrgAdminForOrganization(data.proposal_org)
    if data.proposal.status == 'withdrawn':
      raise exceptions.AccessViolation(
          "You cannot ignore a withdrawn proposal")

  def toggleIgnoreProposal(self, data, value):
    """Toggles the ignore status of the proposal.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.proposal)

    if value != 'checked' and value != 'unchecked':
      raise exceptions.BadRequest("Invalid post data.")

    if value == 'checked' and data.proposal.status != 'ignored':
      raise exceptions.BadRequest("Invalid post data.")
    if value == 'unchecked' and data.proposal.status not in [
        'pending', 'withdrawn']:
      raise exceptions.BadRequest("Invalid post data.")

    proposal_key = data.proposal.key()

    def update_status_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'unchecked':
        proposal.status = 'ignored'
      elif value == 'checked':
        proposal.status = 'pending'

      db.put(proposal)

    db.run_in_transaction(update_status_txn)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.toggleIgnoreProposal(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class ProposalModificationPostDeadline(GSoCRequestHandler):
  """View allowing mentors to allow students to modify the proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/modification/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_modification'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    assert isSet(data.proposal_org)
    check.isMentorForOrganization(data.proposal_org)

  def toggleModificationPermission(self, data, value):
    """Toggles the permission to modify the proposal after proposal deadline.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.proposal)

    if value != 'checked' and value != 'unchecked':
      raise exceptions.BadRequest("Invalid post data.")

    if value == 'checked' and not data.proposal.is_editable_post_deadline:
      raise exceptions.BadRequest("Invalid post data.")
    if value == 'unchecked' and data.proposal.is_editable_post_deadline:
      raise exceptions.BadRequest("Invalid post data.")

    proposal_key = data.proposal.key()

    def update_modification_perm_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'unchecked':
        proposal.is_editable_post_deadline = True
      elif value == 'checked':
        proposal.is_editable_post_deadline = False

      db.put(proposal)

    db.run_in_transaction(update_modification_perm_txn)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.toggleModificationPermission(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class AcceptProposal(GSoCRequestHandler):
  """View allowing org admins to directly accept the proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/accept/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_accept'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    assert isSet(data.proposal_org)
    check.isOrgAdminForOrganization(data.proposal_org)

  def toggleStatus(self, data, value):
    """Toggles the the application state between accept and pending.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.proposal)

    if value != 'checked' and value != 'unchecked':
      raise exceptions.BadRequest("Invalid post data.")

    if value == 'checked' and not data.proposal.accept_as_project:
      raise exceptions.BadRequest("Invalid post data.")
    if value == 'unchecked' and data.proposal.accept_as_project:
      raise exceptions.BadRequest("Invalid post data.")

    proposal_key = data.proposal.key()

    def update_status_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'unchecked':
        proposal.accept_as_project = True
      elif value == 'checked':
        proposal.accept_as_project = False

      db.put(proposal)

    db.run_in_transaction(update_status_txn)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.toggleStatus(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class ProposalPubliclyVisible(GSoCRequestHandler):
  """View allowing the proposer to make the proposal publicly visible."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/publicly_visible/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_publicly_visible'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    check.isProposer()

  def togglePublicVisibilty(self, data, value):
    """Toggles the the public visibility of the application.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.proposal)

    if value != 'checked' and value != 'unchecked':
      raise exceptions.BadRequest("Invalid post data.")

    if value == 'checked' and not data.proposal.is_publicly_visible:
      raise exceptions.BadRequest("Invalid post data.")
    if value == 'unchecked' and data.proposal.is_publicly_visible:
      raise exceptions.BadRequest("Invalid post data.")

    proposal_key = data.proposal.key()

    def update_publicly_visibility_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'unchecked':
        proposal.is_publicly_visible = True
      elif value == 'checked':
        proposal.is_publicly_visible = False

      db.put(proposal)

    db.run_in_transaction(update_publicly_visibility_txn)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.togglePublicVisibilty(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()


class WithdrawProposal(GSoCRequestHandler):
  """View allowing the proposer to withdraw the proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/withdraw/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_withdraw'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.proposalFromKwargs()
    check.isProposer()
    check.canStudentUpdateProposal()

  def toggleWithdrawProposal(self, data, value):
    """Toggles the the application state between withdraw and pending.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.proposal)

    if value != 'checked' and value != 'unchecked':
      raise exceptions.BadRequest("Invalid post data.")

    if value == 'checked' and not data.proposal.status == 'withdrawn':
      raise exceptions.BadRequest("Invalid post data.")
    if value == 'unchecked' and data.proposal.status == 'withdrawn':
      raise exceptions.BadRequest("Invalid post data.")

    proposal_key = data.proposal.key()

    def update_withdraw_status_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'unchecked':
        proposal.status = 'withdrawn'
      elif value == 'checked':
        proposal.status = 'pending'

      db.put(proposal)

    db.run_in_transaction(update_withdraw_status_txn)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.toggleWithdrawProposal(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special handler for HTTP GET since this view only handles POST."""
    raise exceptions.MethodNotAllowed()
