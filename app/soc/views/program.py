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


class CreateProgramPage(object):
  """View to create a new program.

  It implements some functionalities of soc.views.base.RequestHandler. These
  function will be used by inheriting, module-specific classes.
  """

  def checkAccess(self, data, check, mutator):
    "See soc.views.base.RequestHandler.checkAccess for specification."
    check.isHost()

  def context(self, data, check, mutator):
    """See soc.views.base.RequestHandler.context for specification."""
    form = self._getForm(data)
    context = {
        'page_name': 'Create a new program',
        'forms': [form],
        'error': form.errors,
        }

    return context

  def post(self, data, check, mutator):
    """See soc.views.base.RequestHandler.post for specification."""
    form = self._getForm(data)
    if form.is_valid():
      timeline = self._createTimelineFromForm(data, form)
      form.cleaned_data['timeline'] = timeline
      form.cleaned_data['scope'] = data.sponsor
      form.cleaned_data['sponsor'] = data.sponsor

      key_name = '%s/%s' % (
          data.sponsor.key().name(), form.cleaned_data['link_id'])

      program = form.create(key_name=key_name, commit=False)

      db.put([timeline, program])

      # TODO(nathaniel): Make this .program() call unnecessary.
      data.redirect.program(program=program)
      return data.redirect.to(self._getUrlNameForRedirect(), validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

  def _createTimelineFromForm(self, data, form):
    """Creates a new empty Timeline entity based on the information provided
    in the form. The returned entity is not persisted in the datastore.

    Args:
      data: A RequestData describing the current request.
      form: A validated model form used to collect information on the program
          which is being created

    Returns:
      A new timeline for the program which is being created
    """
    key_name = '%s/%s' % (
        data.sponsor.key().name(), form.cleaned_data['link_id'])

    properties = {
        'link_id': form.cleaned_data['link_id'],
        'scope': data.sponsor,
        }

    timeline_model = self._getTimelineModel()
    return timeline_model(key_name=key_name, **properties)

  def _getForm(self, data):
    """Returns a form to be filled by the user with program specific settings.

    Args:
      data: A RequestData describing the current request.

    Returns:
      soc.views.forms.ModelForm to create a new program
    """
    raise NotImplementedError

  def _getTimelineModel(self):
    """Returns the timeline model which is appropriate for the program model
    used by the class. A new instance of the resulted model will be used by
    the timeline property of the created program.

    Returns:
      a timeline model class which inherits from soc.models.program.Timeline.
    """
    raise NotImplementedError

  def _getUrlNameForRedirect(self):
    """Returns the URL name of the redirect which should be used on successful
    program creation.

    Returns:
      a string representing a PROGRAM scoped URL name
    """
    raise NotImplementedError


class ProgramMessagesPage(object):
  """View for the content of program specific messages to be sent."""

  def checkAccess(self, data, check, mutator):
    check.isHost()

  def context(self, data, check, mutator):
    """See soc.views.base.RequestHandler.context for specification."""
    entity = self._getSingletonEntity(data.program)
    form = self._getForm(data, entity)

    return {
        'page_name': 'Edit program messages',
        'forms': [form],
        'error': form.errors,
        }

  def post(self, data, check, mutator):
    """See soc.views.base.RequestHandler.post for specification."""
    if self.validate(data):
      # TODO(nathaniel): Make this .program() call unnecessary.
      data.redirect.program()
      # TODO(nathaniel): Redirection to same page?
      return data.redirect.to(self._getUrlName(), validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

  def validate(self, data):
    entity = self._getSingletonEntity(data.program)
    form = self._getForm(data, entity)

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

  def _getForm(self, data, entity):
    raise NotImplementedError

  def _getModel(self):
    raise NotImplementedError

  def _getUrlName(self):
    raise NotImplementedError
