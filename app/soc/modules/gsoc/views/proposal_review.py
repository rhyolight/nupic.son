#!/usr/bin/env python2.5
#
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

"""Module for the GSoC proposal page.
"""

__authors__ = [
  '"Madhusudan C.S." <madhusudancs@gmail.com>',
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from google.appengine.ext import db

from django.core.urlresolvers import resolve
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url
from django import forms as django_forms
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic.exceptions import NotFound
from soc.logic.exceptions import BadRequest
from soc.logic.helper import notifications
from soc.models.user import User
from soc.views import forms
from soc.views.button import ButtonTemplate
from soc.views.helper import url as url_helper
from soc.views.helper.access_checker import isSet
from soc.views.template import Template
from soc.tasks import mailer

from soc.modules.gsoc.models.comment import GSoCComment
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.score import GSoCScore

from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns


DEF_ACCEPT_PROPOSAL_ENABLE_DISABLED_MSG = ugettext(
    'You have already accepted this proposal. To revert to the pending '
    'status, click the revert button adjacent to this button.')

DEF_ACCEPT_PROPOSAL_DISABLE_DISABLED_MSG = ugettext(
    'This proposal is already in pending status. To accept this proposal '
    'click the accept button adjacent to this button.')

DEF_IGNORE_PROPOSAL_ENABLE_DISABLED_MSG = ugettext(
    'You have already ignored this proposal. To unignore it, click the '
    'Unignore button adjacent to this button.')

DEF_IGNORE_PROPOSAL_DISABLE_DISABLED_MSG = ugettext(
    'This proposal is unignored already. To Ignore it, click the Ignore '
    'button adjacent to this button.')

DEF_PROPOSAL_MODIFICATION_ENABLE_DISABLED_MSG = ugettext(
    'Student is already allowed to edit the proposal. To disable it, '
    'click on the disable button adjacent to this button.')

DEF_PUBLICLY_VISIBLE_ENABLE_DISABLED_MSG = ugettext(
    'Your proposal is already publicly visible. In order to make your '
    'proposal visible to only your mentoring organization, click the '
    'disable button adjacent to this button.')

DEF_PUBLICLY_VISIBLE_DISABLE_DISABLED_MSG = ugettext(
    'Your proposal is not publicly visible. In order to make it public, '
    'click the enable button adjacent to this button.')

DEF_PROPOSAL_MODIFICATION_DISABLE_DISABLED_MSG = ugettext(
    'Student cannot edit the proposal already. To allow student to '
    'edit the proposal click the enable button adjacent to this button.')

DEF_WISH_TO_MENTOR_ENABLE_DISABLED_MSG = ugettext(
    'You have already wished to mentor this project. If you want to change '
    'your decision click the disable button adjacent to this button.')

DEF_WISH_TO_MENTOR_DISABLE_DISABLED_MSG = ugettext(
    'You have not chosen to mentor this project. If you wish to mentor '
    'click the enable button adjacent to this button.')


DEF_WITHDRAW_PROPOSAL_ENABLE_DISABLED_MSG = ugettext(
    'You have already withdrawn your proposal. To resubmit it, click on '
    'the resubmit button adjacent to this button.')

DEF_WITHDRAW_PROPOSAL_DISABLE_DISABLED_MSG = ugettext(
    'Your proposal is already submitted to your organization. To withdraw, '
    'click on the withdraw button adjacent to this button.')


def queryAllMentorsForOrg(org, limit=1000):
  """Returns a list of keys of all the mentors for the organization

  Args:
    org: the organization entity for which we need to get all the mentors
    limit: the maximum number of entities that must be fetched
  """
  # get all mentors keys first
  query = GSoCProfile.all(keys_only=True)
  query.filter('mentor_for', org)
  mentors_keys = query.fetch(limit=limit)

  # get all org admins keys first
  query = GSoCProfile.all(keys_only=True)
  query.filter('org_admin_for', org)
  oa_keys = query.fetch(limit=limit)

  return mentors_keys + oa_keys


def getMentorsChoicesToAssign(proposal):
  """Returns a list of tuple containing the mentor key and mentor name.

  This is the list of mentors who have shown interest in mentoring a proposal.

  Args:
    proposal: entity for which the possible mentors should be obtained.
  """
  org = proposal.org
  possible_mentors = db.get(proposal.possible_mentors)
  cur_men = proposal.mentor

  # construct a choice list for all the mentors in possible mentors list
  possible_mentors_choices = []
  possible_mentors_keys = []
  for m in possible_mentors:
    m_key = m.key()
    choice = {
        'key': m_key,
        'name': m.name(),
        }
    if cur_men and m_key == cur_men.key():
      choice['selected'] = True

    possible_mentors_choices.append(choice)
    possible_mentors_keys.append(m_key)


  # construct the choice list for all the mentors
  all_mentors_choices = []
  if org.list_all_mentors:
    all_mentors_keys = queryAllMentorsForOrg(org)

    # remove all those mentors or org admins already in possible
    # mentors list
    remaining_mentors_keys = set(all_mentors_keys) - set(possible_mentors_keys)
    remaining_mentors = db.get(remaining_mentors_keys)

    # construct the actual choice list for only these remaining mentors
    for m in remaining_mentors:
      m_key = m.key()
      choice = {
          'key': m_key,
          'name': m.name(),
          }
      if cur_men and m_key == cur_men.key():
        choice['selected'] = True

      all_mentors_choices.append(choice)

  return possible_mentors_choices, all_mentors_choices


class CommentForm(forms.ModelForm):
  """Django form for the comment.
  """

  template_path = 'v2/modules/gsoc/proposal/_comment_form.html'

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


class PrivateCommentForm(CommentForm):
  """Django form for the comment.
  """

  class Meta:
    model = GSoCComment
    fields = CommentForm.Meta.fields + ['is_private']


class AssignMentorFields(Template):
  """Template to render the fields necessary to assign a mentor to a proposal.
  """

  def __init__(self, data):
    """Instantiates the template for Assign mentor buttons for org admin.
    """
    super(AssignMentorFields, self).__init__(data)

  def context(self):
    possible_mentors, all_mentors = getMentorsChoicesToAssign(
        self.data.proposal)
    context = {
        'possible_mentors': sorted(possible_mentors),
        'all_mentors': sorted(all_mentors),
        'action': self.data.redirect.review(
            ).urlOf('gsoc_proposal_assign_mentor'),
        }
    return context

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/_assign_mentor_form.html'


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
    """The context for this template used in render().
    """
    r = self.data.redirect

    orgs = []
    for org in db.get(self.duplicate.orgs):
      q = GSoCProfile.all()
      q.filter('org_admin_for', org)
      q.filter('status', 'active')
      admins = q.fetch(1000)

      data = {'name': org.name,
              'link': r.organization(org).urlOf('gsoc_org_home'),
              'admins': admins}

      orgs.append(data)

    context = {'orgs': orgs}

    return context

  def templatePath(self):
    return 'v2/modules/gsoc/duplicates/proposal_duplicate_review.html'


class ReviewProposal(RequestHandler):
  """View for the Propsal Review page.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/review/%s$' % url_patterns.REVIEW,
         self, name='review_gsoc_proposal'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    self.check.canAccessProposalEntity()
    self.mutator.commentVisible()

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/review.html'

  def getScores(self):
    """Gets all the scores for the proposal.
    """
    assert isSet(self.data.private_comments_visible)
    assert isSet(self.data.proposal_org)
    assert isSet(self.data.proposal)

    if not self.data.private_comments_visible:
      return None

    total = 0
    number = 0
    user_score = 0

    query = db.Query(GSoCScore).ancestor(self.data.proposal)
    for score in query:
      total += score.value
      number += 1

      author_key = GSoCScore.author.get_value_for_datastore(score)
      if author_key == self.data.profile.key():
        user_score = score.value

    return {
        'average': total / number if number else 0,
        'number': number,
        'total': total,
        'user_score': user_score,
        }

  def getComments(self, limit=1000):
    """Gets all the comments for the proposal visible by the current user.
    """
    assert isSet(self.data.private_comments_visible)
    assert isSet(self.data.proposal)

    public_comments = []
    private_comments = []

    query = db.Query(GSoCComment).ancestor(self.data.proposal)
    query.order('created')
    all_comments = query.fetch(limit=limit)

    for comment in all_comments:
      if not comment.is_private:
        public_comments.append(comment)
      elif self.data.private_comments_visible:
        private_comments.append(comment)

    return public_comments, private_comments

  def sanitizePossibleMentors(self, possible_mentors):
    """Removes possible mentors that are no longer mentors
    """
    changed = False

    result = []

    for mentor in possible_mentors:
      if self.data.proposal_org.key() in mentor.mentor_for:
        result.append(mentor)
        continue

      changed = True
      self.data.proposal.possible_mentors.remove(mentor.key())

    if changed:
      self.data.proposal.put()

    return result

  def context(self):
    assert isSet(self.data.public_comments_visible)
    assert isSet(self.data.private_comments_visible)
    assert isSet(self.data.url_profile)
    assert isSet(self.data.url_user)
    assert isSet(self.data.proposal)

    context = {}

    scores = self.getScores()

    # TODO: check if the scoring is not disabled
    score_action = reverse('score_gsoc_proposal', kwargs=self.data.kwargs)

    # get all the comments for the the proposal
    public_comments, private_comments = self.getComments()

    # TODO: check if it is possible to post a comment
    comment_action = reverse('comment_gsoc_proposal', kwargs=self.data.kwargs)

    proposal_ignored = self.data.proposal.status == 'ignored'

    if self.data.private_comments_visible:
      context['user_role'] = 'mentor'
      if not proposal_ignored:
        context['wish_to_mentor_button'] = ButtonTemplate(
              self.data, 'Wish to mentor', 'wish_to_mentor',
              'gsoc_proposal_wish_to_mentor',
              not self.data.isPossibleMentorForProposal(),
              disabled_msgs = {
                  'enable': DEF_WISH_TO_MENTOR_ENABLE_DISABLED_MSG,
                  'disable': DEF_WISH_TO_MENTOR_DISABLE_DISABLED_MSG},
              labels = {
                  'enable': 'Yes',
                  'disable': 'No'})

        if self.data.timeline.afterStudentSignupEnd():
          context['proposal_modification_button'] = ButtonTemplate(
              self.data, 'Proposal modifications', 'proposal_modification',
              'gsoc_proposal_modification',
              not self.data.proposal.is_editable_post_deadline,
              disabled_msgs = {
                  'enable': DEF_PROPOSAL_MODIFICATION_ENABLE_DISABLED_MSG,
                  'disable': DEF_PROPOSAL_MODIFICATION_DISABLE_DISABLED_MSG})

      if self.data.orgAdminFor(self.data.proposal.org):
        context['user_role'] = 'org_admin'
        # only org admins can ignore the proposal, assign mentors to proposals
        if self.data.proposal.status in ['pending', 'withdrawn', 'ignored']:
          if self.data.proposal.status in ['pending', 'withdrawn']:
            enable = True
          elif self.data.proposal.status == 'ignored':
            enable = False
          context['ignore_proposal_button'] = ButtonTemplate(
              self.data, 'Ignore proposal', 'ignore_proposal',
              'gsoc_proposal_ignore', enable,
              disabled_msgs = {
                  'enable': DEF_IGNORE_PROPOSAL_ENABLE_DISABLED_MSG,
                  'disable': DEF_IGNORE_PROPOSAL_DISABLE_DISABLED_MSG,},
              labels = {
                  'enable': 'Ignore',
                  'disable': 'Unignore',})

        if not proposal_ignored:
          context['accept_proposal_button'] = ButtonTemplate(
            self.data, 'Accept proposal', 'accept_proposal',
            'gsoc_proposal_accept',
            not self.data.proposal.accept_as_project,
            disabled_msgs = {
                'enable': DEF_ACCEPT_PROPOSAL_ENABLE_DISABLED_MSG,
                'disable': DEF_ACCEPT_PROPOSAL_DISABLE_DISABLED_MSG,},
            labels = {
                'enable': 'Accept',
                'disable': 'Revert',})

          context['assign_mentor'] = AssignMentorFields(self.data)

      form = PrivateCommentForm(self.data.POST or None)
    else:
      form = CommentForm(self.data.POST or None)

    comment_box = {
        'action': comment_action,
        'form': form,
    }

    # to keep the blocks as simple as possible, the if branches have
    # been broken down into several if blocks
    user_is_proposer = self.data.user and \
        (self.data.user.key() == self.data.url_user.key())
    if user_is_proposer:
      context['user_role'] = 'proposer'

      context['publicly_visible_button'] = ButtonTemplate(
              self.data, 'Publicly visible', 'publicly_visible',
              'gsoc_proposal_publicly_visible',
              not self.data.proposal.is_publicly_visible,
              disabled_msgs = {
                  'enable': DEF_PUBLICLY_VISIBLE_ENABLE_DISABLED_MSG,
                  'disable': DEF_PUBLICLY_VISIBLE_DISABLE_DISABLED_MSG,})

      if self.data.proposal.status in ['pending', 'withdrawn']:
        if self.data.proposal.status == 'pending':
          withdraw_enable = True
        elif self.data.proposal.status == 'withdrawn':
          withdraw_enable = False
        context['withdraw_proposal_button'] = ButtonTemplate(
                self.data, 'Withdraw proposal', 'withdraw_proposal',
                'gsoc_proposal_withdraw', withdraw_enable,
                disabled_msgs = {
                    'enable': DEF_WITHDRAW_PROPOSAL_ENABLE_DISABLED_MSG,
                    'disable': DEF_WITHDRAW_PROPOSAL_DISABLE_DISABLED_MSG,},
                labels = {
                    'enable': 'Withdraw',
                    'disable': 'Resubmit',})

      # we will check if the student is allowed to modify the proposal
      # after the student proposal deadline
      is_editable = self.data.timeline.afterStudentSignupEnd() and \
          self.data.proposal.is_editable_post_deadline
      if self.data.timeline.studentSignup() or is_editable:
        context['update_link'] = self.data.redirect.id().urlOf(
            'update_gsoc_proposal')

    possible_mentors = db.get(self.data.proposal.possible_mentors)
    possible_mentors = self.sanitizePossibleMentors(possible_mentors)
    possible_mentors_names = ', '.join([m.name() for m in possible_mentors])

    scoring_visible = self.data.private_comments_visible and (
        not self.data.proposal_org.scoring_disabled)

    if self.data.orgAdminFor(self.data.proposal_org):
      scoring_visible = True

    duplicate = None
    if self.data.program.duplicates_visible and self.data.orgAdminFor(self.data.proposal_org):
      q = GSoCProposalDuplicate.all()
      q.filter('duplicates', self.data.proposal)
      q.filter('is_duplicate', True)
      dup_entity = q.get()
      duplicate = Duplicate(self.data, dup_entity) if dup_entity else None

    additional_info = self.data.proposal.additional_info

    context.update({
        'additional_info': url_helper.trim_url_to(additional_info, 50),
        'additional_info_link': additional_info,
        'comment_box': comment_box,
        'duplicate': duplicate,
        'max_score': self.data.proposal_org.max_score,
        'mentor': self.data.proposal.mentor,
        'page_name': self.data.proposal.title,
        'possible_mentors': possible_mentors_names,
        'private_comments': private_comments,
        'private_comments_visible': self.data.private_comments_visible,
        'proposal': self.data.proposal,
        'public_comments': public_comments,
        'public_comments_visible': self.data.public_comments_visible,
        'score_action': score_action,
        'scores': scores,
        'scoring_visible': scoring_visible,
        'student_email': self.data.url_profile.email,
        'student_name': self.data.url_profile.name(),
        'proposal_ignored': proposal_ignored,
        })

    return context


class PostComment(RequestHandler):
  """View which handles publishing comments.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/comment/%s$' % url_patterns.REVIEW,
         self, name='comment_gsoc_proposal'),
    ]

  def checkAccess(self):
    self.check.isProgramActive()
    self.check.isProfileActive()
    self.mutator.proposalFromKwargs()
    self.mutator.commentVisible()
    assert isSet(self.data.proposer)
    assert isSet(self.data.proposal_org)

    # check if the comment is given by the author of the proposal
    if self.data.proposer.key() == self.data.profile.key():
      self.data.public_only = True
      return

    self.data.public_only = False
    self.check.isMentorForOrganization(self.data.proposal_org)

  def createCommentFromForm(self):
    """Creates a new comment based on the data inserted in the form.

    Returns:
      a newly created comment entity or None
    """

    assert isSet(self.data.public_only)
    assert isSet(self.data.proposal)

    if self.data.public_only:
      comment_form = CommentForm(self.data.request.POST)
    else:
      # this form contains checkbox for indicating private/public comments
      comment_form = PrivateCommentForm(self.data.request.POST)

    if not comment_form.is_valid():
      return None

    if self.data.public_only:
      comment_form.cleaned_data['is_private'] = False
    comment_form.cleaned_data['author'] = self.data.profile

    q = GSoCProfile.all().filter('mentor_for', self.data.proposal.org)
    q = q.filter('status', 'active')
    if comment_form.cleaned_data.get('is_private'):
      q.filter('notify_private_comments', True)
    else:
      q.filter('notify_public_comments', True)
    mentors = q.fetch(1000)

    to_emails = [i.email for i in mentors]

    def create_comment_txn():
      comment = comment_form.create(commit=True, parent=self.data.proposal)
      context = notifications.newCommentContext(self.data, comment, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=comment)
      sub_txn()
      return comment

    return db.run_in_transaction(create_comment_txn)

  def post(self):
    assert isSet(self.data.proposer)
    assert isSet(self.data.proposal)

    comment = self.createCommentFromForm()
    if comment:
      self.redirect.program()
      self.redirect.to('gsoc_dashboard')
    else:
      # This is an insanely and absolutely hacky solution. We definitely
      # do not want any one to use this a model for writing code elsewhere
      # in Melange.
      # TODO (Madhu): Replace this in favor of PJAX for loading comments.
      r = self.redirect.review(self.data.proposal.key().id(),
                           self.data.proposer.link_id)
      redirect_url = r.urlOf('review_gsoc_proposal')
      proposal_match = resolve(redirect_url)
      proposal_view = proposal_match[0]
      self.request.method = 'GET'
      self.response = proposal_view(self.request, *self.args, **self.kwargs)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class PostScore(RequestHandler):
  """View which handles posting scores.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/score/%s$' % url_patterns.REVIEW,
         self, name='score_gsoc_proposal'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    assert isSet(self.data.proposal_org)

    org = self.data.proposal_org

    if not self.data.orgAdminFor(org) and org.scoring_disabled:
      raise BadRequest('Scoring is disabled for this organization')

    self.check.isMentorForOrganization(org)

  def createOrUpdateScore(self, value):
    """Creates a new score or updates a score if there is already one
    posted by the current user.

    If the value passed in is 0 then the Score of the user will be removed and
    None will be returned.

    Args:
      value: The value of the score the user gave as an integer.

    Returns:
      The score entity that was created/updated or None if value is 0.
    """
    assert isSet(self.data.proposal)
    assert isSet(self.data.proposal_org)

    max_score = self.data.proposal_org.max_score

    if value < 0 or value > max_score:
      raise BadRequest("Score must not be higher than %d" % max_score)

    query = db.Query(GSoCScore)
    query.filter('author = ', self.data.profile)
    query.ancestor(self.data.proposal)

    def update_score_trx():
      delta = 0

      # update score entity
      score = query.get()
      if not score:
        if not value:
          return
        old_value = 0
        score = GSoCScore(
            parent=self.data.proposal,
            author=self.data.profile,
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
      proposal = db.get(self.data.proposal.key())
      proposal.score += value - old_value
      proposal.nr_scores += delta
      proposal.put()

    db.run_in_transaction(update_score_trx)

  def post(self):
    value = int(self.data.POST['value'])
    self.createOrUpdateScore(value)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class WishToMentor(RequestHandler):
  """View handling wishing to mentor requests.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/wish_to_mentor/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_wish_to_mentor'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    assert isSet(self.data.proposal_org)

    self.check.isMentorForOrganization(self.data.proposal_org)

  def addToPotentialMentors(self, value):
    """Toggles the user from the potential mentors list.

    Args:
      value: can be either "enable" or "disable".
    """
    assert isSet(self.data.profile)
    assert isSet(self.data.proposal)

    if value != 'enable' and value != 'disable':
      raise BadRequest("Invalid post data.")

    if value == 'enable' and self.data.isPossibleMentorForProposal():
      raise BadRequest("Invalid post data.")
    if value == 'disable' and not self.data.isPossibleMentorForProposal():
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()
    profile_key = self.data.profile.key()

    def update_possible_mentors_trx():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'enable':
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

  def post(self):
    value = self.data.POST.get('value')
    self.addToPotentialMentors(value)


  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class AssignMentor(RequestHandler):
  """View which handles assigning mentor to a proposal.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/assign_mentor/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_assign_mentor'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    assert isSet(self.data.proposal_org)
    self.check.isOrgAdminForOrganization(self.data.proposal_org)

  def assignMentor(self, mentor_entity):
    """Assigns the mentor to the proposal.

    Args:
      mentor_entity: The entity of the mentor profile which needs to assigned
          to the proposal.
    """
    assert isSet(self.data.proposal)

    proposal = self.data.proposal

    # do not do an update on the entity if the request is for same mentor
    if proposal.mentor and proposal.mentor.key() == mentor_entity.key():
      return

    proposal.mentor = mentor_entity

    db.put(proposal)

  def unassignMentor(self):
    """Removes the mentor assigned to the proposal.
    """
    assert isSet(self.data.proposal)

    proposal = self.data.proposal
    proposal.mentor = None
    db.put(proposal)

  def validate(self):
    mentor_key = self.data.POST.get('assign_mentor')
    if mentor_key:
      mentor_entity = db.get(mentor_key)
      org = self.data.proposal.org

      if mentor_entity and self.data.isPossibleMentorForProposal(
          mentor_entity) or (org.list_all_mentors
          and db.Key(mentor_key) in queryAllMentorsForOrg(org)):
        return mentor_entity
      else:
        raise BadRequest("Invalid post data.")

    return None

  def post(self):
    assert isSet(self.data.proposal)

    mentor_entity= self.validate()
    if mentor_entity:
      self.assignMentor(mentor_entity)
    else:
      self.unassignMentor()

    self.data.proposer = self.data.proposal.parent()

    self.redirect.review(self.data.proposal.key().id(),
                         self.data.proposer.link_id)
    self.redirect.to('review_gsoc_proposal')

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class IgnoreProposal(RequestHandler):
  """View which allows org admins to ignore a proposal.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/ignore/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_ignore'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    assert isSet(self.data.proposal_org)
    self.check.isOrgAdminForOrganization(self.data.proposal_org)

  def toggleIgnoreProposal(self, value):
    """Toggles the ignore status of the proposal.

    Args:
      value: can be either "enable" or "disable".
    """
    assert isSet(self.data.proposal)

    if value != 'enable' and value != 'disable':
      raise BadRequest("Invalid post data.")

    if value == 'enable' and self.data.proposal.status not in [
        'pending', 'withdrawn']:
      raise BadRequest("Invalid post data.")
    if value == 'disable' and self.data.proposal.status != 'ignored':
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()

    def update_status_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'enable':
        proposal.status = 'ignored'
      elif value == 'disable':
        proposal.status = 'pending'

      db.put(proposal)

    db.run_in_transaction(update_status_txn)

  def post(self):
    value = self.data.POST.get('value')
    self.toggleIgnoreProposal(value)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class ProposalModificationPostDeadline(RequestHandler):
  """View allowing mentors to allow students to modify the proposal.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/modification/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_modification'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    assert isSet(self.data.proposal_org)
    self.check.isMentorForOrganization(self.data.proposal_org)

  def toggleModificationPermission(self, value):
    """Toggles the permission to modify the proposal after proposal deadline.

    Args:
      value: can be either "enable" or "disable".
    """
    assert isSet(self.data.proposal)

    if value != 'enable' and value != 'disable':
      raise BadRequest("Invalid post data.")

    if value == 'enable' and self.data.proposal.is_editable_post_deadline:
      raise BadRequest("Invalid post data.")
    if (value == 'disable' and not
        self.data.proposal.is_editable_post_deadline):
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()

    def update_modification_perm_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'enable':
        proposal.is_editable_post_deadline = True
      elif value == 'disable':
        proposal.is_editable_post_deadline = False

      db.put(proposal)

    db.run_in_transaction(update_modification_perm_txn)

  def post(self):
    value = self.data.POST.get('value')
    self.toggleModificationPermission(value)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class AcceptProposal(RequestHandler):
  """View allowing org admins to directly accept the proposal.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/accept/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_accept'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    assert isSet(self.data.proposal_org)
    self.check.isOrgAdminForOrganization(self.data.proposal_org)

  def toggleStatus(self, value):
    """Toggles the the application state between accept and pending.

    Args:
      value: can be either "enable" or "disable".
    """
    assert isSet(self.data.proposal)

    if value != 'enable' and value != 'disable':
      raise BadRequest("Invalid post data.")

    if value == 'enable' and self.data.proposal.accept_as_project:
      raise BadRequest("Invalid post data.")
    if value == 'disable' and not self.data.proposal.accept_as_project:
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()

    def update_status_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'enable':
        proposal.accept_as_project = True
      elif value == 'disable':
        proposal.accept_as_project = False

      db.put(proposal)

    db.run_in_transaction(update_status_txn)

  def post(self):
    value = self.data.POST.get('value')
    self.toggleStatus(value)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class ProposalPubliclyVisible(RequestHandler):
  """View allowing the proposer to make the proposal publicly visible.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/publicly_visible/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_publicly_visible'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    self.check.isProposer()

  def togglePublicVisibilty(self, value):
    """Toggles the the public visibility of the application.

    Args:
      value: can be either "enable" or "disable".
    """
    assert isSet(self.data.proposal)

    if value != 'enable' and value != 'disable':
      raise BadRequest("Invalid post data.")

    if value == 'enable' and self.data.proposal.is_publicly_visible:
      raise BadRequest("Invalid post data.")
    if value == 'disable' and not self.data.proposal.is_publicly_visible:
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()

    def update_publicly_visibility_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'enable':
        proposal.is_publicly_visible = True
      elif value == 'disable':
        proposal.is_publicly_visible = False

      db.put(proposal)

    db.run_in_transaction(update_publicly_visibility_txn)

  def post(self):
    value = self.data.POST.get('value')
    self.togglePublicVisibilty(value)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)


class WithdrawProposal(RequestHandler):
  """View allowing the proposer to withdraw the proposal.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/withdraw/%s$' % url_patterns.REVIEW,
         self, name='gsoc_proposal_withdraw'),
    ]

  def checkAccess(self):
    self.mutator.proposalFromKwargs()
    self.check.isProposer()

  def toggleWithdrawProposal(self, value):
    """Toggles the the application state between withdraw and pending.

    Args:
      value: can be either "enable" or "disable".
    """
    assert isSet(self.data.proposal)

    if value != 'enable' and value != 'disable':
      raise BadRequest("Invalid post data.")

    if value == 'enable' and self.data.proposal.status == 'withdrawn':
      raise BadRequest("Invalid post data.")
    if value == 'disable' and not self.data.proposal.status == 'withdrawn':
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()

    def update_withdraw_status_txn():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'enable':
        proposal.status = 'withdrawn'
      elif value == 'disable':
        proposal.status = 'pending'

      db.put(proposal)

    db.run_in_transaction(update_withdraw_status_txn)

  def post(self):
    value = self.data.POST.get('value')
    self.toggleWithdrawProposal(value)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)
