#!/usr/bin/env python
#
# Copyright 2009 the Melange authors.
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

"""Starts an interactive shell with statistic helpers.
"""


import cPickle
import datetime
import operator
import sys
import time

import interactive


def dateFetch(queryGen, last=None, batchSize=100):
  """Iterator that yields an entity in batches.

  Args:
    queryGen: should return a Query object
    last: used to .filter() for last_modified_on
    batchSize: how many entities to retrieve in one datastore call

  Retrieved from http://tinyurl.com/d887ll (AppEngine cookbook).
  """

  from google.appengine.ext import db

  # AppEngine will not fetch more than 1000 results
  batchSize = min(batchSize,1000)

  query = None
  done = False
  count = 0

  while not done:
    print count
    query = queryGen()
    query.order('last_modified_on')
    if last:
      query.filter("last_modified_on > ", last)
    results = query.fetch(batchSize)
    for result in results:
      count += 1
      yield result
    if batchSize > len(results):
      done = True
    else:
      last = results[-1].last_modified_on


def addKey(target, fieldname):
  """Adds the key of the specified field.
  """

  result = target.copy()
  result['%s_key' % fieldname] = target[fieldname].key().name()
  return result


def getEntities(model, fields=None):
  """Returns all entities as dictionary keyed on their id_or_name property.
  """
  if not fields:
    fields = {}

  def gen():
    q = model.all()
    for key, value in fields.iteritems():
      q.filter(key, value)
    return q

  def wrapped():
    it = interactive.deepFetch(gen)

    entities = [(i.key().id_or_name(), i) for i in it]
    return dict(entities)

  return wrapped


def orgStats(target, orgs):
  """Retrieves org stats.
  """

  from soc.logic import dicts

  orgs = [(v.key(), v) for k, v in orgs.iteritems()]
  orgs = dict(orgs)

  grouped = dicts.groupby(target.values(), '_org')

  grouped = [(orgs[k], v) for k, v in grouped.iteritems()]
  popularity = [(k.link_id, len(v)) for k, v in grouped]

  return dict(grouped), dict(popularity)


def printPopularity(popularity):
  """Prints the popularity for the specified proposals.
  """

  g = operator.itemgetter(1)

  for item in sorted(popularity.iteritems(), key=g, reverse=True):
    print "%s: %d" % item


def saveValues(values, saver):
  """Saves the specified popularities.
  """

  import logging
  from google.appengine.ext import db

  from soc.models.organization import Organization

  def txn(key, value):
    org = Organization.get_by_key_name(key)
    saver(org, value)
    org.put()

  for key, value in sorted(values.iteritems()):
    print key
    db.run_in_transaction_custom_retries(10, txn, key, value)

  print "done"


def addFollower(follower, proposals, add_public=True, add_private=True):
  """Adds a user as follower to the specified proposals.

  Args:
    follower: the User to add as follower
    proposals: a list with the StudnetProposals that should be subscribed to
    add_public: whether the user is subscribed to public updates
    add_private: whether the user should be subscribed to private updates
  """

  from soc.models.review_follower import ReviewFollower

  result = []

  for i in proposals:
     properties = {
       'user': follower,
       'link_id': follower.link_id,
       'scope': i,
       'scope_path': i.key().name(),
       'key_name': '%s/%s' % (i.key().name(), follower.link_id),
       'subscribed_public': add_public,
       'subscribed_private': add_private,
     }

     entity = ReviewFollower(**properties)
     result.append(entity)

  return result


