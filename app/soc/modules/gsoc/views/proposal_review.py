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

from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url

from soc.logic import cleaning
from soc.logic.exceptions import NotFound
from soc.logic.exceptions import BadRequest
from soc.models.user import User
from soc.views import forms
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.modules.gsoc.models.comment import GSoCComment
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.score import GSoCScore

from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns


def queryAllMentorsForOrg(org):
  """Returns a list of keys of all the mentors for the organization

  Args:
    org: the organization entity for which we need to get all the mentors
  """
  # get all mentors keys first
  query = GSoCProfile.all(keys_only=True)
  query.filter('mentor_for', org)
  mentors_keys = query.fetch(limit=1000)

  # get all org admins keys first
  query = GSoCProfile.all(keys_only=True)
  query.filter('org_admin_for', org)
  oa_keys = query.fetch(limit=1000)

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

  clean_content = cleaning.clean_html_content('content')


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
    self.data = data

  def context(self):
    possible_mentors, all_mentors = getMentorsChoicesToAssign(
        self.data.proposal)
    context = {
        'possible_mentors': possible_mentors,
        'all_mentors': all_mentors,
        'action': self.data.redirect.review(
            ).urlOf('gsoc_proposal_assign_mentor'),
        }
    return context

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/_assign_mentor_form.html'


