/* Copyright 2011 the Melange authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * @author <a href="mailto:madhusudancs@gmail.com">Madhusudan.C.S</a>
 */
(function () {
  /** @lends melange.action */

  if (window.melange === undefined) {
    throw new Error("Melange not loaded");
  }

  var melange = window.melange;

  /** Package that handles all action buttons related functions
    * @name melange.action
    * @namespace melange.action
    * @borrows melange.logging.debugDecorator.log as log
    */
  melange.action = window.melange.action = function () {
    return new melange.action();
  };

  /** Shortcut to current package.
    * @private
    */
  var $m = melange.logging.debugDecorator(melange.action);

  melange.error.createErrors([
  ]);

  $m.createFloatMenu = function () {
    var name = "#floatMenu";
    var menuYloc = null;
    $(document).ready(function(){
      menuYloc = parseInt($(name).css("top").substring(0,$(name).css("top").indexOf("px")))
      $(window).scroll(function () { 
        offset = menuYloc+$(document).scrollTop()+"px";
        $(name).animate({top:offset},{duration:500,queue:false});
      });
    });
  }

  $m.createToggleButton = function () {
    $(window).load(function() {
      $('.on_off :checkbox').iphoneStyle({
        checkedLabel: 'Yes', uncheckedLabel: 'No'
      });
      $('.disabled :checkbox').iphoneStyle({
        checkedLabel: 'Yes', uncheckedLabel: 'No'
      });
      $('.long :checkbox').iphoneStyle({
        checkedLabel: 'Enable', uncheckedLabel: 'Disable'
      });

      var onchange_checkbox = $('.onchange :checkbox').iphoneStyle();
      setInterval(function toggleCheckbox() {
        onchange_checkbox.attr(
          'checked', !onchange_checkbox.is(':checked')).change();
        $('span#status').html(onchange_checkbox.is(':checked').toString());
      }, 2500);
    });
  }

  $m.createCluetip = function () {
    $(document).ready(function() {
      $('a.load-tooltip').cluetip({
        local:true,
        cursor: 'pointer',
        showTitle:false,
        tracking:true,
        dropShadow:false
      });
    });
  }

  $m.createActionBox = function () {
    $m.createCluetip();
    $m.createToggleButton();
  }
}());
