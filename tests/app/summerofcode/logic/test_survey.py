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

"""Unit tests for survey logic."""

import unittest

from google.appengine.ext import ndb
from datetime import timedelta

from soc.models import profile as profile_model
from soc.models import survey as soc_survey_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic
from summerofcode.logic import survey as survey_logic
from summerofcode.models import survey as survey_model

from tests import timeline_utils


class GetPersonalExtensionTest(unittest.TestCase):
  """Unit tests for getPersonalExtension function."""

  def setUp(self):
    self.survey = seeder_logic.seed(soc_survey_model.Survey)
    self.profile = seeder_logic.seed(profile_model.Profile)

  def testPersonalExtensionExists(self):
    """Tests that if a personal extension exists, it will be returned."""
    # create personal extension
    # TODO(daniel): NDB migration
    ndb_profile_key = ndb.Key.from_old_key(self.profile.key())
    ndb_survey_key = ndb.Key.from_old_key(self.survey.key())

    extension = survey_model.PersonalExtension(
        parent=ndb_profile_key, survey=ndb_survey_key)
    extension.put()

    # try getting the extension
    result = survey_logic.getPersonalExtension(
        self.profile.key(), self.survey.key())

    # the extension should be returned
    self.assertEqual(extension.key, result.key)

  def testPersonalExtensionDoesNotExist(self):
    """Tests that if a personal extensions does not exist, None is returned."""
    # try getting the extension
    result = survey_logic.getPersonalExtension(
        self.profile.key(), self.survey.key())

    # no extension should be returned
    self.assertIsNone(result)

  def testPersonalExtensionForAnotherSurvey(self):
    """Tests for no result even if extension exists for another survey."""
    # TODO(daniel): NDB migration
    ndb_profile_key = ndb.Key.from_old_key(self.profile.key())

    # create an extension but for another survey
    other_survey = seeder_logic.seed(soc_survey_model.Survey)
    # TODO(daniel): NDB migration
    ndb_other_survey_key = ndb.Key.from_old_key(other_survey.key())
    extension = survey_model.PersonalExtension(
        parent=ndb_profile_key, survey=ndb_other_survey_key)
    extension.put()

    # try getting the extension for the main survey
    result = survey_logic.getPersonalExtension(
        self.profile.key(), self.survey.key())

    # no extension should be returned
    self.assertIsNone(result)

  def testPersonalExtensionForAnotherProfile(self):
    """Tests for no result even if extension exists for another profile."""
    # TODO(daniel): NDB migration
    ndb_survey_key = ndb.Key.from_old_key(self.survey.key())

    # create an extension but for another profile
    other_profile = seeder_logic.seed(profile_model.Profile)
    # TODO(daniel): NDB migration
    ndb_other_profile_key = ndb.Key.from_old_key(other_profile.key())
    extension = survey_model.PersonalExtension(
        parent=ndb_other_profile_key, survey=ndb_survey_key)
    extension.put()

    # try getting the extension for the main profile
    result = survey_logic.getPersonalExtension(
        self.profile.key(), self.survey.key())

    # no extension should be returned
    self.assertIsNone(result)


