# Copyright 2012 the Melange authors.
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

"""Module for the program settings pages."""

from google.appengine.ext import db


class ProgramMessagesPage(object):
  """View for the content of program specific messages to be sent."""

  def checkAccess(self):
    self.check.isHost()

  def context(self):
    entity = self._getSingletonEntity(self.data.program)
    form = self._getForm(entity)

    return {
        'page_name': 'Edit program messages',
        'forms': [form],
        'error': form.errors,
        }

  def post(self, data, check, mutator):
    """See soc.views.base.RequestHandler.post for specification."""
    if self.validate():
      # TODO(nathaniel): Make this .program() call unnecessary.
      data.redirect.program()
      # TODO(nathaniel): Redirection to same page?
      return data.redirect.to(self._getUrlName(), validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

  def validate(self):
    entity = self._getSingletonEntity(self.data.program)
    form = self._getForm(entity)

    if form.is_valid():
      form.save()
      return True
    else:
      return False

  def _getSingletonEntity(self, program):
    model = self._getModel()
    def get_or_create_txn():
      entity = model.all().ancestor(program).get()
      if not entity:
        entity = model(parent=program)
        entity.put()
      return entity

    return db.run_in_transaction(get_or_create_txn)

  def _getForm(self, entity):
    raise NotImplementedError

  def _getModel(self):
    raise NotImplementedError

  def _getUrlName(self):
    raise NotImplementedError
