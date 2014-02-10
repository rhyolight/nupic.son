# Copyright 2008 the Melange authors.
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

"""Seeds or clears the datastore.
"""


import itertools
import datetime

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http

from melange.models import education
from melange.models import address
from melange.models import contact
from melange.models import profile as profile_model
from melange.models import user

from soc.logic import accounts
from soc.models.document import Document

from soc.models import program as program_model
from soc.models import org_app_survey as org_app_survey_model
from soc.models.site import Site
from soc.models.sponsor import Sponsor

from soc.models.survey import Survey
from soc.models.survey_record import SurveyRecord

from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.score import GCIScore
from soc.modules.gci.models.timeline import GCITimeline
from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.models.task import DifficultyLevel
from soc.modules.gci.models.task import GCITask

from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.timeline import GSoCTimeline

from summerofcode.models import organization as soc_org_model
from summerofcode.models import profile as soc_profile


def seed(request, *args, **kwargs):
  """Seeds the datastore with some default values.
  """

  site_properties = {
      'key_name': 'site',
      'latest_gsoc': 'google/gsoc2014',
      'latest_gci': 'google/gci2013',
      }
  site = Site(**site_properties)
  site.put()

  account = accounts.getCurrentAccount()

  if not account:
    account = users.User(email='test@example.com')

  user_properties = {
      'id': 'test',
      'account_id': account.user_id(),
      'account': account,
      }
  current_user = user.User(**user_properties)
  current_user.put()

  group_properties = {
       'key_name': 'google',
       'link_id': 'google',
       'name': 'Google Inc.',
       'short_name': 'Google',
       'home_page': 'http://www.google.com',
       'email': 'ospo@google.com',
       'description': 'This is the profile for Google.',
       'contact_street': 'Some Street',
       'contact_city': 'Some City',
       'contact_country': 'United States',
       'contact_postalcode': '12345',
       'phone': '15551110000',
       'status': 'active',
       }
  google = Sponsor(**group_properties)
  google.put()

  now = datetime.datetime.now()
  before = now - datetime.timedelta(365)
  after = now + datetime.timedelta(365)

  timeline_properties = {
      'key_name': 'google/gsoc2014',
      'link_id': 'gsoc2014',
      'scope': google,
      'program_start': before,
      'program_end': after,
      'accepted_organization_announced_deadline': before,
      'accepted_students_announced_deadline' : after,
      'student_signup_start': before,
      'student_signup_end': after,
      'application_review_deadline': after,
      'student_application_matched_deadline': after,
      'accepted_students_announced_deadline': after,
      'form_submission_start':before,
  }
  gsoc2014_timeline = GSoCTimeline(**timeline_properties)
  gsoc2014_timeline.put()

  program_properties = {
      'key_name': 'google/gsoc2014',
      'link_id': 'gsoc2014',
      'program_id': 'gsoc2014',
      'sponsor': google,
      'scope': google,
      'name': 'Google Summer of Code 2014',
      'short_name': 'GSoC 2014',
      'description': 'This is the program for GSoC 2014.',
      'apps_tasks_limit': 42,
      'slots': 42,
      'timeline': gsoc2014_timeline,
      'status': program_model.STATUS_VISIBLE,
      }
  gsoc2014 = GSoCProgram(**program_properties)
  gsoc2014.put()

  timeline_properties.update({
      'key_name': 'google/gsoc2010',
      'link_id': 'gsoc2010',
  })
  gsoc2010_timeline = GSoCTimeline(**timeline_properties)
  gsoc2010_timeline.put()

  program_properties.update({
      'key_name': 'google/gsoc2010',
      'link_id': 'gsoc2010',
      'program_id': 'gsoc2010',
      'name': 'Google Summer of Code 2010',
      'description': 'This is the program for GSoC 2010.',
      'short_name': 'GSoC 2010',
      'timeline': gsoc2010_timeline,
  })
  gsoc2010 = GSoCProgram(**program_properties)
  gsoc2010.put()

  # TODO(drew): Replace gsoc2014.prefix with whatever its replacement becomes
  # once prefix is removed from program and no longer used in the query for
  # OrgAppSurvey in soc.views.helper.RequestData._getProgramWideFields().
  org_app_survey_properties = {
    'key_name' : '%s/%s/orgapp' % (gsoc2014.prefix, gsoc2014.key().name()),
    'program' : gsoc2014,
    'title' : 'Org App Survey',
    'content' : 'Here is some content.',
    'modified_by' : current_user.key.to_old_key(),
    'survey_start' : before,
    'survey_end' : after
  }
  org_app_survey_model.OrgAppSurvey(**org_app_survey_properties).put()

  org_app_survey_properties['program'] = gsoc2010
  org_app_survey_model.OrgAppSurvey(**org_app_survey_properties).put()

  timeline_properties = {
        'key_name': 'google/gci2013',
        'link_id': 'gci2013',
        'scope': google,
        'program_start': before,
        'program_end': after,
        'accepted_organization_announced_deadline': before,
        'student_signup_start': before,
        'student_signup_end': after,
        'tasks_publicly_visible': before,
        'task_claim_deadline': after,
        'stop_all_work_deadline': after,
  }
  gci2013_timeline = GCITimeline(**timeline_properties)
  gci2013_timeline.put()

  program_properties.update({
      'key_name': 'google/gci2013',
      'link_id': 'gci2013',
      'program_id': 'gci2013',
      'name': 'Google Code In Contest 2013',
      'short_name': 'GCI 2009',
      'description': 'This is the program for GCI 2013.',
      'timeline': gci2013_timeline,
      })
  gci2013 = GCIProgram(**program_properties)
  gci2013.put()

  site.active_program = gci2013
  site.put()

  current_user.host_for = [
      ndb.Key.from_old_key(gsoc2010.key()),
      ndb.Key.from_old_key(gsoc2014.key()),
      ndb.Key.from_old_key(gci2013.key())]
  current_user.put()

  group_properties.update({
    'key_name': 'google/gci2013/melange',
    'link_id': 'melange',
    'name': 'Melange Development Team',
    'short_name': 'Melange',
    'scope': gci2013,
    'program': gci2013,
    'sponsor': google,
    'home_page': 'http://code.google.com/p/soc',
    'description': 'Melange, share the love!',
    'license_name': 'Apache License',
    'ideas': 'http://code.google.com/p/soc/issues',
    })
  melange = GCIOrganization(**group_properties)
  melange.put()

  group_properties.update({
    'scope': gsoc2014,
    'program': gsoc2014,
    })

  address_properties = address.Address(
      street='1 Test St.',
      city='Some City',
      country='United States',
      postal_code='12345')
  address_properties.put()

  contact_info = contact.Contact(email='test@example.com')
  contact_info.put()

  gsoc_delta = datetime.timedelta(days=(365 * 18))

  profile_properties = {
      'id': gsoc2014.key().name() + '/' + current_user.key.id(),
      'parent': current_user.key,
      'public_name': 'test',
      'program': ndb.Key.from_old_key(gsoc2014.key()),
      'first_name': 'Test',
      'last_name': 'Example',
      'contact' : contact_info,
      'residential_address' : address_properties,
      'shipping_address' : address_properties,
      'birth_date' : datetime.date.today() - gsoc_delta,
      'program_knowledge' : 'Friend referral',
      }
  profile = profile_model.Profile(**profile_properties)

  ndb_orgs = []
  for i in range(15):
    group_properties.update({
        'key_name': 'google/gsoc2014/org_%d' % i,
        'link_id': 'org_%d' % i,
        'name': 'Organization %d' % i,
        'short_name': 'Org %d' % i,
        'description': 'Organization %d!' % i,
        })

    org_properties = {
        'name': 'Organization %d' % i,
        'org_id': 'org_%d' % i,
        'program': ndb.Key.from_old_key(gsoc2014.key()),
        'description': 'Organization %d!' % i,
        }
    org = soc_org_model.SOCOrganization(
        id='google/gsoc2014/org_%d' % i, **org_properties)
    org.put()
    ndb_orgs.append(org)

    # Admin (and thus mentor) for the first org
    if i == 0:
      profile.admin_for.append(org.key)
      profile.mentor_for.append(org.key)
      profile.put()

    # Mentor for the second org
    if i == 1:
      profile.mentor_for.append(org.key)
      profile.put()

  profile_properties.update({
      'id': gci2013.key().name() + '/' + current_user.key.id(),
      'parent': current_user.key,
      'program': ndb.Key.from_old_key(gci2013.key()),
      'admin_for': [ndb.Key.from_old_key(melange.key())],
      'mentor_for': [ndb.Key.from_old_key(melange.key())],
      })
  melange_admin = profile_model.Profile(**profile_properties)
  # TODO: add GCI orgs
  melange_admin.put()

  task_properties = {
      'status': 'Open',
      'modified_by': melange_admin.key.to_old_key(),
      'subscribers': [melange_admin.key.to_old_key()],
      'title': 'Awesomeness',
      'created_by': melange_admin.key.to_old_key(),
      'created_on': now,
      'program': gci2013,
      'time_to_complete': 1337,
      'modified_on': now,
      'org': melange.key(),
      'description': '<p>AWESOME</p>',
      'difficulty_level': DifficultyLevel.MEDIUM,
      'types': ['Code']
  }
  gci_task = GCITask(**task_properties)
  gci_task.put()

  user_properties = {
      'id': 'student',
      'account_id': '12345',
      'account': users.User(email='student@example.com'),
      }
  student_user = user.User(**user_properties)
  student_user.put()

  gci_delta = datetime.timedelta(days=(365 * 14))

  contact_properties = contact.Contact(
      email='student@email.com',
      web_page='http://www.homepage.com/',
      blog='http://www.blog.com/',
      phone='1650253000')
  contact_properties.put()

  graduation_year = datetime.date.today() + datetime.timedelta(days=365)

  student_data = soc_profile.SOCStudentData(
      education=education.Education(
          school_id="123",
          school_country="United States",
          expected_graduation=int(graduation_year.strftime('%Y')),
          major='Some Major',
          degree=education.Degree.UNDERGRADUATE)
      )
  student_data.put()

  student_id = 'student'
  student_properties = {
      'id': gsoc2014.key().name() + "/" + student_id,
      'parent': student_user.key,
      'program': ndb.Key.from_old_key(gsoc2014.key()),
      'public_name': 'Student',
      'first_name': 'Student',
      'last_name': 'Student',
      'contact' : contact_properties,
      'residential_address' : address_properties,
      'shipping_address' : address_properties,
      'birth_date': datetime.date.today() - gci_delta,
      'tee_size': profile_model.TeeSize.L,
      'tee_style': profile_model.TeeStyle.MALE,
      'gender' : profile_model.Gender.MALE,
      'program_knowledge': 'Friend referral.',
      'student_data' : student_data,
      }
  melange_student = profile_model.Profile(**student_properties)
  melange_student.put()

  student_id = 'student2'
  user_properties = {
      'id': student_id,
      'account_id': 'student2',
      'account': users.User(email='student2@example.com'),
      }
  student_user2 = user.User(**user_properties)
  student_user2.put()

  student_properties.update({
      'id': gsoc2014.key().name() + "/" + student_id,
      'parent': student_user2.key,
      'first_name' : 'Student 2',
      'last_name' : 'Example'
  })
  melange_student2 = profile_model.Profile(**student_properties)
  melange_student2.put()

  proposal_properties = {
      'parent': melange_student.key.to_old_key(),
      'program': gsoc2014,
      'title': 'test proposal',
      'abstract': 'test abstract',
      'content': 'test content',
      'mentor': profile.key.to_old_key(),
      'status': 'accepted',
      'has_mentor': True,
      'org': ndb_orgs[0].key.to_old_key(),
      'possible_mentors': [profile.key.to_old_key()]
      }
  melange_proposal = GSoCProposal(**proposal_properties)
  melange_proposal.put()

  project_properties = {
      'title': 'test project',
      'abstract': 'test abstract',
      'status': 'accepted',
      'parent': melange_student.key.to_old_key(),
      'mentors': [profile.key.to_old_key()],
      'program':  gsoc2014,
      'org': ndb_orgs[0].key.to_old_key(),
      'proposal' : melange_proposal.key(),
       }
  melange_project = GSoCProject(**project_properties)
  melange_project.put()
  ndb_orgs[1].slot_allocation = 1
  ndb_orgs[1].put()

  student_data.number_of_projects = 1
  student_data.number_of_proposals = 1
  student_data.project_for_orgs = [ndb_orgs[1].key]

  melange_student.put()
  melange_student2.put()

  project_properties.update({
      'student': melange_student2,
      'title': 'test project2'
      })
  melange_project2 = GSoCProject(**project_properties)
  melange_project2.put()
  ndb_orgs[1].slot_allocation += 1
  ndb_orgs[1].put()

  student_id = 'student'
  student_properties.update({
      'id': gci2013.key().name() + '/' + student_id,
      'parent': student_user.key,
      'program': ndb.Key.from_old_key(gci2013.key()),
  })
  gci_student = profile_model.Profile(**student_properties)
  gci_student.put()

  score_properties = {
      'parent': gci_student.key.to_old_key(),
      'program': gci2013,
      'points': 5,
      'tasks': [gci_task.key()]
      }
  score = GCIScore(**score_properties)
  score.put()

  document_properties = {
      'key_name': 'site/site/home',
      'link_id': 'home',
      'scope': site,
      'prefix': 'site',
      'author': current_user.key.to_old_key(),
      'title': 'Home Page',
      'content': 'This is the Home Page',
      'modified_by': current_user.key.to_old_key(),
      }
  home_document = Document(**document_properties)
  home_document.put()

  document_properties = {
      'key_name': 'user/test/notes',
      'link_id': 'notes',
      'scope': current_user.key.to_old_key(),
      'prefix': 'user',
      'author': current_user.key.to_old_key(),
      'title': 'My Notes',
      'content': 'These are my notes',
      'modified_by': current_user.key.to_old_key(),
      }
  notes_document = Document(**document_properties)
  notes_document.put()

  site.home = home_document
  site.put()

  memcache.flush_all()

  return http.HttpResponse('Done')