def convertProposals(org):
  """Convert all proposals for the specified organization.

  Args:
    org: the organization for which all proposals will be converted
  """

  from soc.logic.models.student_proposal import logic as proposal_logic
  from soc.logic.models.student_project import logic as project_logic

  proposals = proposal_logic.getProposalsToBeAcceptedForOrg(org)

  print "accepting %d proposals, with %d slots" % (len(proposals), org.slots)

  for proposal in proposals:
    fields = {
        'link_id': 't%i' % (int(time.time()*100)),
        'scope_path': proposal.org.key().id_or_name(),
        'scope': proposal.org,
        'program': proposal.program,
        'student': proposal.scope,
        'title': proposal.title,
        'abstract': proposal.abstract,
        'mentor': proposal.mentor,
        }

    project = project_logic.updateOrCreateFromFields(fields, silent=True)

    fields = {
        'status':'accepted',
        }

    proposal_logic.updateEntityProperties(proposal, fields, silent=True)

  fields = {
      'status': ['new', 'pending'],
      'org': org,
      }

  querygen = lambda: proposal_logic.getQueryForFields(fields)
  proposals = [i for i in interactive.deepFetch(querygen, batchSize=10)]

  print "rejecting %d proposals" % len(proposals)

  fields = {
      'status': 'rejected',
      }

  for proposal in proposals:
    proposal_logic.updateEntityProperties(proposal, fields, silent=True)


def deleteEntities(model, step_size=25):
  """Deletes all entities of the specified type
  """

  print "Deleting..."
  count = 0

  while True:
    entities = model.all().fetch(step_size)

    if not entities:
      break

    for entity in entities:
      entity.delete()

    count += step_size

    print "deleted %d entities" % count

  print "Done"


def loadPickle(name):
  """Loads a pickle.
  """

  f = open(name + '.dat')
  return cPickle.load(f)


def dumpPickle(target, name):
  """Dumps a pickle.
  """

  f = open("%s.dat" % name, 'w')
  cPickle.dump(target, f)


def addOrganizationToSurveyRecords(survey_record_model):
  """Set Organization in SurveyRecords entities of a given model.
  """
  
  print "Fetching %s." % survey_record_model.__name__
  getSurveyRecord = getEntities(survey_record_model)
  survey_records = getSurveyRecord()
  survey_records_amount = len(survey_records)
  print "Fetched %d %s." % (survey_records_amount, survey_record_model.__name__)
  
  counter = 0
  
  for key in survey_records.keys():
    survey_records[key].org = survey_records[key].project.scope
    survey_records[key].put()
    
    counter += 1
    print str(counter) + '/' + str(survey_records_amount) + ' ' + str(key)
    
  print "Organization added to all %s." % survey_record_model.__name__


def setOrganizationInSurveyRecords():
  """Sets Organization property in ProjectSurveyRecords 
  and GradingProjectSurveyRecords entities.
  """

  from soc.modules.gsoc.models.grading_project_survey_record \
      import GradingProjectSurveyRecord
  from soc.modules.gsoc.models.project_survey_record import ProjectSurveyRecord
  
  addOrganizationToSurveyRecords(ProjectSurveyRecord)
  addOrganizationToSurveyRecords(GradingProjectSurveyRecord)


def saveDataToCSV(csv_filename, data, key_order):
  """Saves data in order into CSV file.

  This is a helper function used for exporting CSV data.
  
  Args:
    csv_filename: The name of the file where to save the CSV data
    data: the data dict to write to CSV
    key_order: the order in which to export the data in data dict
  """

  import csv
  import StringIO

  from soc.logic import dicts

  file_handler = StringIO.StringIO()

  # ignore the extra data
  writer = csv.DictWriter(file_handler, key_order, extrasaction='ignore', dialect='excel')
  writer.writerow(dicts.identity(key_order))

  # encode the data to UTF-8 to ensure compatibiliy
  for row_dict in data:
    for key in row_dict.keys():
      value = row_dict[key]
      if isinstance(value, basestring):
        row_dict[key] = value.encode("utf-8")
      else:
        row_dict[key] = str(value)
    writer.writerow(row_dict)

  csv_data = file_handler.getvalue()
  csv_file = open(csv_filename, 'w')
  csv_file.write(csv_data)
  csv_file.close()


