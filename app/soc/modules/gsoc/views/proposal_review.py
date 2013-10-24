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

from google.appengine.ext import db

from django import http
from django.core.urlresolvers import resolve
from django.core.urlresolvers import reverse
from django import forms as django_forms
from django.utils.translation import ugettext

from melange.request import access
from melange.request import exception
from melange.request import links
from melange.views.helper import form_handler

from soc.logic import cleaning
from soc.views.helper import url as url_helper
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template
from soc.views.toggle_button import ToggleButtonTemplate
from soc.tasks import mailer

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.logic.helper import notifications
from soc.modules.gsoc.models.comment import GSoCComment
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.score import GSoCScore
from soc.modules.gsoc.views import assign_mentor
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names

from soc.modules.gsoc.views.helper.url_patterns import url


TOGGLE_BUTTON_IS_WITHDRAWN = 'checked'
TOGGLE_BUTTON_NOT_WITHDRAWN = 'unchecked'

PROPOSAL_CANNOT_BE_RESUBMITTED = ugettext(
    'This proposal cannot be resubmitted at this time.')

PROPOSAL_CANNOT_BE_WITHDRAWN = ugettext(
    'This proposal cannot be withdrawn at this time.')

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
    return 'modules/gsoc/proposal/_comment_form.html'


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
      admins = profile_logic.getOrgAdmins(org.key())

      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=org)

      data = {'name': org.name,
              'link': self.data.redirect.urlOf(url_names.GSOC_ORG_HOME),
              'admins': admins}

      orgs.append(data)

    context = {'orgs': orgs}

    return context

  def templatePath(self):
    return 'modules/gsoc/duplicates/proposal_duplicate_review.html'


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

    wish_to_mentor_url = links.LINKER.userId(
        self.data.url_profile, self.data.kwargs['id'],
        'gsoc_proposal_wish_to_mentor')

    wish_to_mentor = ToggleButtonTemplate(
        self.data, 'on_off', 'Wish to Mentor', 'wish-to-mentor',
        wish_to_mentor_url, checked=self.data.isPossibleMentorForProposal(),
        help_text=self.DEF_WISH_TO_MENTOR_HELP,
        labels = {
            'checked': 'Yes',
            'unchecked': 'No'})
    self.toggle_buttons.append(wish_to_mentor)

    if self.data.timeline.afterStudentSignupEnd():
      proposal_modification_button = ToggleButtonTemplate(
          self.data, 'long', 'Proposal Modifications', 'proposal-modification',
          self.data.redirect.urlOf('gsoc_proposal_modification'),
          checked=self.data.url_proposal.is_editable_post_deadline,
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

    ignore_proposal_url = links.LINKER.userId(
        self.data.url_profile, self.data.kwargs['id'],
        url_names.PROPOSAL_IGNORE)

    ignore_button_checked = False
    if self.data.url_proposal.status == 'ignored':
      ignore_button_checked = True
    if self.data.url_proposal.status in ['pending', 'ignored']:
      ignore_proposal = ToggleButtonTemplate(
          self.data, 'on_off', 'Ignore Proposal', 'proposal-ignore',
          ignore_proposal_url, checked=ignore_button_checked,
          help_text=self.DEF_IGNORE_PROPOSAL_HELP,
          note=self.DEF_IGNORE_PROPOSAL_NOTE,
          labels={
              'checked': 'Yes',
              'unchecked': 'No'})
      self.toggle_buttons.append(ignore_proposal)

    if not self.proposal_ignored:
      accept_proposal = ToggleButtonTemplate(
          self.data, 'on_off', 'Accept proposal', 'accept-proposal',
          self.data.redirect.urlOf('gsoc_proposal_accept'),
          checked=self.data.url_proposal.accept_as_project,
          help_text=self.DEF_ACCEPT_PROPOSAL_HELP,
          labels = {
              'checked': 'Yes',
              'unchecked': 'No',})
      self.toggle_buttons.append(accept_proposal)

      possible_mentors_keys = self.data.url_proposal.possible_mentors
      if self.data.url_proposal.org.list_all_mentors:
        all_mentors_keys = profile_logic.queryAllMentorsKeysForOrg(
            self.data.url_proposal.org)
      else:
        all_mentors_keys = []

      current_mentors = []
      if self.data.url_proposal.mentor:
        current_mentors.append(self.data.url_proposal.mentor.key())

      assign_mentor_url = links.LINKER.userId(
          self.data.url_profile, self.data.kwargs['id'],
          'gsoc_proposal_assign_mentor')

      context['assign_mentor'] = assign_mentor.AssignMentorFields(
          self.data, current_mentors, assign_mentor_url,
          all_mentors_keys, possible_mentors_keys)

    return context

  def _proposerContext(self):
    """Construct the context needed for proposer actions.
    """
    publicly_visible_url = links.LINKER.userId(
        self.data.url_profile, self.data.kwargs['id'],
        'gsoc_proposal_publicly_visible')

    publicly_visible = ToggleButtonTemplate(
        self.data, 'on_off', 'Publicly Visible', 'publicly-visible',
        publicly_visible_url,
        checked=self.data.url_proposal.is_publicly_visible,
        help_text=self.DEF_PUBLICLY_VISIBLE_HELP,
        labels = {
            'checked': 'Yes',
            'unchecked': 'No',})
    self.toggle_buttons.append(publicly_visible)

    if self.data.url_proposal.status in ['pending', 'withdrawn']:
      if self.data.url_proposal.status == 'withdrawn':
        checked = True
      elif self.data.url_proposal.status == 'pending':
        checked = False

      withdraw_proposal_url = links.LINKER.userId(
          self.data.url_profile, self.data.kwargs['id'],
          url_names.PROPOSAL_STATUS)
      withdraw_proposal = ToggleButtonTemplate(
          self.data, 'on_off', 'Withdraw Proposal', 'withdraw-proposal',
          withdraw_proposal_url, checked=checked,
          help_text=self.DEF_WITHDRAW_PROPOSAL_HELP,
          labels = {
              TOGGLE_BUTTON_IS_WITHDRAWN: 'Yes',
              TOGGLE_BUTTON_NOT_WITHDRAWN: 'No'
          })
      self.toggle_buttons.append(withdraw_proposal)

    return {}

  def context(self):
    context = {
        'title': 'Proposal Actions',
        }

    self.proposal_ignored = self.data.url_proposal.status == 'ignored'

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
    return "modules/gsoc/proposal/_user_action.html"


class ReviewProposal(base.GSoCRequestHandler):
  """View for the Propsal Review page."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/review/%s$' % url_patterns.USER_ID,
         self, name=url_names.PROPOSAL_REVIEW),
    ]

  def checkAccess(self, data, check, mutator):
    check.canAccessProposalEntity()
    mutator.commentVisible(data.url_proposal.org)

  def templatePath(self):
    return 'modules/gsoc/proposal/review.html'

  def getScores(self, data):
    """Gets all the scores for the proposal."""
    assert isSet(data.private_comments_visible)

    if not data.private_comments_visible:
      return None

    total = 0
    number = 0
    user_score = 0

    query = db.Query(GSoCScore).ancestor(data.url_proposal)
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
    assert isSet(data.url_proposal)

    public_comments = []
    private_comments = []

    query = db.Query(GSoCComment).ancestor(data.url_proposal)
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
      if data.url_proposal.org.key() in mentor.mentor_for:
        result.append(mentor)
        continue

      changed = True
      data.url_proposal.possible_mentors.remove(mentor.key())

    if changed:
      data.url_proposal.put()

    return result

  def context(self, data, check, mutator):
    assert isSet(data.public_comments_visible)
    assert isSet(data.private_comments_visible)
    assert isSet(data.url_profile)
    assert isSet(data.url_user)

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
      context['proposal_ignored'] = data.url_proposal.status == 'ignored'

      form = PrivateCommentForm(data=data.POST or None)
      if data.orgAdminFor(data.url_proposal.org):
        user_role = 'org_admin'
      else:
        user_role = 'mentor'

    else:
      form = CommentForm(data=data.POST or None)

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
          data.url_proposal.is_editable_post_deadline
      if data.timeline.studentSignup() or is_editable:
        context['update_link'] = links.LINKER.userId(
            data.url_profile, data.url_proposal.key().id(),
            'update_gsoc_proposal')

    possible_mentors = db.get(data.url_proposal.possible_mentors)
    possible_mentors = self.sanitizePossibleMentors(data, possible_mentors)
    possible_mentors_names = ', '.join([m.name() for m in possible_mentors])

    scoring_visible = data.private_comments_visible and (
        not data.url_proposal.org.scoring_disabled)

    if data.orgAdminFor(data.url_proposal.org):
      scoring_visible = True

    duplicate = None
    if (data.program.duplicates_visible and 
        data.orgAdminFor(data.url_proposal.org)):
      q = GSoCProposalDuplicate.all()
      q.filter('duplicates', data.url_proposal)
      q.filter('is_duplicate', True)
      dup_entity = q.get()
      duplicate = Duplicate(data, dup_entity) if dup_entity else None

    additional_info = data.url_proposal.additional_info

    if user_role:
      context['user_actions'] = UserActions(data, user_role)

    context.update({
        'additional_info': url_helper.trim_url_to(additional_info, 50),
        'additional_info_link': additional_info,
        'comment_box': comment_box,
        'duplicate': duplicate,
        'max_score': data.url_proposal.org.max_score,
        'mentor': data.url_proposal.mentor,
        'page_name': data.url_proposal.title,
        'possible_mentors': possible_mentors_names,
        'private_comments': private_comments,
        'private_comments_visible': data.private_comments_visible,
        'proposal': data.url_proposal,
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


class PostComment(base.GSoCRequestHandler):
  """View which handles publishing comments."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/comment/%s$' % url_patterns.USER_ID,
         self, name='comment_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.isProfileActive()
    mutator.commentVisible(data.organization)

    # private comments may be posted only by organization members
    if not self._isProposer(data):
      check.isMentorForOrganization(data.url_proposal.org)

  def createCommentFromForm(self, data):
    """Creates a new comment based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created comment entity or None
    """
    assert isSet(data.url_proposal)

    if self._isProposer(data):
      comment_form = CommentForm(data=data.request.POST)
    else:
      # this form contains checkbox for indicating private/public comments
      comment_form = PrivateCommentForm(data=data.request.POST)

    if not comment_form.is_valid():
      return None

    if self._isProposer(data):
      comment_form.cleaned_data['is_private'] = False
    comment_form.cleaned_data['author'] = data.profile

    q = GSoCProfile.all().filter('mentor_for', data.url_proposal.org)
    q = q.filter('status', 'active')
    if comment_form.cleaned_data.get('is_private'):
      q.filter('notify_private_comments', True)
    else:
      q.filter('notify_public_comments', True)
    mentors = q.fetch(1000)

    to_emails = [i.email for i in mentors if i.key() != data.profile.key()]

    def create_comment_txn():
      comment = comment_form.create(commit=True, parent=data.url_proposal)
      context = notifications.newReviewContext(data, comment, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=comment)
      sub_txn()
      return comment

    return db.run_in_transaction(create_comment_txn)

  def post(self, data, check, mutator):
    assert isSet(data.url_proposal)

    comment = self.createCommentFromForm(data)
    if comment:
      data.redirect.program()
      return data.redirect.to('gsoc_dashboard', anchor='proposals_submitted')
    else:
      # This is an insanely and absolutely hacky solution. We definitely
      # do not want any one to use this a model for writing code elsewhere
      # in Melange.
      # TODO (Madhu): Replace this in favor of PJAX for loading comments.
      redirect_url = links.LINKER.userId(
          data.url_profile, data.url_proposal.key().id(),
          url_names.PROPOSAL_REVIEW)
      proposal_match = resolve(redirect_url)
      proposal_view = proposal_match[0]
      data.request.method = 'GET'
      return proposal_view(data.request, *data.args, **data.kwargs)

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exception.MethodNotAllowed()

  def _isProposer(self, data):
    """Determines whether the currently logged in user is a student to whom
    the proposal belongs.

    If so, he or she is eligible to post only public comments.

    Args:
      data: request_data.RequestData for the current request.
    """
    return data.url_profile.key() == data.profile.key()


class PostScore(base.GSoCRequestHandler):
  """View which handles posting scores."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/score/%s$' % url_patterns.USER_ID,
         self, name='score_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    if (not data.orgAdminFor(data.url_proposal.org)
        and data.url_proposal.org.scoring_disabled):
      raise exception.BadRequest(
          message='Scoring is disabled for this organization')

    check.isMentorForOrganization(data.url_proposal.org)

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
    max_score = data.url_proposal.org.max_score

    if value < 0 or value > max_score:
      raise exception.BadRequest(
          message="Score must not be higher than %d" % max_score)

    query = db.Query(GSoCScore)
    query.filter('author = ', data.profile)
    query.ancestor(data.url_proposal)

    def update_score_trx():
      delta = 0

      # update score entity
      score = query.get()
      if not score:
        if not value:
          return
        old_value = 0
        score = GSoCScore(
            parent=data.url_proposal,
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
      proposal = db.get(data.url_proposal.key())
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
    raise exception.MethodNotAllowed()


class WishToMentor(base.GSoCRequestHandler):
  """View handling wishing to mentor requests."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/wish_to_mentor/%s$' % url_patterns.USER_ID,
         self, name='gsoc_proposal_wish_to_mentor'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isMentorForOrganization(data.url_proposal.org)

  def addToPotentialMentors(self, data, value):
    """Toggles the user from the potential mentors list.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.profile)
    assert isSet(data.url_proposal)

    if value != 'checked' and value != 'unchecked':
      raise exception.BadRequest(message="Invalid post data.")

    if value == 'checked' and not data.isPossibleMentorForProposal():
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'unchecked' and data.isPossibleMentorForProposal():
      raise exception.BadRequest(message="Invalid post data.")

    proposal_key = data.url_proposal.key()
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
    raise exception.MethodNotAllowed()


class AssignMentor(base.GSoCRequestHandler):
  """View which handles assigning mentor to a proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/assign_mentor/%s$' % url_patterns.USER_ID,
         self, name='gsoc_proposal_assign_mentor'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isOrgAdminForOrganization(data.url_proposal.org)

  def assignMentor(self, data, mentor_entity):
    """Assigns the mentor to the proposal.

    Args:
      data: A RequestData describing the current request.
      mentor_entity: The entity of the mentor profile which needs to assigned
          to the proposal.
    """
    proposal_key = data.url_proposal.key()

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
    proposal_key = data.url_proposal.key()

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
      org = data.url_proposal.org

      if mentor_entity and data.isPossibleMentorForProposal(
          mentor_entity) or (org.list_all_mentors
          and db.Key(mentor_key) in profile_logic.queryAllMentorsKeysForOrg(
          org)):
        return mentor_entity
      else:
        raise exception.BadRequest(message="Invalid post data.")

    return None

  def post(self, data, check, mutator):
    mentor_entity = self.validate(data)
    if mentor_entity:
      self.assignMentor(data, mentor_entity)
    else:
      self.unassignMentor(data)

    url = links.LINKER.userId(
        data.url_profile, data.url_proposal.key().id(),
        url_names.PROPOSAL_REVIEW)
    return http.HttpResponseRedirect(url)

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exception.MethodNotAllowed()


class IgnoreProposal(base.GSoCRequestHandler):
  """View which allows org admins to ignore a proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/ignore/%s$' % url_patterns.USER_ID,
         self, name=url_names.PROPOSAL_IGNORE),
    ]

  def checkAccess(self, data, check, mutator):
    check.isOrgAdminForOrganization(data.url_proposal.org)
    if data.url_proposal.status == 'withdrawn':
      raise exception.Forbidden(
          message="You cannot ignore a withdrawn proposal")

  def toggleIgnoreProposal(self, data, value):
    """Toggles the ignore status of the proposal.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    if value != 'checked' and value != 'unchecked':
      raise exception.BadRequest(message="Invalid post data.")

    if value == 'checked' and data.url_proposal.status != 'ignored':
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'unchecked' and data.url_proposal.status not in [
        'pending', 'withdrawn']:
      raise exception.BadRequest(message="Invalid post data.")

    proposal_key = data.url_proposal.key()

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
    raise exception.MethodNotAllowed()


class ProposalModificationPostDeadline(base.GSoCRequestHandler):
  """View allowing mentors to allow students to modify the proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/modification/%s$' % url_patterns.USER_ID,
         self, name='gsoc_proposal_modification'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isMentorForOrganization(data.url_proposal.org)

  def toggleModificationPermission(self, data, value):
    """Toggles the permission to modify the proposal after proposal deadline.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    if value != 'checked' and value != 'unchecked':
      raise exception.BadRequest(message="Invalid post data.")

    if value == 'checked' and not data.url_proposal.is_editable_post_deadline:
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'unchecked' and data.url_proposal.is_editable_post_deadline:
      raise exception.BadRequest(message="Invalid post data.")

    proposal_key = data.url_proposal.key()

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
    raise exception.MethodNotAllowed()


class AcceptProposal(base.GSoCRequestHandler):
  """View allowing org admins to directly accept the proposal."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/accept/%s$' % url_patterns.USER_ID,
         self, name='gsoc_proposal_accept'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isOrgAdminForOrganization(data.url_proposal.org)

  def toggleStatus(self, data, value):
    """Toggles the the application state between accept and pending.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    if value != 'checked' and value != 'unchecked':
      raise exception.BadRequest(message="Invalid post data.")

    if value == 'checked' and not data.url_proposal.accept_as_project:
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'unchecked' and data.url_proposal.accept_as_project:
      raise exception.BadRequest(message="Invalid post data.")

    proposal_key = data.url_proposal.key()

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
    raise exception.MethodNotAllowed()


class ProposalPubliclyVisible(base.GSoCRequestHandler):
  """View allowing the proposer to make the proposal publicly visible."""

  def djangoURLPatterns(self):
    return [
         url(r'proposal/publicly_visible/%s$' % url_patterns.USER_ID,
         self, name='gsoc_proposal_publicly_visible'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProposer()

  def togglePublicVisibilty(self, data, value):
    """Toggles the the public visibility of the application.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    if value != 'checked' and value != 'unchecked':
      raise exception.BadRequest(message="Invalid post data.")

    if value == 'checked' and not data.url_proposal.is_publicly_visible:
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'unchecked' and data.url_proposal.is_publicly_visible:
      raise exception.BadRequest(message="Invalid post data.")

    def update_publicly_visibility_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(data.url_proposal.key())
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
    raise exception.MethodNotAllowed()


class ProposalStatusSetter(base.GSoCRequestHandler):
  """POST handler to allow a proposer to change status of their proposals.

  In other words, they may want to withdraw a submitted proposal or
  resubmit a withdrawn one.
  """

  access_checker = access.IS_URL_USER_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url(r'proposal/status/%s$' % url_patterns.USER_ID,
         self, name=url_names.PROPOSAL_STATUS),
    ]

  def get(self, data, check, mutator):
    """Special handler for HTTP GET since this view only handles POST."""
    raise exception.MethodNotAllowed()

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    value = data.POST.get('value')
    if value == TOGGLE_BUTTON_NOT_WITHDRAWN:
      handler = ResubmitProposalHandler(None)
    elif value == TOGGLE_BUTTON_IS_WITHDRAWN:
      handler = WithdrawProposalHandler(None)

    return handler.handle(data, check, mutator)


class WithdrawProposalHandler(form_handler.FormHandler):
  """FormHandler implementation to withdraw proposals."""

  def handle(self, data, check, mutator):
    """See form_handler.FormHandler.handle for specification."""
    is_withdrawn = withdrawProposalTxn(
        data.url_proposal.key(), data.profile.student_info.key())
    if is_withdrawn:
      if self._url is not None:
        return http.HttpResponseRedirect(self._url)
      else:
        return http.HttpResponse()
    else:
      raise exception.Forbidden(PROPOSAL_CANNOT_BE_WITHDRAWN)


class ResubmitProposalHandler(form_handler.FormHandler):
  """FormHandler implementation to resubmit withdrawn proposals"""

  def handle(self, data, check, mutator):
    """See form_handler.FormHandler.handle for specification."""
    is_resubmitted = resubmitProposalTxn(
        data.url_proposal.key(), data.profile.student_info.key(),
        data.program, data.program.timeline)
    if is_resubmitted:
      return http.HttpResponse()
    else:
      raise exception.Forbidden(PROPOSAL_CANNOT_BE_RESUBMITTED)


@db.transactional
def withdrawProposalTxn(proposal_key, student_info_key):
  """Withdraws the specified proposal in a transaction.

  Args:
    proposal_key: Proposal key.
    student_info_key: Student info key of the student who owns the proposal.
  """
  proposal, student_info = db.get([proposal_key, student_info_key])
  return proposal_logic.withdrawProposal(proposal, student_info)


@db.transactional
def resubmitProposalTxn(proposal_key, student_info_key, program, timeline):
  """Resubmits the specified proposal in a transaction.

  Args:
    proposal_key: Proposal key.
    student_info_key: Student info key of the student who owns the proposal.
    program: Program entity.
    timeline: Timeline enity.
  """
  proposal, student_info = db.get([proposal_key, student_info_key])
  return proposal_logic.resubmitProposal(
      proposal, student_info, program, timeline)
