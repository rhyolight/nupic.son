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

"""Tests for organization applications."""

import json

from datetime import datetime
from datetime import timedelta

from google.appengine.ext import db
from google.appengine.ext import ndb

from soc.models import org_app_survey
from soc.models import org_app_record

from soc.modules.gci.models import program as program_model

from tests import org_utils
from tests import test_utils
from tests import survey_utils
from tests import profile_utils
from tests import program_utils
from tests import timeline_utils


class GCIOrgAppEditPageTest(test_utils.GCIDjangoTestCase):
  """Tests for organization applications edit page.
  """

  def setUp(self):
    self.init()
    self.url = '/gci/org/application/edit/%s' % self.gci.key().name()
    self.post_params = {
        'title': 'Test Title',
        'short_name': 'Test Short Name',
        'content': 'Test Content',
        'survey_start': '2011-10-13 00:00:00',
        'survey_end': '2011-10-13 00:00:00',
        'schema': 'Test Scheme',
    }

  def assertTemplatesUsed(self, response):
    """Asserts all the templates for edit page were used."""
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/org_app/edit.html')
    self.assertTemplateUsed(response, 'modules/gci/_form.html')

  def testProgramHostAccessGranted(self):
    """Asserts program administrators can access the page."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self.url)
    self.assertResponseOK(response)

  def testLoneUserAccessDenied(self):
    """Asserts lone users cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    response = self.get(self.url)
    self.assertResponseForbidden(response)

  def testEditPage(self):
    """Tests organization applications edit page."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self.url)
    self.assertTemplatesUsed(response)

    response = self.post(self.url, self.post_params)
    self.assertResponseRedirect(response, '%s?validated' % self.url)

    query = org_app_survey.OrgAppSurvey.all().filter('program = ', self.gci)
    self.assertEqual(query.count(), 1,
                     ('There must be one and only one OrgAppSurvey '
                      'instance for the program.'))

    survey = query.get()
    self.assertEqual(survey.title, self.post_params['title'])
    self.assertEqual(
        org_app_survey.OrgAppSurvey.modified_by.get_value_for_datastore(survey),
        user.key.to_old_key())


class GCIOrgAppTakePageTest(test_utils.GCIDjangoTestCase):
  """Tests for organizations to submit and edit their application.
  """

  def setUp(self):
    self.init()

    # make org up survey active
    self.updateOrgAppSurvey()

    self.take_url = '/gci/org/application/%s' % self.gci.key().name()
    self.retake_url_raw = '/gci/org/application/%s/%s'

    self.post_params = {
      'org_id': 'melange',
      'name': 'Melange',
      'description': 'Melange',
      'home_page': 'code.google.com/p/soc',
      'license': 'Apache License, 2.0',
      'new_org': 'Veteran',
      'agreed_to_admin_agreement': 'on',
      'item': 'test',
    }

  def assertTemplatesUsed(self, response):
    """Asserts all the templates for edit page were used.
    """

    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/org_app/take.html')

  def updateOrgAppSurvey(self, survey_start=None, survey_end=None):
    """Create an organization application survey.
    """

    if survey_start is None:
      survey_start = datetime.now()

    if survey_end is None:
      survey_end = survey_start + timedelta(days=10)

    self.org_app.survey_start = survey_start
    self.org_app.survey_end = survey_end
    self.org_app.put()

  def testLoneUserAccessDenied(self):
    """Tests that users without profiles cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    response = self.get(self.take_url)
    self.assertResponseForbidden(response)

  def testCodeInStudentAccessDenied(self):
    """Tests that Code-in student cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(self.take_url)
    self.assertResponseForbidden(response)

  def testSummerOfCodeStudentAccessDenied(self):
    """Tests that Summer Of Code student cannot access the page."""
    # seed Summer Of Code program
    soc_program = program_utils.seedGSoCProgram()

    # seed Summer Of Code student
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(soc_program, user=user)

    response = self.get(self.take_url)
    self.assertResponseForbidden(response)

  def testSummerOfCodeProfileAccessDenied(self):
    """Tests that Summer Of Code profile (no role) cannot access the page."""
    # seed Summer Of Code program
    soc_program = program_utils.seedGSoCProgram()

    # seed Summer Of Code student
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(soc_program.key(), user=user)

    response = self.get(self.take_url)
    self.assertResponseForbidden(response)

  def testSummerOfCodeOrgAdminAccessGranted(self):
    """Tests that Summer Of Code org admins need a new profile first."""
    # seed Summer Of Code program and organization
    soc_program = program_utils.seedGSoCProgram()
    soc_org = org_utils.seedSOCOrganization(soc_program.key())

    # seed Summer Of Code org admin
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        soc_program.key(), user=user, admin_for=[soc_org.key])

    response = self.get(self.take_url)
    self.assertResponseRedirect(response)

  def testCodeInOrgAdminAccessGranted(self):
    """Tests that Code In org admins can access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.take_url)
    self.assertResponseOK(response)

  def testOtherCodeInOrgAdminRedirected(self):
    """Tests that org admin for another Code In needs a new profile first."""
    # seed another Code In program and organization
    ci_program_helper = program_utils.GCIProgramHelper()
    other_ci_program = ci_program_helper.createProgram()
    other_ci_org = ci_program_helper.createOrUpdateOrg()

    # seed Code In org admin for that program and organization
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        other_ci_program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(other_ci_org.key())])

    # user must create profile for this program first
    response = self.get(self.take_url)
    self.assertResponseRedirect(response)

  def testPreActivePeriodAccessDenied(self):
    """Tests that access is forbidden before org application is active."""
    # make org application active in the future
    self.updateOrgAppSurvey(survey_start=timeline_utils.future(delta=100),
        survey_end=timeline_utils.future(delta=150))

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.take_url)
    self.assertResponseForbidden(response)

  def testPostActivePeriodAccessDenied(self):
    """Tests that access is forbidden after org application is closed."""
    # make org application active in the past
    self.updateOrgAppSurvey(survey_start=timeline_utils.past(delta=150),
        survey_end=timeline_utils.past(delta=100))

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.take_url)
    self.assertResponseForbidden(response)

  def testAccessCheckWithoutSurvey(self):
    self.org_app.delete()

    response = self.get(self.take_url)
    self.assertResponseNotFound(response)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.take_url)
    self.assertResponseNotFound(response)

  def testOrgAppSurveyTakePage(self):
    """Tests organizationn application survey take/retake page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    main_admin = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    backup_admin = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.take_url)
    self.assertTemplatesUsed(response)

    params = {
        'admin_id': main_admin.key.parent().id(),
        'backup_admin_id': backup_admin.key.parent().id()
        }
    params.update(self.post_params)
    response = self.post(self.take_url, params)
    query = org_app_record.OrgAppRecord.all()
    query.filter('main_admin', main_admin.key.parent().to_old_key())
    self.assertEqual(query.count(), 1, 'Survey record is not created.')

    record = query.get()
    self.assertEqual(record.org_id, self.post_params['org_id'])
    self.assertEqual(record.name, self.post_params['name'])
    self.assertEqual(record.description, self.post_params['description'])
    self.assertEqual(record.license, self.post_params['license'])

    main_admin_key = (
        org_app_record.OrgAppRecord.main_admin.get_value_for_datastore(record))
    self.assertEqual(main_admin_key, user.key.to_old_key())

    backup_admin_key = (
        org_app_record.OrgAppRecord.backup_admin
            .get_value_for_datastore(record))
    self.assertEqual(backup_admin_key, backup_admin.key.parent().to_old_key())

    retake_url = self.retake_url_raw % (self.gci.key().name(),
                                        record.key().id())
    self.assertResponseRedirect(response, retake_url + '?validated')

    response = self.get(retake_url)
    self.assertResponseOK(response)

    params = {'backup_admin_id': backup_admin.key.parent().id()}
    params.update(self.post_params)
    params['name'] = 'New title'

    response = self.post(retake_url, params)
    self.assertResponseRedirect(response, retake_url + '?validated')
    record = org_app_record.OrgAppRecord.get_by_id(record.key().id())
    self.assertEqual(record.name, params['name'])


TEST_ACCEPTED_ORGS_MSG = 'Organization accepted'
TEST_REJECTED_ORGS_MSG = 'Organization rejected'

class GCIOrgAppRecordsPageTest(test_utils.GCIDjangoTestCase):
  """Tests for organization applications edit page.
  """

  def setUp(self):
    super(GCIOrgAppRecordsPageTest, self).setUp()
    self.init()
    self.record = survey_utils.SurveyHelper(
        self.gci, self.dev_test, self.org_app)
    self.url = '/gci/org/application/records/%s' % self.gci.key().name()

  def assertTemplatesUsed(self, response):
    """Asserts all the templates for edit page were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'soc/org_app/records.html')

  def dataPostSingle(self, url, record, status):
    return self.dataPost(url, {record: status})

  def dataPost(self, url, changes):
    values = {}

    for record, status in changes.iteritems():
      record_data = {
          'status': status,
      }
      record_id = record.key().id()

      values[record_id] = record_data

    data = json.dumps(values)

    postdata = {
        'data': data,
        'button_id': 'save',
        'idx': 0,
    }

    return self.post(url, postdata)

  def testGetRecords(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # set acceptance / rejection messages
    program_messages = (
        program_model.GCIProgramMessages.all().ancestor(self.program).get())
    program_messages.accepted_orgs_msg = TEST_ACCEPTED_ORGS_MSG
    program_messages.rejected_orgs_msg = TEST_REJECTED_ORGS_MSG
    program_messages.put()

    record = self.record.createOrgAppRecord(
        'org1', user.key, user.key, {'status': 'needs review'})

    response = self.get(self.url)
    self.assertTemplatesUsed(response)

    list_data = self.getListData(self.url, 0)
    self.assertEqual(1, len(list_data))

    self.dataPostSingle(self.url, record, 'bogus')
    record = db.get(record.key())
    self.assertEqual('needs review', record.status)

    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    # self.assertEmailNotSent()

    self.dataPostSingle(self.url, record, 'pre-accepted')
    record = db.get(record.key())
    self.assertEqual('pre-accepted', record.status)

    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    # self.assertEmailNotSent()

    self.dataPostSingle(self.url, record, 'pre-rejected')
    record = db.get(record.key())
    self.assertEqual('pre-rejected', record.status)

    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    # self.assertEmailNotSent()

    self.dataPostSingle(self.url, record, 'accepted')
    record = db.get(record.key())
    self.assertEqual('accepted', record.status)
    #self.assertEmailSent(html=TEST_ACCEPTED_ORGS_MSG)

    self.dataPostSingle(self.url, record, 'rejected')
    record = db.get(record.key())
    self.assertEqual('rejected', record.status)
    #self.assertEmailSent(html=TEST_REJECTED_ORGS_MSG)

    # TODO(daniel): add a utility function for that?
    # self.assertEmailSent(n=2)