def exportOrgsForGoogleCode(csv_filename, gc_project_prefix=None,
                            scope_path=None, include_description=False):
  """Export all Organizations from given program as CSV.
      
  CSV file will contain 3 columns: organization name, organization google 
  code project name, organization description.
  
  Args:
    csv_filename: the name of the csv file to save
    gc_project_prefix: Google Code project prefix for example
      could be google-summer-of-code-2009- for GSoC 2009
    scope_path: the scope path of the roles to get could be
      google/gsoc2009 if you want to export all GSoC 2009 Organizations.
    include_description: if true, includes the orgs description in the export
  """
  from soc.modules.gsoc.models.organization import GSoCOrganization
  
  if not gc_project_prefix:
    gc_project_prefix = ''

  print 'Retrieving all Organizations'
  fields = {'scope_path': scope_path}
  orgs = getEntities(GSoCOrganization, fields=fields)()
  orgs_export = []
  
  print 'Preparing data for CSV export'
  for key in orgs.keys():
    org_for_export = {} 
    org_short_name = orgs[key].short_name
    org_short_name = org_short_name.replace(' ','-').replace('.', '')
    org_short_name = org_short_name.replace('/','-').replace('!','').lower()
    if include_description:
      org_for_export['org_description'] = orgs[key].description
    org_for_export['org_name'] = orgs[key].name
    org_for_export['google_code_project_name'] = gc_project_prefix + \
        org_short_name
    orgs_export.append(org_for_export)

  export_fields = ['org_name', 'google_code_project_name', 'org_description']
  print 'Exporting the data to CSV'
  saveDataToCSV(csv_filename, orgs_export, export_fields)
  print "Exported Organizations for Google Code to %s file." % csv_filename


def exportRolesForGoogleCode(csv_filename, gc_project_prefix='', 
                             scope_path=''):
  """Export all Students/Mentors/OrgAdmins Roles from given program as CSV.
      
  CSV file will contain 3 columns: google_account, organization google 
  code project name and role (project member or project owner).
  
  Args:
    csv_filename: the name of the csv file to save
    gc_project_prefix: Google Code project prefix for example
      could be google-summer-of-code-2009- for GSoC 2009
    scope_path: the scope path of the roles to get could be
      google/gsoc2009 if you want to export all GSoC 2009 Organizations.
  """
  from google.appengine.ext import db

  from soc.modules.gsoc.models.org_admin import GSoCOrgAdmin
  from soc.modules.gsoc.models.mentor import GSoCMentor
  from soc.modules.gsoc.models.profile import GSoCProfile
  from soc.modules.gsoc.models.project import GSoCProject
  from soc.modules.gsoc.models.student import GSoCStudent
  from soc.modules.gsoc.models.organization import GSoCOrganization
  from soc.modules.gsoc.models.student_project import StudentProject

  # get orgs
  fields = {'scope_path': scope_path}
  orgs = getEntities(GSoCOrganization, fields=fields)()

  org_admins_by_orgs = {}
  students_by_orgs = {}
  mentors_by_orgs = {}
  resolved_users = {}

  def get_new_users(keys):
    have = set(resolved_users.keys())
    want = set(keys).difference(have)
    if not want:
      return
    new_users = db.get(want)
    for i in new_users:
      resolved_users[i.key()] = i

  def resolve_profile_key_to_user(profile_key):
    return resolved_users[profile_key.parent()]

  def key(prop, item):
    return prop.get_value_for_datastore(item)

  def value(prop, item):
    return resolved_keys[key(prop, item)]

  def short_name(org):
    org_short_name = org.short_name
    org_short_name = org_short_name.replace(' ','-').replace('.', '')
    org_short_name = org_short_name.replace('/','-').replace('!','').lower()
    return org_short_name

  for org in orgs.values():
    # get all projects
    #TODO: fix that
    #fields = {'scope_path': org.key().id_or_name()}
    fields = {'org_admin_for': org.key()}
    #org_admins = getEntities(GSoCOrgAdmin, fields=fields)()
    org_admins = getEntities(GSoCProfile, fields=fields)()

    fields = {'org': org, 'status': 'accepted'}
    student_projects = getEntities(GSoCProject, fields=fields)()
    #fields = {'scope_path': org.key().id_or_name(), 'status': 'accepted'}
    #student_projects = getEntities(StudentProject, fields=fields)()

    org_short_name = short_name(org)

    if not gc_project_prefix.endswith('-'):
      gc_project_prefix += '-'

    project_key = gc_project_prefix + org_short_name

    org_admins_by_orgs[project_key] = []
    students_by_orgs[project_key] = []
    mentors_by_orgs[project_key] = []

    keys = []
    keys += [key(GSoCProfile.user, i) for i in org_admins.values()]
    keys += [i.parent_key().parent() for i in student_projects.values()]
    for project in student_projects.values():
      keys += [i.parent() for i in project.mentors]

    print keys
    get_new_users(keys)

    org_short_name = short_name(org)

    for org_admin in org_admins.values():
      account_name = str(resolve_profile_key_to_user(org_admin.key()).account)
      org_admins_by_orgs[project_key].append(account_name)
      print 'OrgAdmin %s for %s' % (account_name, project_key)
    
    #students = [value(StudentProject.student, i) for i in student_projects.values()]
    #mentors = [value(StudentProject.mentor, i) for i in student_projects.values()]

    #keys = []
    #keys += [key(GSoCStudent.user, i) for i in students]
    #keys += [key(GSoCMentor.user, i) for i in mentors]

    #get_new_keys(keys)

    #org_short_name = short_name(org)

    for project in student_projects.values():
      account_name = str(resolve_profile_key_to_user(
          project.parent_key()).account)
      students_by_orgs[project_key].append(account_name)
      print 'Student %s for %s' % (account_name, project_key)

      for mentor in project.mentors:
        account_name = str(resolve_profile_key_to_user(mentor).account)
        mentors_by_orgs[project_key].append(account_name)
        print 'Mentor %s for %s' % (account_name, project_key)
