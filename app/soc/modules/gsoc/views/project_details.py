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

"""Module containing the view for GSoC project details page."""

from google.appengine.ext import blobstore
from google.appengine.ext import db

from django import forms as django_forms
from django import http
from django.forms.util import ErrorDict
from django.utils.translation import ugettext

from melange.request import exception
from melange.request import links

from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template
from soc.views.toggle_button import ToggleButtonTemplate

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.code_sample import GSoCCodeSample
from soc.modules.gsoc.views import assign_mentor
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.views.helper import urls


class ProjectDetailsForm(gsoc_forms.GSoCModelForm):
  """Constructs the form to edit the project details
  """

  class Meta:
    model = GSoCProject
    css_prefix = 'gsoc_project'
    fields = ['title', 'abstract', 'public_info',
              'additional_info', 'feed_url']


class CodeSampleUploadFileForm(gsoc_forms.GSoCModelForm):
  """Django form for submitting code samples for a project.
  """

  DEF_NO_UPLOAD = ugettext(
      'An error occurred, please upload a file.')

  class Meta:
    model = GSoCCodeSample
    css_prefix = 'gsoc_code_sample'
    fields = ['upload_of_work']

  upload_of_work = django_forms.FileField(
      label='Upload code sample', required=False)

  def addFileRequiredError(self):
    """Appends a form error message indicating that this field is required.
    """
    if not self._errors:
      self._errors = ErrorDict()

    self._errors["upload_of_work"] = self.error_class([self.DEF_NO_UPLOAD])

  def clean_upload_of_work(self):
    """Ensure that file field has data.
    """
    cleaned_data = self.cleaned_data

    upload = cleaned_data.get('upload_of_work')

    # Although we need the ValidationError exception the message there
    # is dummy because it won't pass through the Appengine's Blobstore
    # API. We use the same error message when adding the form error.
    # See self.addFileRequiredError method.
    if not upload:
      raise gsoc_forms.ValidationError(self.DEF_NO_UPLOAD)

    return upload


class ListCodeSamples(Template):
  """Template to render all the GSoCCodeSample entities for the project.
  """

  def __init__(self, data, deleteable):
    super(ListCodeSamples, self).__init__(data)
    self.deleteable = deleteable

  def _buildContextForExistingCodeSamples(self):
    """Builds a list containing the info related to each code sample.
    """
    assert isSet(self.data.project)
    code_samples = []
    sources = self.data.project.codeSamples()
    for source in sorted(sources, key=lambda e: e.submitted_on):
      code_sample = {
          'entity': source
          }
      uploaded_blob = source.upload_of_work
      code_sample['uploaded_blob'] = uploaded_blob
      if uploaded_blob and blobstore.BlobInfo.get(uploaded_blob.key()):
        code_sample['is_blob_valid'] = True
      else:
        code_sample['is_blob_valid'] = False

      code_samples.append(code_sample)

    return code_samples

  def context(self):
    """See template.Template.context for specification."""
    code_sample_download_url = links.LINKER.userId(
        self.data.url_profile.key(), self.data.project.key().id(),
        url_names.GSOC_PROJECT_CODE_SAMPLE_DOWNLOAD)
    code_sample_delete_file_action = links.LINKER.userId(
        self.data.url_profile.key(), self.data.project.key().id(),
        url_names.GSOC_PROJECT_CODE_SAMPLE_DELETE)
    return {
        'code_samples': self._buildContextForExistingCodeSamples(),
        'code_sample_download_url': code_sample_download_url,
        'code_sample_delete_file_action': code_sample_delete_file_action,
        'deleteable': self.deleteable
        }

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'modules/gsoc/project_details/_list_code_samples.html'


class UploadCodeSamples(Template):
  """Template that contains a form to upload code samples.
  """

  def context(self):
    """See template.Template.context for specification."""
    code_sample_upload_file_action = links.LINKER.userId(
        self.data.url_profile.key(), self.data.project.key().id(),
        url_names.GSOC_PROJECT_CODE_SAMPLE_UPLOAD)

    context = {
        'code_sample_upload_file_form': CodeSampleUploadFileForm(),
        'code_sample_upload_file_action': code_sample_upload_file_action,
        }

    if self.data.GET.get('file', None) == '0':
      context['code_sample_upload_file_form'].addFileRequiredError()

    return context

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'modules/gsoc/project_details/_upload_code_samples.html'