def clear(*args, **kwargs):
  """Removes all entities from the datastore.
  """

  # TODO(dbentley): If there are more than 1000 instances of any model,
  # this method will not clear all instances.  Instead, it should continually
  # call .all(), delete all those, and loop until .all() is empty.
  entities = itertools.chain(*[
      Survey.all(),
      SurveyRecord.all(),
      GCIOrganization.all(),
      GSoCTimeline.all(),
      GCITimeline.all(),
      GSoCProgram.all(),
      GSoCProject.all(),
      GSoCProposal.all(),
      GCIProgram.all(),
      GCIScore.all(),
      GSoCStudentInfo.all(),
      GCIStudentInfo.all(),
      GCITask.all(),
      Sponsor.all(),
      Site.all(),
      Document.all(),
      # The below models are all subclasses of ndb.Model and therefore must
      # use .query() to return all instances instead of .all().
      soc_org_model.SOCOrganization.query(),
      profile_model.Profile.query(),
      soc_profile.SOCStudentData.query(),
      user.User.query(),
      address.Address.query(),
      contact.Contact.query()
      ])

  try:
    for entity in entities:
      if isinstance(entity, ndb.Model):
        entity.key.delete()
      else:
        entity.delete()
  except db.Timeout:
    return http.HttpResponseRedirect('#')
  memcache.flush_all()

  return http.HttpResponse('Done')


def reseed(*args, **kwargs):
  """Clears and seeds the datastore.
  """

  clear(*args, **kwargs)
  seed(*args, **kwargs)

  return http.HttpResponse('Done')