class ReviewProposal(RequestHandler):
  """View for the Propsal Review page.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/proposal/review/%s$' % url_patterns.REVIEW,
         self, name='review_gsoc_proposal'),
    ]

  def checkAccess(self):
    self.data.proposer_user = User.get_by_key_name(self.data.kwargs['student'])

    fields = ['sponsor', 'program', 'student']
    key_name = '/'.join(self.data.kwargs[i] for i in fields)

    self.data.proposer_profile = GSoCProfile.get_by_key_name(
        key_name, parent=self.data.proposer_user)

    if not self.data.proposer_profile:
      raise NotFound('Requested user does not exist')

    self.data.proposal = GSoCProposal.get_by_id(
        int(self.data.kwargs['id']),
        parent=self.data.proposer_profile)

    if not self.data.proposal:
      raise NotFound('Requested proposal does not exist')

    self.data.proposal_org = self.data.proposal.org

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

  def context(self):
    assert isSet(self.data.public_comments_visible)
    assert isSet(self.data.private_comments_visible)
    assert isSet(self.data.proposer_profile)
    assert isSet(self.data.proposal)

    context = {}

    scores = self.getScores()

    # TODO: check if the scoring is not disabled
    score_action = reverse('score_gsoc_proposal', kwargs=self.data.kwargs)

    # get all the comments for the the proposal
    public_comments, private_comments = self.getComments()

    # TODO: check if it is possible to post a comment
    comment_action = reverse('comment_gsoc_proposal', kwargs=self.data.kwargs)

    if self.data.private_comments_visible:
      if self.data.isPossibleMentorForProposal():
        context['wish_to_mentor'] = 'withdraw'
      else:
        context['wish_to_mentor'] = 'request'
      context['wish_to_mentor_link'] = self.data.redirect.review(
          ).urlOf('gsoc_proposal_wish_to_mentor')

      if self.data.orgAdminFor(self.data.proposal.org):
        # only org admins can assign mentors to proposals
        context['assign_mentor'] = AssignMentorFields(self.data)

      form = PrivateCommentForm()
    else:
      form = CommentForm()

    comment_box = {
        'action': comment_action,
        'form': form,
    }

    # TODO: timeline check to see if you are allowed to edit
    user_is_proposer = self.data.user and \
        (self.data.user.key() == self.data.proposer_user.key())
    update_link = self.data.redirect.id().urlOf('update_gsoc_proposal')

    possible_mentors = db.get(self.data.proposal.possible_mentors)
    possible_mentors_names = ', '.join([m.name() for m in possible_mentors])

    scoring_visible = self.data.private_comments_visible and (
        not self.data.proposal_org.scoring_disabled)

    if self.data.orgAdminFor(self.data.proposal_org):
      scoring_visible = True

    context.update({
        'comment_box': comment_box,
        'max_score': self.data.proposal_org.max_score,
        'proposal': self.data.proposal,
        'mentor': self.data.proposal.mentor,
        'possible_mentors': possible_mentors_names,
        'public_comments': public_comments,
        'public_comments_visible': self.data.public_comments_visible,
        'private_comments': private_comments,
        'private_comments_visible': self.data.private_comments_visible,
        'scoring_visible': scoring_visible,
        'scores': scores,
        'score_action': score_action,
        'user_is_proposer': user_is_proposer,
        'update_link': update_link,
        'student_name': self.data.proposer_profile.name(),
        'student_email': self.data.proposer_profile.email,
        'title': self.data.proposal.title,
        'page_name': self.data.proposal.title,
        })

    return context

def getProposalFromKwargs(kwargs):
  fields = ['sponsor', 'program', 'student']
  key_name = '/'.join(kwargs[i] for i in fields)

  parent = db.Key.from_path('User', kwargs['student'],
                            'GSoCProfile', key_name)

  if not kwargs['id'].isdigit():
    raise BadRequest("Proposal id is not numeric")

  id = int(kwargs['id'])

  return GSoCProposal.get_by_id(id, parent=parent)


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

    self.data.proposal = getProposalFromKwargs(self.data.kwargs)

    if not self.data.proposal:
      raise NotFound('Proposal does not exist')

    self.data.proposer = self.data.proposal.parent()

    # check if the comment is given by the author of the proposal
    if self.data.proposer.key() == self.data.profile.key():
      self.data.public_only = True
      return

    self.data.public_only = False
    self.check.isMentorForOrganization(self.data.proposal.org)

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

    comment_form.cleaned_data['author'] = self.data.profile

    return comment_form.create(commit=True, parent=self.data.proposal)

  def post(self):
    assert isSet(self.data.proposer)
    assert isSet(self.data.proposal)

    comment = self.createCommentFromForm()
    if comment:
      self.redirect.review(self.data.proposal.key().id(),
                           self.data.proposer.link_id)
      self.redirect.to('review_gsoc_proposal')
    else:
      # TODO: probably we want to handle an error somehow
      pass

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
    self.data.proposal = getProposalFromKwargs(self.data.kwargs)

    if not self.data.proposal:
      raise NotFound('Requested proposal does not exist')

    org = self.data.proposal.org

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

    max_score = self.data.proposal.org.max_score

    if value < 1 or value > max_score:
      raise BadRequest("Score should be between 1 and %d" % max_score)

    query = db.Query(GSoCScore)
    query.filter('author = ', self.data.profile)
    query.ancestor(self.data.proposal)

    def update_score_trx():
      
      # update score entity
      score = query.get()
      if not score:
        old_value = 0
        score = GSoCScore(
            parent=self.data.proposal,
            author=self.data.profile,
            value=value)
        score.put()
      else:
        old_value = score.value
        if not value:
          score.delete()
        else:
          score.value = value
          score.put()

      # update total score for the proposal
      proposal = db.get(self.data.proposal.key())
      proposal.score += value - old_value
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
    self.data.proposal = getProposalFromKwargs(self.data.kwargs)

    if not self.data.proposal:
      raise NotFound('Requested proposal does not exist')

    self.check.isMentorForOrganization(self.data.proposal.org)

  def addToPotentialMentors(self, value):
    """Toggles the user from the potential mentors list.

    Args:
      value: can be either "request" or "withdraw".
    """
    assert isSet(self.data.profile)
    assert isSet(self.data.proposal)

    if value != 'request' and value != 'withdraw':
      raise BadRequest("Invalid post data.")

    if value == 'request' and self.data.isPossibleMentorForProposal():
      raise BadRequest("Invalid post data.")
    if value == 'withdraw' and not self.data.isPossibleMentorForProposal():
      raise BadRequest("Invalid post data.")

    proposal_key = self.data.proposal.key()
    profile_key = self.data.profile.key()

    def update_possible_mentors_trx():
      # transactionally get latest version of the proposal
      proposal = db.get(proposal_key)
      if value == 'request':
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
    self.data.proposal = getProposalFromKwargs(self.data.kwargs)

    if not self.data.proposal:
      raise NotFound('Requested proposal does not exist')

    self.check.isOrgAdminForOrganization(self.data.proposal.org)

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
