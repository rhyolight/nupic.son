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

"""Test case for GSoC student registration process."""

from melange_functional_actions import FunctionalTestCase

from tests.timeline_utils import GSoCTimelineHelper

class StudentRegistrationTest(FunctionalTestCase):

  def setUp(self):
    self.init()
    self.createGSoCProgram()
    self.timeline = GSoCTimelineHelper(self.gsoc.timeline, self.org_app)
    self.timeline.studentSignup()
    # TODO(nathaniel): Extract this giant list of dicts in to a constant.
    self.properties=[{"Object":"Url","Identification":"http://localhost:%d/gsoc/homepage/" %self.port,"Value":None},
{"Object":"How Google Summer of Code Works","Identification":"title-section-how-it-works","Value":"How Google Summer of Code Works"},
{"Object":"Register_Button","Identification":"//*[@id='block-apply-text-action']/a[2]","Value":None},
{"Object":"Login_email_localhost","Identification":"email","Value":"test101@gmail.com"},
{"Object":"Sign_in_button_localhost","Identification":"submit-login","Value":None},
{"Object":"Google_account","Identification":"email","Value":None},
{"Object":"Password_for_google_account","Identification":"Passwd","Value":None},
{"Object":"Sign_in","Identification":"signIn","Value":None},
{"Object":"User_name","Identification":"link_id","Value":"Lucy12"},
{"Object":"Public_name","Identification":"public_name","Value":"Lucy"},
{"Object":"Im_network","Identification":"im_network","Value":"irc.freenode.net"},
{"Object":"Im_handle","Identification":"im_handle","Value":"#lucy"},
{"Object":"Home_page_url","Identification":"home_page","Value":"www.lucy.com"},
{"Object":"Blog_url","Identification":"blog","Value":"lucy.blogspot.com"},
{"Object":"Thumbnail_photo_url","Identification":"photo_url","Value":"lucy.blogspot.com"},
{"Object":"First_name","Identification":"given_name","Value":"Lucy"},
{"Object":"Last_name","Identification":"surname","Value":"Mcmaan"},
{"Object":"Email","Identification":"email","Value":"lucy@gmail.com"},
{"Object":"Residential_street","Identification":"res_street","Value":"alpha street"},
{"Object":"Residential_street_extra","Identification":"res_street_extra","Value":"beta street"},
{"Object":"City","Identification":"res_city","Value":"New Delhi"},
{"Object":"State","Identification":"res_state","Value":"New Delhi"},
{"Object":"Country","Identification":"res_country","Value":"India"},
{"Object":"Postal_code","Identification":"res_postalcode","Value":"98765"},
{"Object":"Phone","Identification":"phone","Value":"09876546789"},
{"Object":"Publish_my_location","Identification":"publish_location","Value":None},
{"Object":"Full_recipient_name","Identification":"ship_name","Value":"Donald Mcmann"},
{"Object":"Shipping_street","Identification":"ship_street","Value":"alpha street"},
{"Object":"Shipping_street_extra","Identification":"ship_street_extra","Value":"beta street"},
{"Object":"Shipping_city","Identification":"ship_city","Value":"New Delhi"},
{"Object":"Shipping_state","Identification":"ship_state","Value":"New Delhi"},
{"Object":"Shipping_country","Identification":"ship_country","Value":"India"},
{"Object":"Shipping_postal_code","Identification":"ship_postalcode","Value":"98765"},
{"Object":"Birth_date","Identification":"birth_date","Value":"1990-08-09"},
{"Object":"T_shirt_style","Identification":"tshirt_style","Value":"female"},
{"Object":"T_shirt_size","Identification":"tshirt_size","Value":"M"},
{"Object":"Gender","Identification":"gender","Value":"female"},
{"Object":"How_did_you_hear_about_gsoc","Identification":"melange-program_knowledge-textarea","Value":"friends"},
{"Object":"I_agree","Identification":"agreed_to_tos","Value":None},
{"Object":"Notify_to_new_public_comments","Identification":"notify_public_comments","Value":None},
{"Object":"School_name","Identification":"school_name","Value":"Delhi University"},
{"Object":"School_country","Identification":"school_country","Value":"India"},
{"Object":"Major_subject","Identification":"major","Value":"Computer"},
{"Object":"Degree","Identification":"degree","Value":"Undergraduate"},
{"Object":"Expected_graduation","Identification":"expected_graduation","Value":"2012"},
{"Object":"School_homepage","Identification":"school_home_page","Value":"www.abc.com"},
{"Object":"Submit_button","Identification":"form-register-submit","Value":None},
{"Object":"Message_from_melange","Identification":"//*[@id='flash-message']/p","Value":"Sorry, we could not save your data. Please fix the errors mentioned below."}]
     
  def testGSoCRegisterAsAStudent(self):
    # Load test data.
    self.loadProperties()

    # Test url, Change it according to your environment.
    self.openUrl("gsoc")
  
    # Scroll down.
    self.scrollDown()
  
    # Click on Register.
    self.wait(3)
    self.clickOn("Register_Button")
  
    # Login on melange.
    self.wait(3) 
    self.login()

    # Wait for the page load completely, then fill the user name field.
    self.waitAndEnterText(5, "User_name")
    
    # Fill the public name field.
    self.writeTextField("Public_name")
    self.scrollDown()

    # Fill IM network field.
    self.writeTextField("Im_network")

    # Fill IM handle field.
    self.writeTextField("Im_handle")
  
    # Enter a valid home page address.
    self.writeTextField("Home_page_url")
  
    # Enter a valid blog address.
    self.writeTextField("Blog_url")
  
    # Enter photo url.
    self.writeTextField("Thumbnail_photo_url")

    # Enter given Name.
    self.writeTextField("First_name")

    # Enter surname.
    self.writeTextField("Last_name")

    # Enter email.
    self.writeTextField("Email")

    # Enter residential street address.
    self.writeTextField("Residential_street")

    # Enter extra residential address.
    self.writeTextField("Residential_street_extra")

    # Enter the city.
    self.writeTextField("City")

    # Enter state.
    self.writeTextField("State")

    # Traverse through country names and select a country from the list.
    self.setDropDownList("Country")
    self.wait(2)

    # Enter postal code.
    self.writeTextField("Postal_code")    

    # Enter phone number.
    self.writeTextField("Phone")

    # Enter full recipient name.
    self.writeTextField("Full_recipient_name")

    # Enter shipping street address.
    self.writeTextField("Shipping_street")

    # Enter extra shipping street address.
    self.writeTextField("Shipping_street_extra")

    # Enter the city name for shipment.
    self.writeTextField("Shipping_city")

    # Enter state.
    self.writeTextField("Shipping_state")
  
    # Traverse through country names and select a country from the list.
    self.setDropDownList("Shipping_country")    

    # Enter postal code.
    self.writeTextField("Shipping_postal_code")

    # Enter the date of birth.
    self.writeTextField("Birth_date")
  
    # Traverse through the list and select t-shirt style.
    self.setDropDownList("T_shirt_style")    

    # Traverse through the list and select a t-shirt size.
    self.setDropDownList("T_shirt_size")

    # Select gender as female.
    self.setDropDownList("Gender")

    # Fill the text area.
    self.writeTextField("How_did_you_hear_about_gsoc")

    # Unset the check box for notification to new comments.
    self.toggleCheckBox("Notify_to_new_public_comments")
 
    # Enter school name.
    self.writeTextField("School_name")   

    # Select school country.
    self.setDropDownList("School_country")
  
    # Enter major subject.
    self.writeTextField("Major_subject")
  
    # Select degree.
    self.setDropDownList("Degree")
  
    # Enter expected graduation.
    self.writeTextField("Expected_graduation")
  
    # Enter school homepage URL.
    self.writeTextField("School_homepage")
 
    # Submit.
    self.clickOn("Submit_button")

  def tearDown(self):
    self.terminateInstance()

