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

"""This module contains the view for the site menus."""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
]


from soc.views.template import Template


class LoggedInMsg(Template):
  """Template to render user login message at the top of the profile form.
  """
  def __init__(self, data, apply_role=False, apply_link=True, div_name=None):
    if not div_name:
      div_name = 'loggedin-message'
    self.data = data
    self.apply_link = apply_link
    self.apply_role = apply_role
    self.div_name = div_name

  def context(self):
    context = {
        'logout_link': self.data.redirect.logout().url(),
        'has_profile': bool(self.data.profile),
        'div_name': self.div_name,
    }

    if self.apply_role and self.data.kwargs.get('role'):
      context['role'] = self.data.kwargs['role']

    if self.data.gae_user:
      context['user_email'] = self.data.gae_user.email()

    if self.data.user:
      context['link_id'] = " [link_id: %s]" % self.data.user.link_id

    if self.apply_link and self.data.timeline.orgsAnnounced() and (
      (self.data.profile and not self.data.student_info) or
      (self.data.timeline.studentSignup() and self.data.student_info)):
      context['apply_link'] = self.data.redirect.acceptedOrgs().url()

    return context

