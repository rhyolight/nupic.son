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

"""Base module for writing functional test scripts."""

import glob
import os
import random
import shutil
import signal
import string
import subprocess
import sys
import tempfile
import time
import unittest

from selenium import webdriver
from selenium.common import exceptions

from google.appengine.ext.remote_api import remote_api_stub

from soc.models import seed_db

from tests import profile_utils
from tests import program_utils


# TODO(nathaniel): Eliminate sleep calls.
class FunctionalTestCase(unittest.TestCase):  
  """Base class for all the Melange Functional Tests.

  Contains actions which will be used in writing Test scripts.
  """

  def init(self):
    """This is the function to be called at the beginning of every test."""    
    # Test case will send a list of dictionaries to this variable.
    self.properties = []
    # This variable will store the unique id of an element on a page.
    self.obj_id = {}
    # If there is a value that needs to be written to the text field, it will go here.
    self.obj_val = {}    
  
    # Select a random port to start a dev server.
    # Random ports and a seperate datastore file is for running of tests in multiple processes.
    self.port = random.randrange(50000, 60000, 2)
    # Start the dev server as a process running in background.

    # TODO(nathaniel): Reflow these few lines.
    self.server_process = subprocess.Popen(('nohup thirdparty/google_appengine/dev_appserver.py\
               --clear_datastore --datastore_path=%s --port=%s build >/dev/null 2>&1&' 
               %(tempfile.mktemp(), self.port)), stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True, preexec_fn=os.setsid)    
    if not self.server_process:
      self.fail("Server cannot be started: %s" % self.server_process)    
    self.setupLocalRemote()
    
  def createGSoCProgram(self):	  
    """Create GSoC Program."""
    self.program_helper = program_utils.GSoCProgramHelper()
    self.gsoc = self.program_helper.createProgram(override={'name':'Google Summer of Code',
      'short_name':'gsoc'})
    self.program = self.gsoc.key().name()
    self.org = self.program_helper.createOrg()
    self.org_app = self.program_helper.createOrgApp()
    self.user = profile_utils.seedGSoCProfile(self.gsoc)
    self.sponsor = program_utils.seedSponsor(sponsor_id='google')
    self.site = program_utils.seedSite(latest_gsoc=self.sponsor.key().name() + '/' + self.program, active_program=self.gsoc)

  def createGCIProgram(self):
    """Create GCI Program."""  
    self.program_helper = program_utils.GCIProgramHelper()
    self.gci = self.program = self.program_helper.createProgram(override={'name':'Google Code In',
      'short_name':'gci'})
    self.program = self.gci.key().name()
    self.org = self.program_helper.createOrg()
    self.org_app = self.program_helper.createOrgApp()
    self.user = profile_utils.seedGCIProfile(self.gci)
    self.sponsor = program_utils.seedSponsor(sponsor_id='google')
    self.site = program_utils.seedSite(latest_gci=self.sponsor.key().name() + '/' + self.program, active_program=self.gci)

  def openUrl(self, program):
    """Open the url specified in the test case.

    Args:
      program: Specify which program gsoc/gci.
    """	
    if program == "gsoc":
      self.url = self.obj_id["Url"] + self.gsoc.key().name()
    else:
      self.url = self.obj_id["Url"] + self.gci.key().name()
    time.sleep(2)
    # Start the firefox.
    self.Browser = webdriver.Firefox(timeout=20)
    # Go to the url specified by self.url variable.  
    self.Browser.get(self.url)
    
  def setupLocalRemote(self):
    """It connects with the remote/dev server."""
    time.sleep(2)
    remote_api_stub.ConfigureRemoteApi('dev~local-devel', '/_ah/remote_api', lambda: ('test@example.com', '') , "localhost:%d" % self.port)

  def loadProperties(self):
    """Load data from test cases."""
    for i in range(len(self.properties)):
      self.obj_id[self.properties[i]["Object"]] = self.properties[i]["Identification"]
      self.obj_val[self.properties[i]["Object"]] = self.properties[i]["Value"]

  # TODO(nathaniel): Drop this method.
  def wait(self, sec):
    """Delay the execution of script for specified number of seconds.

    Args:
      sec: Number of seconds for which the script should wait.
    """
    time.sleep(sec)

  def writeTextField(self, element=None):
    """Write text field in a form.

    Args:
      element: Particular text field which will be written.
    """
    web_element=self.obj_id[element]
    value=self.obj_val[element]
    if web_element.startswith("//"):
      self.Browser.find_element_by_xpath(web_element).send_keys(value)
    else:
      self.Browser.find_element_by_id(web_element).send_keys(value)
    
  def toggleCheckBox(self, chk_box=None):
    """Toggle a check box.

    Args:
      chk_box: particular check box which will be selected/not selected.
    """
    web_element=self.obj_id[chk_box]
    if web_element.startswith("//"):
      self.Browser.find_element_by_xpath(web_element).click()
    else:
      self.Browser.find_element_by_id(web_element).click()

  def setDropDownList(self, select_opt=None):
    """Selects one option from the drop down list.

    Args:
      select_opt: The option which should be selected from the drop down list.       
    """
    web_element=self.obj_id[select_opt]
    time.sleep(2)
    if web_element.startswith("//"):
      selection = self.Browser.find_element_by_xpath(web_element)
    else:
      selection = self.Browser.find_element_by_id(web_element)    
    all_options = selection.find_elements_by_tag_name("option")
    for option in all_options:
      if option.get_attribute("value") == self.obj_val[select_opt]:
        option.click()
        return
    else:
      self.fail("Could not find the option")
    
  def waitAndEnterText(self, sec, element=None):
    """Wait and enter text in a particular field.

    Args:
      sec: Number of seconds script should wait.
      element: The field in which we we want to enter some text.      
    """
    web_element=self.obj_id[element]
    value=self.obj_val[element]
    time.sleep(sec)
    if web_element.startswith("//"):
      self.Browser.find_element_by_xpath(web_element).send_keys(value)
    else:
      self.Browser.find_element_by_id(web_element).send_keys(value)   

  def clearFieldAssertMessageEnterData(self, error_element=None, element=None):
    """Assert the error message , clear the input field and enter a new value.

    Args:
      error_element: It is the element which is showing error message.
      element: The correct value for the input field.                 
    """
    self.assertTextIn(error_element)
    self.clearField(element)
    self.writeTextField(element)
 
  def clearField(self, clear_element=None):
    """Wait and clear a particular field.

    Args:
      clear_element: The field which we want to clear.
    """
    web_element=self.obj_id[clear_element]
    if web_element.startswith("//"):
      self.Browser.find_element_by_xpath(web_element).clear()
    else:
      self.Browser.find_element_by_id(web_element).clear()
 
  def clickOn(self, click_element=None):
    """Click on the specified element.

    Args:
      click_element: The element which will be clicked.
    """
    web_element=self.obj_id[click_element]
    if web_element.startswith("//"):
      self.Browser.find_element_by_xpath(web_element).click()
    else:
      self.Browser.find_element_by_id(web_element).click()

  # TODO(nathaniel): Kill this in favor of assertIn.
  def assertTextInElement(self, text_in=None, text_element=None):
    """Checks if particular text is present in message.

    Args:
      text_in: The text message part that will be checked.
      text_element: Text element which will be checked.
      Returns True if concerned text is present.
    """ 
    if text_in in text_element:
      return True
    else:
      msg = "Element %s has no text %s" % (text_element, text_in)
      raise AssertionError(msg)


  def assertLink(self, link_text=None):
    """Assert if a link is there.

    Args:
      link_text: The link which will be tested.  
    """
    try:
      self.Browser.find_element_by_link_text(link_text)      
    except exceptions.NoSuchElementException:
      msg = "The text %s is not part of a Link" % link_text
      raise AssertionError(msg)

  def assertText(self, text_element=None):
    """Assert a particular text.

    Args:
      text_element: The text which will be checked. 
    """
    web_element=self.obj_id[text_element]
    if web_element.startswith("//"):
      txt = self.Browser.find_element_by_xpath(web_element).text
    else:
      txt = self.Browser.find_element_by_id(web_element).text
    text_value = self.obj_val[text_element]
    if txt is None:
        msg = "Element %s has no text %s " % (text_element, txt)
        raise AssertionError(msg)
    if txt != self.obj_val[text_element]:
        msg = "Element text should be %s. It is %s."% (text_value, txt)
        raise AssertionError(msg)

  def assertMessageAndEnterText(self, error_element=None, input_field=None):
    """Assert a message and enter value in the text field.

    Args:
      error_element : error message from the application which will be checked.
      input_field : input box in which a value will be entered.
    """
    self.assertText(error_element)
    self.writeTextField(input_field)

  def assertTextIn(self, text_element):
    """check for the contents present in a text message.

    Args:
      text_element : the message content which will be checked with the
                     message from the application.      
    """
    text_object = self.obj_id[text_element]
    text_value = self.obj_val[text_element]
    text_msg = self.Browser.find_element_by_xpath(text_object).text
    if text_msg is None:
        msg = "Element %s has no text %s " % (text_element, text_msg)
        raise AssertionError(msg)
    if text_msg not in text_value:
        msg = "Element text should be %s. It is %s." % (text_value, text_msg)
        raise AssertionError(msg)
    if text_msg in self.obj_val[text_element]:
      return True

  def isElementDisplayed(self, sec, element_displayed=None):
    """ Wait and check if a particular element is displayed.

    Args:
      sec: Number of seconds script should wait.
      element_displayed: A particular element which we want to check if it is 
      displayed.Return True if it is present else return false. if it is not 
      displayed just pass and continue the execution.
    """   
    time.sleep(sec)
    display_element = self.obj_id[element_displayed]
    try:
      if self.Browser.find_element_by_xpath(display_element).is_displayed():
        return True        
    except exceptions.NoSuchElementException:
      msg = "The element %s is not displayed" % display_element
      raise AssertionError(msg)

  # TODO(syed): If it is not used in tests, drop it.
  def fillRandomValue(self, element=None):
    """It takes a value , add random string at the end and fill it in the form.

    Args:
      element: The element whose value will be changed by adding a random string 
               at the end.
    """
    range_number=5
    val = self.obj_val[element] + ''.join(random.choice(string.ascii_lowercase\
                                             + string.digits) for x in range(range_number))
    time.sleep(1)
    self.clearField(element)
    self.Browser.find_element_by_xpath(self.obj_id[element]).send_keys(val)

  def waitAndClick(self, sec, click_element):
    """wait and click on a particular element.

    Args:
      sec: Number of seconds script should wait.
      click_element: The element which we want to click.
    """    
    time.sleep(sec)
    web_element=self.obj_id[click_element]
    if web_element.startswith("//"):
      self.Browser.find_element_by_xpath(web_element).click()
    else:
      self.Browser.find_element_by_id(web_element).click()

  def checkRegistrationSuccess(self, flash_message):
    """Check Message from the melange if student data is saved successfully.

    Args:
      flash_message: This is the web element which gets displayed and show
                     message if data is saved successfully.
    """
    if self.isElementDisplayed(5, flash_message) is True:
      text = self.Browser.find_element_by_xpath(self.obj_id[flash_message]).text
      if text == self.obj_val[flash_message]:  
        raise AssertionError(text)
    
  def takeScreenshot(self):
    """Take screenshot."""
    # If there is a results directory then store snapshots there or create a new one.
    results_directory = "./tests/functional/results"
    random_string= ''.join(random.sample(string.letters*5,5))
    name_of_screenshot = random_string + ".png"
    screenshot = results_directory + "/" + name_of_screenshot
    if os.path.isdir(results_directory):
      self.Browser.save_screenshot(screenshot)
    else:
      os.makedirs(results_directory)
      self.Browser.save_screenshot(screenshot)

  def scrollDown(self):
    """Scroll Down."""
    self.Browser.execute_script("window.\
                                 scrollTo(0, document.body.scrollHeight);")

  def terminateInstance(self):
    """Take a screenshot, clear the datastore and close the browser."""    
    # Take a screenshot
    self.takeScreenshot()
    self.Browser.close()
    # Clear Datastore
    self.clearDatastore()
    # Kill the server
    os.killpg(self.server_process.pid, signal.SIGTERM)        
    # Delete *.pyc files
    subprocess.call('find . -name "*.pyc" -delete', shell=True)   
    # Delete temporary files.
    self.deleteTemporaryFiles()

  def clearDatastore(self):
    """Clear the datastore."""
    seed_db.clear()

  def deleteTemporaryFiles(self):
    """Delete the temporary files."""  
    pattern = "/tmp/tmp*"
    tmpdir = glob.glob(pattern)
    for temporary_file in tmpdir:
      if os.path.isdir(temporary_file):
        shutil.rmtree(temporary_file)
      else:
        os.remove(temporary_file)

  def login(self):
    """Login to melange."""
    Url = self.obj_id["Url"]
    if 'localhost' in Url:
      self.clearField("Login_email_localhost")
      self.writeTextField("Login_email_localhost")
      self.clickOn("Sign_in_button_localhost")
    else:
      time.sleep(5)
      self.clearField("Google_account")
      self.writeTextField("Google_account")
      time.sleep(2)
      self.writeTextField("Password_for_google_account")
      time.sleep(2)    
      self.clickOn("Sign_in")

