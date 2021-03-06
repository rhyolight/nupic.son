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

from google.appengine.ext import ndb

from django import forms as django_forms
from django.utils.translation import ugettext

from melange.request import exception
from soc.logic import validate
from soc.models import org_app_record
from soc.views import forms
from soc.views import survey
from soc.views.helper import access_checker
from soc.views.helper import lists

from soc.logic import cleaning
from soc.models.org_app_record import OrgAppRecord
from soc.models.org_app_survey import OrgAppSurvey
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate


DEF_BACKUP_ADMIN_NO_PROFILE = ugettext(
    'Backup admin does not have an org admin profile for the program. Please '
    'ask your backup admin to register a profile for %s at %s')

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
  # have trouble later. As a precaution, we display this field as a choice
  # field and then convert the data back to boolean value in the corresponding
  # field cleaner.
  new_org = forms.ChoiceField(choices=NEW_ORG_CHOICES)

  def __init__(self, bound_class_field, request_data=None, **kwargs):
    self.request_data = request_data

    # Workaround for Django's limitation of not being able to set initial value
    # for ChoiceField after calling super.
    if 'instance' in kwargs:
      kwargs['initial'] = {
          'new_org': 'New' if kwargs['instance'].new_org else 'Veteran'
          }

    super(OrgAppTakeForm, self).__init__(
        bound_class_field, survey=self.request_data.org_app, **kwargs)
    if self.instance:
      backup_admin_key = ndb.Key.from_old_key(
          org_app_record.OrgAppRecord.backup_admin
              .get_value_for_datastore(self.instance))
      self.fields['backup_admin_id'].initial = backup_admin_key.get().user_id

    # not marked required by data model for backwards compatibility
    self.fields['org_id'].required = True

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-record'
    exclude = ['main_admin', 'backup_admin', 'status', 'user', 'survey',
               'created', 'modified', 'program', 'agreed_to_admin_agreement']
    widgets = forms.choiceWidgets(model,
        ['license'])

  def validateBackupAdminProfile(self, backup_admin_user, profile_model):
    """Validates if backup admin has a profile for the current program.

    Args:
      backup_admin_user: User entity for the backup admin.
      profile_model: Model class from which the profile must be fetched.

    Raises:
      django_forms.ValidationError if the backup admin does not have a profile.
    """
    if not validate.hasNonStudentProfileForProgram(
        backup_admin_user.key, self.request_data.program.key(),
        models=self.request_data.models):
      redirector = self.request_data.redirect.createProfile('org_admin')

      raise django_forms.ValidationError(
          DEF_BACKUP_ADMIN_NO_PROFILE % (
              self.request_data.program.name,
              self._getCreateProfileURL(redirector)))

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
    else:
      main_admin_key = ndb.Key.from_old_key(
          org_app_record.OrgAppRecord.main_admin
              .get_value_for_datastore(self.instance))
      if main_admin_key == backup_admin.key:
        raise django_forms.ValidationError(
            'You cannot enter the person who created the application here.')

    self.cleaned_data['backup_admin'] = backup_admin.key.to_old_key()
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

  def _getCreateProfileURL(self, redirector):
    """Returns the full secure URL of the create profile page."""
    raise NotImplementedError


class OrgAppRecordsList(object):
  """View for listing all records of a Organization Applications."""

  def __init__(self, read_only_view):
    """Initializes the OrgAppRecordsList.

    Args:
      read_only_view: Name of the url pattern for the read only view of a
                      record.
    """
    self.read_only_view = read_only_view

  def checkAccess(self, data, check, mutator):
    """Defines access checks for this list, all hosts should be able to see it.
    """
    if not data.org_app:
      raise exception.NotFound(
          message=access_checker.DEF_NO_ORG_APP % data.program.name)

    check.isHost()

  def context(self, data, check, mutator):
    """Returns the context of the page to render."""
    record_list = self._createOrgAppsList(data)

    page_name = ugettext('Records - %s' % (data.org_app.title))
    context = {
        'page_name': page_name,
        'record_list': record_list,
        }
    return context

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    idx = lists.getListIndex(data.request)
    if idx == 0:
      record_list = self._createOrgAppsList(data)
      return record_list.listContentResponse(data.request).content()
    else:
      # TODO(nathaniel): This needs to be a return statement, right?
      super(OrgAppRecordsList, self).jsonContext(data, check, mutator)

  def _createOrgAppsList(self, data):
    """Creates a SurveyRecordList for the requested survey."""
    record_list = survey.SurveyRecordList(
        data, data.org_app, OrgAppRecord, idx=0)
    record_list.list_config.addSimpleColumn('name', 'Name')
    record_list.list_config.addSimpleColumn('org_id', 'Organization ID')
    record_list.list_config.addPlainTextColumn(
        'new_org', 'New/Veteran',
        lambda ent, *args: 'New' if ent.new_org else 'Veteran')

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
        lambda e, *args: data.redirect.id(e.key().id_or_name()).
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
              'new_org']
    renderers = {
        'new_org': lambda instance: 'New' if instance.new_org else 'Veteran'
        }
    survey_name = 'Organization Application'