class ProjectDetailsUpdate(base.GSoCRequestHandler):
  """Encapsulate the methods required to generate Project Details update form.
  """

  def templatePath(self):
    return 'modules/gsoc/project_details/update.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""
    return [
        url(r'project/update/%s$' % url_patterns.USER_ID, self,
            name=url_names.GSOC_PROJECT_UPDATE)
    ]

  def checkAccess(self, data, check, mutator):
    """Access checks for GSoC project details page."""
    mutator.projectFromKwargs()
    check.canUpdateProject()

  def context(self, data, check, mutator):
    """Handler to for GSoC project details page HTTP get request."""
    project_details_form = ProjectDetailsForm(
        data=data.POST or None, instance=data.project)

    context = {
        'page_name': 'Update project details',
        'project': data.project,
        'forms': [project_details_form],
        'error': project_details_form.errors,
    }

    if len(data.project.passed_evaluations) >= \
        project_logic.NUMBER_OF_EVALUATIONS:
      context['upload_code_samples'] = UploadCodeSamples(data)
      context['list_code_samples'] = ListCodeSamples(data, True)

    return context

  def validate(self, data):
    """Validate the form data and save if valid."""
    project_details_form = ProjectDetailsForm(
        data=data.POST or None, instance=data.project)

    if project_details_form.is_valid():
      project_details_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Post handler for the project details update form."""
    if self.validate(data):
      url = links.LINKER.userId(
          data.url_profile.key(), data.project.key().id(),
          url_names.GSOC_PROJECT_DETAILS)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class CodeSampleUploadFilePost(base.GSoCRequestHandler):
  """Handler for POST requests to upload files with code samples."""

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""
    return [
        url(r'project/code_sample/upload/%s$' % url_patterns.USER_ID, self,
            name=url_names.GSOC_PROJECT_CODE_SAMPLE_UPLOAD)
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
    check.isProjectCompleted()
    check.canUpdateProject()

  def post(self, data, check, mutator):
    """Post handler for the code sample upload file."""
    assert isSet(data.project)

    form = CodeSampleUploadFileForm(
        data=data.POST, files=data.request.file_uploads)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blob from the cloud
      for blob_info in data.request.file_uploads.itervalues():
        blob_info.delete()
      url = links.LINKER.userId(
          data.url_profile.key(), data.project.key().id(),
          url_names.GSOC_PROJECT_UPDATE)
      # TODO(daniel): GET params should be handled automatically
      url = url + '?file=0'
      return http.HttpResponseRedirect(url)

    form.cleaned_data['user'] = data.user
    form.cleaned_data['org'] = data.project.org
    form.cleaned_data['program'] = data.project.program

    project_key = data.project.key()
    code_sample = form.create(commit=False, parent=project_key)

    def txn():
      code_sample.put()

      project = GSoCProject.get(project_key)
      if not project.code_samples_submitted:
        project.code_samples_submitted = True
        project.put()

    db.run_in_transaction(txn)

    url = links.LINKER.userId(
        data.url_profile.key(), data.project.key().id(),
        url_names.GSOC_PROJECT_UPDATE)
    return http.HttpResponseRedirect(url)


class CodeSampleDownloadFileGet(base.GSoCRequestHandler):
  """Handler for POST requests to download files with code samples."""

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""
    return [
        url(r'project/code_sample/download/%s$' % url_patterns.USER_ID, self,
            name=url_names.GSOC_PROJECT_CODE_SAMPLE_DOWNLOAD)
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
    check.isProjectCompleted()

  def get(self, data, check, mutator):
    """Get handler for the code sample download file."""
    assert isSet(data.project)

    try:
      id_value = int(data.request.GET['id'])
      code_sample = GSoCCodeSample.get_by_id(id_value, data.project)
      if not code_sample or not code_sample.upload_of_work:
        raise exception.BadRequest(
            message='Requested project or code sample not found')
      else:
        return bs_helper.sendBlob(code_sample.upload_of_work)
    except KeyError:
      raise exception.BadRequest(message='id argument missing in GET data')
    except ValueError:
      raise exception.BadRequest(
          message='id argument in GET data is not a number')


class CodeSampleDeleteFilePost(base.GSoCRequestHandler):
  """Handler for POST requests to delete code sample files."""

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""
    return [
        url(r'project/code_sample/delete/%s$' % url_patterns.USER_ID, self,
            name=url_names.GSOC_PROJECT_CODE_SAMPLE_DELETE)
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
    check.isProjectCompleted()
    check.canUpdateProject()

  def post(self, data, check, mutator):
    """Get handler for the code sample delete file."""
    assert isSet(data.project)

    try:
      id_value = int(data.request.POST['id'])
      code_sample = GSoCCodeSample.get_by_id(id_value, data.project)

      if not code_sample:
        raise exception.BadRequest(message='Requested code sample not found')

      upload_of_work = code_sample.upload_of_work

      def txn():
        code_sample.delete()
        if upload_of_work:
          # this is executed outside of transaction
          upload_of_work.delete()

        if data.project.countCodeSamples() <= 1:
          project = GSoCProject.get(data.project.key())
          project.code_samples_submitted = False
          project.put()

      db.run_in_transaction(txn)

      url = links.LINKER.userId(
          data.url_profile.key(), data.project.key().id(),
          url_names.GSOC_PROJECT_UPDATE)
      return http.HttpResponseRedirect(url)
    except KeyError:
      raise exception.BadRequest(message='id argument missing in POST data')
    except ValueError:
      raise exception.BadRequest(
          message='id argument in POST data is not a number')


class UserActions(Template):
  """Template to render the left side user actions.
  """

  DEF_FEATURED_PROJECT_HELP = ugettext(
      'Choosing Yes features this project on program home page. The '
      'project is featured when Yes is displayed in bright orange.')

  def __init__(self, data):
    super(UserActions, self).__init__(data)
    self.toggle_buttons = []

  def context(self):
    """See template.Template.context for specification."""
    featured_project_url = links.LINKER.userId(
        self.data.url_profile.key(), self.data.project.key().id(),
        'gsoc_featured_project')

    featured_project = ToggleButtonTemplate(
        self.data, 'on_off', 'Featured', 'project-featured',
        featured_project_url, checked=self.data.project.is_featured,
        help_text=self.DEF_FEATURED_PROJECT_HELP,
        labels={
            'checked': 'Yes',
            'unchecked': 'No'})
    self.toggle_buttons.append(featured_project)

    context = {
        'title': 'Project Actions',
        'toggle_buttons': self.toggle_buttons,
        }

    assign_mentor_url = links.LINKER.userId(
        self.data.url_profile.key(), self.data.project.key().id(),
        'gsoc_project_assign_mentors')
    all_mentors_keys = profile_logic.queryAllMentorsKeysForOrg(
        self.data.project.org)
    context['assign_mentor'] = assign_mentor.AssignMentorFields(
        self.data, self.data.project.mentors, assign_mentor_url,
        all_mentors=all_mentors_keys, mentor_required=True,
        allow_multiple=True)

    return context

  def templatePath(self):
    return "modules/gsoc/project_details/_user_action.html"


def _isUpdateLinkVisible(data):
  """Determines whether the current user is allowed to update the project
  and therefore if the project update link should visible or not.

  Args:
    data: a RequestData object

  Returns: True if the update link should be visible, False otherwise.
  """
  # program hosts are able to edit project details
  if data.is_host:
    return True

  # users without active profiles cannot definitely update projects
  if not data.profile or data.profile.status != 'active':
    return False

  # only passed and valid project can be updated
  if data.project.status in ['invalid', 'withdrawn', 'failed']:
    return False

  # a student who own the project can update it
  if data.project.parent_key() == data.profile.key():
    return True

  # org admins of the organization that manages the project can update it
  org_key = GSoCProject.org.get_value_for_datastore(data.project)
  if data.orgAdminFor(org_key):
    return True

  # no other users are permitted to update project
  return False


def _getUpdateLinkText(data):
  """Returns text which may be used to display update project link.

  Args:
    request: a RequestData object

  Returns: a string with the text to be used with update project link
  """
  if data.timeline.afterFormSubmissionStart():
    return 'Update or Upload Code Samples'
  else:
    return 'Update'


class ProjectDetails(base.GSoCRequestHandler):
  """Encapsulate all the methods required to generate GSoC project
  details page.
  """

  def templatePath(self):
    return 'modules/gsoc/project_details/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""

    return [
        url(r'project/%s$' % url_patterns.USER_ID, self,
            name=url_names.GSOC_PROJECT_DETAILS)
    ]

  def checkAccess(self, data, check, mutator):
    """Access checks for GSoC project details page."""
    mutator.projectFromKwargs()

  def context(self, data, check, mutator):
    """Handler to for GSoC project details page HTTP get request."""

    org_home_link = links.LINKER.organization(
        data.project.org.key(), urls.UrlNames.ORG_HOME)
    context = {
        'page_name': 'Project details',
        'project': data.project,
        'org_home_link': org_home_link,
    }

    if data.orgAdminFor(data.project.org):
      context['user_actions'] = UserActions(data)

    if _isUpdateLinkVisible(data):
      update_link_url = links.LINKER.userId(
          data.url_profile.key(), data.project.key().id(),
          url_names.GSOC_PROJECT_UPDATE)
      context['update_link_visible'] = True
      context['update_link_url'] = update_link_url
      context['update_link_text'] = _getUpdateLinkText(data)
    else:
      context['update_link_visible'] = False

    if len(data.project.passed_evaluations) >= \
        project_logic.NUMBER_OF_EVALUATIONS:
      context['list_code_samples'] = ListCodeSamples(data, False)

    return context


class AssignMentors(base.GSoCRequestHandler):
  """View which handles assigning mentor to a project."""

  def djangoURLPatterns(self):
    return [
         url(r'project/assign_mentors/%s$' % url_patterns.USER_ID,
         self, name='gsoc_project_assign_mentors'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
    assert isSet(data.project.org)
    check.isOrgAdminForOrganization(data.project.org)

  def assignMentors(self, data, mentor_keys):
    """Assigns the mentor to the project.

    Args:
      data: A RequestData describing the current request.
      mentor_keys: List of mentor profile keys to to be assigned
          to the project.
    """
    assert isSet(data.project)

    project_key = data.project.key()

    def assign_mentor_txn():
      project = db.get(project_key)

      project.mentors = mentor_keys

      db.put(project)

    db.run_in_transaction(assign_mentor_txn)

  def validate(self, data):
    str_mentor_keys = data.POST.getlist('assign_mentor')

    if str_mentor_keys:
      org = data.project.org

      # need the list to set conversion and back to list conversion
      # to ensure that same mentor doesn't get assigned to the
      # project more than once
      mentor_keys = set([db.Key(k) for k in str_mentor_keys if k])
      if mentor_keys < set(
          profile_logic.queryAllMentorsKeysForOrg(org)):
        return list(mentor_keys)
      else:
        raise exception.BadRequest(message="Invalid post data.")

    return None

  def post(self, data, check, mutator):
    assert isSet(data.project)

    mentor_keys = self.validate(data)
    if mentor_keys:
      self.assignMentors(data, mentor_keys)

    url = links.LINKER.userId(
        data.url_profile.key(), data.project.key().id(),
        url_names.GSOC_PROJECT_UPDATE)
    return http.HttpResponseRedirect(url)

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exception.MethodNotAllowed()


class FeaturedProject(base.GSoCRequestHandler):
  """View which handles making the project featured by toggle button."""

  def djangoURLPatterns(self):
    return [
         url(r'project/featured/%s$' % url_patterns.USER_ID,
         self, name='gsoc_featured_project'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
    assert isSet(data.project.org)
    check.isOrgAdminForOrganization(data.project.org)

  def toggleFeatured(self, data, value):
    """Makes the project featured.

    Args:
      data: A RequestData describing the current request.
      value: can be either "checked" or "unchecked".
    """
    assert isSet(data.project)

    if value != 'checked' and value != 'unchecked':
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'checked' and not data.project.is_featured:
      raise exception.BadRequest(message="Invalid post data.")
    if value == 'unchecked' and data.project.is_featured:
      raise exception.BadRequest(message="Invalid post data.")

    project_key = data.project.key()

    def make_featured_txn():
      # transactionally get latest version of the project
      project = db.get(project_key)
      if value == 'unchecked':
        project.is_featured = True
      elif value == 'checked':
        project.is_featured = False

      db.put(project)

    db.run_in_transaction(make_featured_txn)

  def post(self, data, check, mutator):
    value = data.POST.get('value')
    self.toggleFeatured(data, value)
    return http.HttpResponse()

  def get(self, data, check, mutator):
    """Special Handler for HTTP GET since this view only handles POST."""
    raise exception.MethodNotAllowed()