class PeriodStateTest(unittest.TestCase):
  """Unit tests for Period class."""

  def testForUnboundPeriod(self):
    """Tests state for unbound period."""
    period = survey_logic.Period()
    self.assertEqual(period.state, survey_logic.IN_PERIOD_STATE)

  def testForLeftUnboundPeriod(self):
    """Tests state for periods with no start date."""
    # set the end of period to the past so the period is already over
    period = survey_logic.Period(end=timeline_utils.past())
    self.assertEqual(period.state, survey_logic.POST_PERIOD_STATE)

    # set the end of period to the future so we are currently in
    period = survey_logic.Period(end=timeline_utils.future())
    self.assertEqual(period.state, survey_logic.IN_PERIOD_STATE)

  def testForRightUnboundPeriod(self):
    """Tests state for periods with no end date."""
    # set the start of period to the past so that we are currently in
    period = survey_logic.Period(start=timeline_utils.past())
    self.assertEqual(period.state, survey_logic.IN_PERIOD_STATE)

    # set the start of period to the future so that is has yet to start
    period = survey_logic.Period(start=timeline_utils.future())
    self.assertEqual(period.state, survey_logic.PRE_PERIOD_STATE)

  def testForBoundPeriod(self):
    """Tests state for periods with both start and end dates."""
    # set the start and end dates to the past so it is after the period
    period = survey_logic.Period(start=timeline_utils.past(),
        end=timeline_utils.past())
    self.assertEqual(period.state, survey_logic.POST_PERIOD_STATE)

    # set the start date to the past and the end date to the future
    # so it is in the period
    period = survey_logic.Period(
        start=timeline_utils.past(), end=timeline_utils.future())
    self.assertEqual(period.state, survey_logic.IN_PERIOD_STATE)

    # set the start and end dates to the past so it is before the period
    period = survey_logic.Period(
        start=timeline_utils.future(), end=timeline_utils.future())
    self.assertEqual(period.state, survey_logic.PRE_PERIOD_STATE)


class GetSurveyActivePeriodTest(unittest.TestCase):
  """Unit tests for getSurveyActivePeriod function."""

  def setUp(self):
    self.survey = seeder_logic.seed(soc_survey_model.Survey)
    self.extension = survey_model.PersonalExtension()

  def testForNoExtension(self):
    """Tests active period if there is no extension."""
    # test for survey with both start and end dates
    self.survey.survey_start = timeline_utils.past()
    self.survey.survey_end = timeline_utils.future()
    period = survey_logic.getSurveyActivePeriod(self.survey)
    self.assertEquals(period.start, self.survey.survey_start)
    self.assertEquals(period.end, self.survey.survey_end)

  def testForExtensionWithStartAndEndDate(self):
    """Tests active period if there is an extension with start and end date."""
    self.survey.survey_start = timeline_utils.past(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=100)

    # test for an extension that is within the survey period
    self.extension.start_date = self.survey.survey_start + timedelta(1)
    self.extension.end_date = self.survey.survey_end - timedelta(1)

    # active period should be the same as for the survey
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.survey.survey_start)
    self.assertEquals(period.end, self.survey.survey_end)

    # test for an extension which is a superset of the survey
    self.extension.start_date = self.survey.survey_start - timedelta(1)
    self.extension.end_date = self.survey.survey_end + timedelta(1)

    # active period should be the same as for the extension
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.extension.start_date)
    self.assertEquals(period.end, self.extension.end_date)

    # test for an extension which starts earlier than the survey and ends
    # before the survey ends
    self.extension.start_date = self.survey.survey_start - timedelta(1)
    self.extension.end_date = self.survey.survey_end - timedelta(1)

    # active period should start as extension starts and ends as survey ends
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.extension.start_date)
    self.assertEquals(period.end, self.survey.survey_end)

    # test for an extension which starts after than the survey and ends
    # before the survey ends
    self.extension.start_date = self.survey.survey_start + timedelta(1)
    self.extension.end_date = self.survey.survey_end + timedelta(1)

    # active period should start when survey starts and end when extension ends
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.survey.survey_start)
    self.assertEquals(period.end, self.extension.end_date)

    # test for an extension that does not overlap with the survey dates
    self.extension.start_date = self.survey.survey_start - timedelta(10)
    self.extension.end_date = self.survey.survey_start - timedelta(5)

    # active period should span between extension start and survey end
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.extension.start_date)
    self.assertEquals(period.end, self.survey.survey_end)

  def testForExtensionWithStartDate(self):
    """Tests active period for extensions that have only start date."""
    self.survey.survey_start = timeline_utils.past(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=100)

    # test for an extension that starts before survey starts
    self.extension.start_date = self.survey.survey_start - timedelta(1)

    # active period should span between extension start and survey end
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.extension.start_date)
    self.assertEquals(period.end, self.survey.survey_end)

    # test for an extension that starts after survey starts
    self.extension.start_date = self.survey.survey_start + timedelta(1)

    # active period should be the same as for the survey
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.survey.survey_start)
    self.assertEquals(period.end, self.survey.survey_end)

  def testForExtensionWithEndDate(self):
    """Tests active period for extensions that have only start date."""
    self.survey.survey_start = timeline_utils.past(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=100)

    # test for an extension that ends before survey ends
    self.extension.end_date = self.survey.survey_end - timedelta(1)

    # active period should be the same as for the survey
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.survey.survey_start)
    self.assertEquals(period.end, self.survey.survey_end)

    # test for an extension that starts after survey ends
    self.extension.end_date = self.survey.survey_end + timedelta(1)

    # active period should end when the extension ends
    period = survey_logic.getSurveyActivePeriod(self.survey, self.extension)
    self.assertEquals(period.start, self.survey.survey_start)
    self.assertEquals(period.end, self.extension.end_date)


