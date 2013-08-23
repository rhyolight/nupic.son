# Copyright 2013 the Melange authors.
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

"""Tests for profile logic."""

import unittest

from melange.logic import profile as profile_logic

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class GetOrgAdminsTest(unittest.TestCase):
  """Unit tests for getOrgAdmins function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(program_model.Program)

    # seed a couple of organizations
    self.organization_one = seeder_logic.seed(org_model.Organization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(org_model.Organization,
        {'program': self.program})

  def testNoOrgAdmin(self):
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(org_admins, [])

  def testOneOrgAdmin(self):
    # seed a new org admin for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    org_admin = seeder_logic.seed(profile_model.Profile, org_admin_properties)

    # the org admin should be returned
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(len(org_admins), 1)
    self.assertEqual(org_admins[0].key(), org_admin.key())

    # keys_only set to True should return only the key
    org_admins_keys = profile_logic.getOrgAdmins(
        self.organization_one.key(), keys_only=True)
    self.assertEqual(len(org_admins_keys), 1)
    self.assertEqual(org_admins_keys[0], org_admin.key())

    # there is still no org admin for organization two
    org_admins = profile_logic.getOrgAdmins(self.organization_two.key())
    self.assertEqual(org_admins, [])

  def testManyOrgAdmins(self):
    # seed  org admins for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    seeded_org_admins = set()
    for _ in range(5):
      seeded_org_admins.add(seeder_logic.seed(
        profile_model.Profile, org_admin_properties).key())

    # all org admins should be returned
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(len(org_admins), 5)
    self.assertEqual(seeded_org_admins,
        set([org_admin.key() for org_admin in org_admins]))

    # all org admins keys should be returned if keys_only set
    org_admins_keys = profile_logic.getOrgAdmins(
        self.organization_one.key(), keys_only=True)
    self.assertEqual(len(org_admins_keys), 5)
    self.assertEqual(seeded_org_admins, set(org_admins_keys))

  def testNotActiveOrgAdmin(self):
    # seed invalid org admins for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'invalid',
    }
    seeder_logic.seed(
        profile_model.Profile, org_admin_properties)

    # not active org admin not returned
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(org_admins, [])

    # keys_only set to True does not return any keys
    org_admins_keys = profile_logic.getOrgAdmins(
        self.organization_one.key(), keys_only=True)
    self.assertEqual(org_admins_keys, [])

  def testExtraAttrs(self):
    # seed male org admin for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
        'gender': 'male',
      }
    org_admin = seeder_logic.seed(
        profile_model.Profile, org_admin_properties)

    # seed female org admin for organization one
    org_admin_properties['gender'] = 'female'
    seeder_logic.seed(
        profile_model.Profile, org_admin_properties)

    # retrieve only org admins with extra attrs
    extra_attrs = {profile_model.Profile.gender: 'male'}
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key(),
        extra_attrs=extra_attrs)

    # only the male org admin should be returned
    self.assertEqual(1, len(org_admins))
    self.assertEqual(org_admins[0].key(), org_admin.key())
