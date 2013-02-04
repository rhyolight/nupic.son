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

"""Module for the org applications."""

from django import forms as django_forms
from django.utils.translation import ugettext

from soc.logic import exceptions

from soc.views import forms
from soc.views import survey
from soc.views.helper import access_checker
from soc.views.helper import lists

from soc.logic import cleaning
from soc.models.org_app_record import OrgAppRecord
from soc.models.org_app_survey import OrgAppSurvey
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate

PROCESS_ORG_APPS_FORM_BUTTON_VALUE = \
    'Finalize decisions and send acceptance/rejection emails'


NEW_ORG_CHOICES = [('Veteran', 'Veteran'), ('New', 'New')]


class OrgAppEditForm(forms.SurveyEditForm):
  """Form to create/edit organization application survey.
  """

  class Meta:
    model = OrgAppSurvey
    css_prefix = 'org-app-edit'
    exclude = ['scope', 'author', 'program', 'created_by', 'modified_by']


class OrgAppTakeForm(forms.SurveyTakeForm):
  """Form for would-be organization admins to apply for the program.
  """

  backup_admin_id = django_forms.CharField(
      label=ugettext('Backup Admin'), required=True,
      help_text=ugettext('The username of the user who will serve as the '
                         'backup admin for this organization.'))

  # We render this field as a select field instead of a checkbox because
  # of the visibility on the form. The checkbox field because of its location
  # is not correctly visible to the person who fills the form, so we may
  # have trouble later. As a precaution, we display this field as a select
  # widget and then convert the data back to boolean value in the corresponding
  # field cleaner.
  new_org = forms.CharField(widget=django_forms.Select(choices=NEW_ORG_CHOICES))

  def __init__(self, request_data, tos_content, bound_class_field, *args,
               **kwargs):
    self.request_data = request_data
    super(OrgAppTakeForm, self).__init__(
        self.request_data.org_app, bound_class_field, *args, **kwargs)
    if self.instance:
      self.fields['backup_admin_id'].initial = \
          self.instance.backup_admin.link_id

    # not marked required by data model for backwards compatibility
    self.fields['org_id'].required = True

    self.fields['agreed_to_admin_agreement'].widget = forms.TOSWidget(
        tos_content)

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-record'
    exclude = ['main_admin', 'backup_admin', 'status', 'user', 'survey',
               'created', 'modified', 'program']
    widgets = forms.choiceWidgets(model,
        ['license'])

  def clean_org_id(self):
    org_id = cleaning.clean_link_id('org_id')(self)

    if not org_id:
      # manual required check, see Issue 1291
      raise django_forms.ValidationError('This field is required.')

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('org_id', org_id)

    org_app = q.get()

    if org_app:
      # If we are creating a new org app it is a duplicate, if we are editing
      # an org app we must check if the one we found has a different key.
      if (not self.instance) or (org_app.key() != self.instance.key()):
        raise django_forms.ValidationError('This ID has already been taken.')

    return org_id

  def clean_backup_admin_id(self):
    backup_admin = cleaning.clean_existing_user('backup_admin_id')(self)

    if not self.instance:
      cleaning.clean_users_not_same('backup_admin_id')(self)
    elif self.instance.main_admin.key() == backup_admin.key():
      raise django_forms.ValidationError(
          'You cannot enter the person who created the application here.')

    self.cleaned_data['backup_admin'] = backup_admin
    return backup_admin

  def clean_new_org(self):
    """Converts the select widget value of the new_org field from the form to
    the boolean value required by the backing data model.
    """
    return self.cleaned_data['new_org'] == 'New'

  def clean(self):
    cleaned_data = self.cleaned_data

    # pop our custom id field if exists
    if 'backup_admin_id' in cleaned_data:
      cleaned_data.pop('backup_admin_id')

    return cleaned_data


class OrgAppRecordsList(object):
  """View for listing all records of a Organization Applications.
  """

  def __init__(self, read_only_view):
    """Initializes the OrgAppRecordsList.

    Args:
      read_only_view: Name of the url pattern for the read only view of a
                      record.
    """
    self.read_only_view = read_only_view

  def checkAccess(self):
    """Defines access checks for this list, all hosts should be able to see it.
    """
    if not self.data.org_app:
      raise exceptions.NotFound(
          access_checker.DEF_NO_ORG_APP % self.data.program.name)

    self.check.isHost()

  def context(self):
    """Returns the context of the page to render.
    """
    record_list = self._createOrgAppsList()

    page_name = ugettext('Records - %s' % (self.data.org_app.title))
    context = {
        'page_name': page_name,
        'record_list': record_list,
        }
    return context

  def jsonContext(self):
    """Handler for JSON requests.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      record_list = self._createOrgAppsList()
      return record_list.listContentResponse(self.data.request).content()
    else:
      super(OrgAppRecordsList, self).jsonContext()

  def _createOrgAppsList(self):
    """Creates a SurveyRecordList for the requested survey."""
    record_list = survey.SurveyRecordList(
        self.data, self.data.org_app, OrgAppRecord, idx=0)
    record_list.list_config.addSimpleColumn('name', 'Name')
    record_list.list_config.addSimpleColumn('org_id', 'Organization ID')

    # TODO(ljvderijk): Poke Mario during all-hands to see if we can separate
    # "search options" and in-line selection options.
    options = [
        ('', 'All'),
        ('(needs review)', 'needs review'),
        ('(pre-accepted)', 'pre-accepted'),
        #('(accepted)', 'accepted'),
        ('(pre-rejected)', 'pre-rejected'),
        #('(rejected)', 'rejected'),
        ('(ignored)', 'ignored'),
    ]

    record_list.list_config.addSimpleColumn('status', 'Status', options=options)
    record_list.list_config.setColumnEditable('status', True, 'select')
    record_list.list_config.addPostEditButton('save', 'Save')

    record_list.list_config.setRowAction(
        lambda e, *args: self.data.redirect.id(e.key().id_or_name()).
            urlOf(self.read_only_view))

    return record_list

  def templatePath(self):
    return 'soc/org_app/records.html'


class OrgAppReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly organization application record.
  """

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-show'
    fields = ['org_id', 'name', 'description', 'home_page', 'license',
              'agreed_to_admin_agreement']
    survey_name = 'Organization Application'