class CreateOrUpdatePersonalExtensionTest(unittest.TestCase):
  """Unit tests for createOrUpdatePersonalExtension function."""

  def setUp(self):
    self.survey = seeder_logic.seed(soc_survey_model.Survey)
    # TODO(daniel): NDB migration; no key translation after Survey migrates
    self.survey_key = ndb.Key.from_old_key(self.survey.key())
    self.profile = seeder_logic.seed(profile_model.Profile)
    # TODO(daniel): NDB migration; no key translation after Profile migrates
    self.profile_key = ndb.Key.from_old_key(self.profile.key())

  def testExtensionDoesNotExist(self):
    """Tests that extension is created when it does not exist."""
    extension = survey_logic.createOrUpdatePersonalExtension(
        self.profile.key(), self.survey.key())
    self.assertIsNotNone(extension)
    self.assertEqual(extension.key.parent(), self.profile_key)
    self.assertEqual(extension.survey, self.survey_key)

  def testExtensionAreadyExists(self):
    """Tests that another extension is not created if one exists."""
    extension = survey_model.PersonalExtension(
        parent=self.profile_key, survey=self.survey_key)
    extension.put()

    result = survey_logic.createOrUpdatePersonalExtension(
        self.profile.key(), self.survey.key())

    # check that result and extension are the same entity
    self.assertEqual(extension.key, result.key)

  def testExtensionIsUpdated(self):
    """Tests that extension can be updated."""
    extension = survey_model.PersonalExtension(
        parent=self.profile_key, survey=self.survey_key)
    extension.put()

    # set new dates
    start_date = timeline_utils.past()
    end_date = timeline_utils.future()
    result = survey_logic.createOrUpdatePersonalExtension(
        self.profile.key(), self.survey.key(),
        start_date=start_date, end_date=end_date)

    # check that the dates are updated
    self.assertEqual(result.start_date, start_date)
    self.assertEqual(result.end_date, end_date)

    # try cleaning the dates
    result = survey_logic.createOrUpdatePersonalExtension(
        self.profile.key(), self.survey.key(),
        start_date=None, end_date=None)

    # check that the dates are cleared
    self.assertIsNone(result.start_date)
    self.assertIsNone(result.end_date)