#      mentor_entity = value(StudentProject.mentor, student_project)
##      account_name = str(value(GSoCMentor.user, mentor_entity).account)
#      mentors_by_orgs[project_key].append(account_name)
#      print 'Mentor %s for %s' % (account_name, project_key)
    
  roles_data = {}

  # prepare org admins data
  for org_key in org_admins_by_orgs.keys():
    for org_admin in org_admins_by_orgs[org_key]:
      roles_data[org_admin + '|' + org_key] = {
          'role': 'project_owner',
          'google_code_project_name': org_key,
          'google_account': org_admin
          }

  # prepare mentors data
  for org_key in mentors_by_orgs.keys():
    for mentor in mentors_by_orgs[org_key]:
      if mentor + '|' + org_key not in roles_data.keys():
        roles_data[mentor + '|' + org_key] = {
            'role': 'project_member',
            'google_code_project_name': org_key,
            'google_account': mentor
            }

  # prepare students data
  for org_key in students_by_orgs.keys():
    for student in students_by_orgs[org_key]:
      roles_data[student + '|' + org_key] = {
          'role': 'project_member',
          'google_code_project_name': org_key,
          'google_account': student
          }
   
  data = []
  
  for roles_key in roles_data.keys():
    # add @gmail.com to all accounts that don't have @ in the account string
    # gmail.com is authorized domain for Google AppEngine that's why it's
    # missing
    if roles_data[roles_key]['google_account'].find('@') == -1:
      account = roles_data[roles_key]['google_account'] + '@gmail.com'
      roles_data[roles_key]['google_account'] = account
    data.append(roles_data[roles_key])
  
  export_fields = ['google_account', 'google_code_project_name', 'role']
  print 'Exporting the data to CSV'
  saveDataToCSV(csv_filename, data, export_fields)
  print "Exported Roles for Google Code to %s file." % csv_filename


def entityToDict(entity, field_names=None):
  """Returns a dict with all specified values of this entity.

  Args:
    entity: entity that will be converted to dictionary
    field_names: the fields that should be included, defaults to
      all fields that are of a type that is in DICT_TYPES.
  """
  from google.appengine.ext import db

  DICT_TYPES = (db.StringProperty, db.IntegerProperty)
  result = {}

  if not field_names:
    props = entity.properties().iteritems()
    field_names = [k for k, v in props if isinstance(v, DICT_TYPES)]

  for key in field_names:
    # Skip everything that is not valid
    if not hasattr(entity, key):
      continue

    result[key] = getattr(entity, key)

  if hasattr(entity, 'name'):
    name_prop = getattr(entity, 'name')
    if callable(name_prop):
      result['name'] = name_prop()

  return result


