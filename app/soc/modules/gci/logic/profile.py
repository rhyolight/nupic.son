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

"""GCI logic for profiles.
"""


import datetime

from soc.logic import user as user_logic
from soc.tasks import mailer

from soc.modules.gsoc.models import profile as gsoc_profile_model

from soc.modules.gci.logic.helper import notifications
from soc.modules.gci.models import comment as comment_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import task as task_model


MELANGE_DELETED_USER_PNAME = 'Melange Deleted User'

MELANGE_DELETED_USER_GNAME = 'Melange Deleted User GName'

MELANGE_DELETED_USER_SNAME = 'Melange Deleted User Surname'

MELANGE_DELETED_USER_EMAIL = 'melange_deleted_user@gmail.com'

MELANGE_DELETED_USER_RES_STREET = 'No address'

MELANGE_DELETED_USER_RES_CITY = 'No city'

MELANGE_DELETED_USER_RES_COUNTY = 'United States'

MELANGE_DELETED_USER_RES_POSTAL_CODE = '00000'

MELANGE_DELETED_USER_PHONE = '0000000000'

MELANGE_DELETED_USER_BIRTH_DATE = datetime.datetime(1, 1, 1)


def hasStudentFormsUploaded(student):
  """Whether the specified student has uploaded their forms.
  """
  return student.consent_form and student.student_id_form


def queryAllMentorsForOrg(org, keys_only=False, limit=1000):
  """Returns a list of keys of all the mentors for the organization

  Args:
    org: the organization entity for which we need to get all the mentors
    keys_only: True if only the entity keys must be fetched instead of the
        entities themselves.
    limit: the maximum number of entities that must be fetched

  returns:
    List of all the mentors for the organization
  """

  # get all mentors keys first
  query = profile_model.GCIProfile.all(keys_only=keys_only)
  query.filter('mentor_for', org)
  mentors = query.fetch(limit=limit)

  return mentors


def queryAllMentorsKeysForOrg(org, limit=1000):
  """Returns a list of keys of all the mentors for the organization

  Args:
    org: the organization entity for which we need to get all the mentors
    limit: the maximum number of entities that must be fetched

  returns:
    List of all the mentors for the organization
  """
  return queryAllMentorsForOrg(org, keys_only=True, limit=limit)


def sendFirstTaskConfirmationTxn(profile, task):
  """Returns a transaction which sends a confirmation email to a student who
  completes their first task.
  """

  if not profile.student_info:
    raise ValueError('Only students can be queried for closed tasks.')
  
  context = notifications.getFirstTaskConfirmationContext(profile)
  return mailer.getSpawnMailTaskTxn(context, parent=task)


def orgAdminsForOrg(org, limit=1000):
  """Returns the organization administrators for the given GCI Organization.

  Args:
    org: The GCIOrganization entity for which the admins should be found.
  """
  query = profile_model.GCIProfile.all()
  query.filter('org_admin_for', org)

  return query.fetch(limit)


def queryProfileForUserAndProgram(user, program):
  """Returns the query to fetch GCIProfile entity for the specified user
  and program.

  Args:
    user: User entity for which the profile should be found
    program: GCIProgram entity for which the profile should be found
  """
  return profile_model.GCIProfile.all().ancestor(user).filter('scope = ', program)


def queryStudentInfoForParent(parent):
  """Returns the query to fetch GCIStudentInfo entity for the specified
  parent.

  Args:
    parent: GCIProfile entity which is the parent of the entity to retrieve
  """
  return profile_model.GCIStudentInfo.all().ancestor(parent)


def getOrCreateDummyMelangeDeletedProfile(program):
  """Fetches or creates the dummy melange deleted profile for the given program.

  Args:
    program: The program entity for which the dummy profile should be fetched
        or created.
  """
  q = profile_model.GCIProfile.all()
  q.filter('link_id', user_logic.MELANGE_DELETED_USER)
  q.filter('scope', program)
  profile_ent = q.get()

  # If the requested user does not exist, create one.
  if not profile_ent:
    user_ent = user_logic.getOrCreateDummyMelangeDeletedUser()
    key_name = '%s/%s' % (program.key(), user_logic.MELANGE_DELETED_USER)

    profile_ent = profile_model.GCIProfile(
        parent=user_ent, key_name=key_name,
        link_id=user_logic.MELANGE_DELETED_USER, scope=program,
        scope_path=program.key().id_or_name(), user=user_ent,
        public_name=MELANGE_DELETED_USER_PNAME,
        given_name=MELANGE_DELETED_USER_GNAME,
        surname=MELANGE_DELETED_USER_SNAME,
        email=MELANGE_DELETED_USER_EMAIL,
        res_street=MELANGE_DELETED_USER_RES_STREET,
        res_city=MELANGE_DELETED_USER_RES_CITY,
        res_country=MELANGE_DELETED_USER_RES_COUNTY,
        res_postalcode=MELANGE_DELETED_USER_RES_POSTAL_CODE,
        phone=MELANGE_DELETED_USER_PHONE,
        birth_date=MELANGE_DELETED_USER_BIRTH_DATE)

    profile_ent.put()

  return profile_ent