class IsSurveyActiveTest(unittest.TestCase):
  """Unit tests for isSurveyActive function."""

  def setUp(self):
    self.survey = seeder_logic.seed(soc_survey_model.Survey)
    # TODO(daniel): NDB migration; no key translation after Survey migrates
    self.survey_key = ndb.Key.from_old_key(self.survey.key())
    self.profile = seeder_logic.seed(profile_model.Profile)
    self.profile_key =  ndb.Key.from_old_key(self.profile.key())

  def testSurveyIsActive(self):
    """Tests for survey that is active."""
    self.survey.survey_start = timeline_utils.past(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=100)

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertTrue(result)

  def testSurveyIsNotActive(self):
    """Tests for survey that is not active."""
    # check for survey that has ended
    self.survey.survey_start = timeline_utils.past(delta=200)
    self.survey.survey_end = timeline_utils.past(delta=100)

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertFalse(result)

    # check for survey that has yet to start
    self.survey.survey_start = timeline_utils.future(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=200)

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertFalse(result)

  def testSurveyActiveWithExtension(self):
    """Tests for survey that has personal extension for the profile."""
    # survey has ended
    self.survey.survey_start = timeline_utils.past(delta=200)
    self.survey.survey_end = timeline_utils.past(delta=100)

    # seed an extension
    self.extension = survey_model.PersonalExtension(
        parent=self.profile_key, survey=self.survey_key)
    self.extension.end_date = timeline_utils.future()
    self.extension.put()

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertTrue(result)

    # survey has not started
    self.survey.survey_start = timeline_utils.future(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=200)

    # set the extension so that the survey can be accessed now
    self.extension.end_date = None
    self.extension.start_date = timeline_utils.past()

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertTrue(result)

  def testSurveyNotActiveWithExtension(self):
    """Tests that the survey is not active even with extension."""
    # survey has ended
    self.survey.survey_start = timeline_utils.past(delta=200)
    self.survey.survey_end = timeline_utils.past(delta=100)

    # seed an extension that also has ended
    self.extension = survey_model.PersonalExtension(
        parent=self.profile_key, survey=self.survey_key)
    self.extension.end_date = timeline_utils.past()
    self.extension.put()

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertFalse(result)

    # survey has not started, neither the extension
    self.survey.survey_start = timeline_utils.future(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=200)

    self.extension.end_date = None
    self.extension.start_date = timeline_utils.future()

    result = survey_logic.isSurveyActive(self.survey, self.profile.key())
    self.assertFalse(result)


class HasSurveyStartedTest(unittest.TestCase):
  """Unit tests for hasSurveyStarted function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.survey = seeder_logic.seed(soc_survey_model.Survey)
    # TODO(daniel): NDB migration; no key translation after Survey migrates
    self.survey_key = ndb.Key.from_old_key(self.survey.key())
    self.profile = seeder_logic.seed(profile_model.Profile)
    self.profile_key =  ndb.Key.from_old_key(self.profile.key())

  def testSurveyHasStarted(self):
    """Tests for survey that has already started."""
    # survey is in active state
    self.survey.survey_start = timeline_utils.past(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=100)

    result = survey_logic.hasSurveyStarted(self.survey, self.profile.key())
    self.assertTrue(result)

    # survey has already ended
    self.survey.survey_start = timeline_utils.past(delta=200)
    self.survey.survey_end = timeline_utils.past(delta=100)

    result = survey_logic.hasSurveyStarted(self.survey, self.profile.key())
    self.assertTrue(result)

  def testSurveyHasNotStarted(self):
    """Tests for survey that has not started yet."""
    # survey has not started yet
    self.survey.survey_start = timeline_utils.future(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=200)

    result = survey_logic.hasSurveyStarted(self.survey, self.profile.key())
    self.assertFalse(result)

  def testSurveyHasStartedWithExtension(self):
    """Tests for survey that has started only with an extension."""
    # survey has not started yet
    self.survey.survey_start = timeline_utils.future(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=200)

    # seed an extension
    self.extension = survey_model.PersonalExtension(
        parent=self.profile_key, survey=self.survey_key)
    self.extension.start_date = timeline_utils.past()
    self.extension.put()

    result = survey_logic.hasSurveyStarted(self.survey, self.profile.key())
    self.assertTrue(result)

  def testSurveyHasNotStartedWithExtension(self):
    """Tests for survey that has not started even with an extension."""
    # survey has not started yet
    self.survey.survey_start = timeline_utils.future(delta=100)
    self.survey.survey_end = timeline_utils.future(delta=200)

    # seed an extension
    self.extension = survey_model.PersonalExtension(
        parent=self.profile_key, survey=self.survey_key)
    self.extension.start_date = timeline_utils.future(delta=50)
    self.extension.put()

    result = survey_logic.hasSurveyStarted(self.survey, self.profile.key())
    self.assertFalse(result)