def surveyRecordCSVExport(csv_filename, survey_record_model, 
                          survey_model, survey_key):
  """CSV export for Survey Records for selected survey type and given survey key.
  
  Args:
    csv_filename: the name of the csv file to save
    survey_record_model: model of surver record that will be exported
    survey_model: model of the survey that wil be exported
    survey_key: key of the survey that records will be exported
  """

  from soc.modules.gsoc.models.project_survey import ProjectSurvey
  from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey

  # fetch survey
  survey = survey_model.get(survey_key)

  if not survey:
    print "Survey of given model and key doesn't exist."
    return

  schema = eval(survey.survey_content.schema)
  ordered_properties = survey.survey_content.orderedProperties()

  getSurveyRecords = getEntities(survey_record_model)
  survey_records = getSurveyRecords()
  survey_records_amount = len(survey_records)
  print "Fetched %d Survey Records." % survey_records_amount

  count = 0

  print "Preparing SurveyRecord data for export."

  sr_key = {}
  comments_properties = []
  for property_name in ordered_properties:
    sr_key[property_name] = schema[property_name]['question']
    if schema[property_name]['has_comment']:
      sr_key['comment_for_' + property_name] = 'None'
      comments_properties.append('comment_for_' + property_name)

  for comment in comments_properties:
    ordered_properties.append(comment)

  survey_record_data = []
  for i in survey_records.keys():
    if str(survey_records[i].survey.key()) != survey_key:
        continue
    data = entityToDict(survey_records[i], ordered_properties)

    if (survey_model == GradingProjectSurvey) or \
        (survey_model == ProjectSurvey):
      data['organization'] = survey_records[i].org.name
      data['project_title'] = survey_records[i].project.title
      data['user_link_id'] = survey_records[i].user.link_id

      if survey_model == GradingProjectSurvey:
        data['project_grade'] = survey_records[i].grade

    survey_record_data.append(data)

    count += 1
    print str(count) + '/' + str(survey_records_amount) + ' ' + str(i)

  if (survey_model == GradingProjectSurvey) or (survey_model == ProjectSurvey):
    ordered_properties.append('organization')
    ordered_properties.append('project_title')
    ordered_properties.append('user_link_id')
    sr_key['organization'] = 'None'
    sr_key['project_title'] = 'None'
    sr_key['user_link_id'] = 'None'

    if survey_model == GradingProjectSurvey:
      ordered_properties.append('project_grade')
      sr_key['project_grade'] = 'None'

  survey_record_data.insert(0, sr_key)

  saveDataToCSV(csv_filename, survey_record_data, ordered_properties)
  print "Survey Records exported to %s file." % csv_filename


def turnaroundTime(task):
  from soc.modules.gci.logic import task as task_logic
  from soc.modules.gci.models.comment import GCIComment

  q = GCIComment.all()
  q.ancestor(task)
  q.filter('modified_by', None)
  q.filter('title', task_logic.DEF_ASSIGNED_TITLE)
  comments = sorted(q, key=lambda x: x.created_on)
  started = comments[-1]

  q = GCIComment.all()
  q.ancestor(task)
  q.filter('modified_by', None)
  q.filter('title', task_logic.DEF_SEND_FOR_REVIEW_TITLE)
  comments = sorted(q, key=lambda x: x.created_on)
  finished = comments[-1]

  q = GCIComment.all()
  q.ancestor(task)
  q.filter('modified_by', None)
  q.filter('title', task_logic.DEF_CLOSED_TITLE)
  approved = q.get() # there can only be one

  implementation = finished.created_on - started.created_on
  turnaround = approved.created_on - finished.created_on
  url = "http://www.google-melange.com/gci/task/view/google/gci2011/%d"
  return (url % task.key().id(),
          str(started.created_on),
          str(finished.created_on),
          str(approved.created_on),
          str(implementation),
          str(turnaround),
          task.difficulty_level,
          finished.created_by.name,
          approved.created_by.name,
         )


class Request(object):
  def __init__(self, **kwargs):
    self.method = kwargs.get('method', "GET")
    self.path = kwargs.get('path', None)
    self.GET = kwargs.get('get', {})
    self.POST = kwargs.get('post', {})

class StudentKeyRequest(Request):
  def __init__(self, key):
    super(StudentKeyRequest, self).__init__(post=dict(student_key=key))


def main():
  """Main routine.
  """

  interactive.setup()
  interactive.setDjango()

  from google.appengine.api import users
  from google.appengine.ext import db

  from soc.models.user import User
  from soc.modules.gsoc.models.program import GSoCProgram
  from soc.modules.gsoc.models.organization import GSoCOrganization
  from soc.modules.gsoc.models.profile import GSoCProfile
  from soc.modules.gsoc.models.profile import GSoCStudentInfo
  from soc.modules.gsoc.models.proposal import GSoCProposal
  from soc.modules.gsoc.models.project import GSoCProject

  from soc.modules.gci.models.task import GCITask
  from soc.modules.gci.models.comment import GCIComment
  from soc.modules.gci.models.organization import GCIOrganization
  from soc.modules.gci.models.profile import GCIProfile
  from soc.modules.gci.models.program import GCIProgram
  from soc.modules.gci import tasks as gci_tasks

  def slotSaver(org, value):
    org.slots = value
  def popSaver(org, value):
    org.nr_applications = value
  def rawSaver(org, value):
    org.slots_calculated = value
  def getGSoC2012Profile(link_id):
    program = GSoCProgram.get_by_key_name('google/gsoc2012')
    return GSoCProfile.all().filter('scope', program).filter('link_id', link_id).get()
  def getGSoC2012Proposal(link_id, id):
    profile = getGSoC2012Profile(link_id)
    return GSoCProposal.get_by_id(id, profile)
  def getGSoC2012Project(link_id, id):
    profile = getGSoC2012Profile(link_id)
    return GSoCProject.get_by_id(id, profile)
  def withdrawProject(link_id, id):
    proposal = getGSoC2012Proposal(link_id, id)
    proposal_key = proposal.key()
    profile = proposal.parent()
    profile_key = profile.key()
    project = GSoCProject.all().ancestor(profile).get()
    project_key = project.key()

    def withdraw_project_txn():
      proposal = db.get(proposal_key)
      project = db.get(project_key)
      profile = db.get(profile_key)

      proposal.status = 'withdrawn'
      project.status = 'withdrawn'
      profile.number_of_projects = 0
      db.put([proposal, project, profile])

    db.run_in_transaction(withdraw_project_txn)

  context = {
      'load': loadPickle,
      'dump': dumpPickle,
      'users': users,
      'db': db,
      'orgStats': orgStats,
      'printPopularity': printPopularity,
      'saveValues': saveValues,
      'getEntities': getEntities,
      'deleteEntities': deleteEntities,
      'getOrgs': getEntities(GSoCOrganization),
      'getUsers': getEntities(User),
      'setOrganizationInSurveyRecords': setOrganizationInSurveyRecords,
      'convertProposals': convertProposals,
      'addFollower': addFollower,
      'p': getGSoC2012Profile,
      'o': getGSoC2012Proposal,
      'r': getGSoC2012Project,
      'withdrawProject': withdrawProject,
      'GSoCOrganization': GSoCOrganization,
      'User': User,
      'GSoCProgram': GSoCProgram,
      'GCIProgram': GCIProgram,
      'GSoCProfile': GSoCProfile,
      'GCIProfile': GCIProfile,
      'GCITask': GCITask,
      'Request': Request,
      'SRequest': StudentKeyRequest,
      'GCIComment': GCIComment,
      'GCIOrganization': GCIOrganization,
      'GSoCStudentInfo': GSoCStudentInfo,
      'GSoCProposal': GSoCProposal,
      'GSoCProject': GSoCProject,
      'gci_tasks': gci_tasks,
      'slotSaver': slotSaver,
      'popSaver': popSaver,
      'rawSaver': rawSaver,
      'exportOrgsForGoogleCode': exportOrgsForGoogleCode,
      'exportRolesForGoogleCode': exportRolesForGoogleCode,
      'surveyRecordCSVExport': surveyRecordCSVExport,
      'turnaroundTime': turnaroundTime,
  }

  interactive.remote(sys.argv[1:], context)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Usage: %s app_id [host]" % (sys.argv[0],)
    sys.exit(1)

  main()
