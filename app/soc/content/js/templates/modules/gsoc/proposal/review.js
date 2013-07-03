/* Copyright 2013 the Melange authors.
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
melange.templates.inherit(
  function (_self, context) {
    /* Apply Uniform CSS to form fields. */
    /* Only in this case we are customizing the input type checkbox to be
       only applied for the field with the id is_private since it interferes
       with the awesome looking action buttons */
    jQuery("select, input:radio, input:file, input:checkbox#is_private").uniform();

    /* Change all the tooltips to be displayed onhover over a
      * question mark. Calling this function only once will take
      * care of all such instances.
      */
    melange.action.createCluetip();

    /* Create the project featured button and make it post using ajax. */
    if (typeof context.user_toggle_buttons !== "undefined") {
      jQuery.each(context.user_toggle_buttons, function(index, button) {
        melange.action.toggleButton(
          button.id,
          button.type,
          button.post_url,
          button.state,
          {
            checked: button.checked_label,
            unchecked: button.unchecked_label
          }
        );
      });
    }

    if (typeof context.public_comments_visible !== 'undefined' && context.public_comments_visible === true) {
      tinyMCE.init(melange.tinyMceConfig(["melange-content-textarea"]));
    }

    if (typeof context.score !== 'undefined') {

      var initialTotal = context.score.total;
      var initialNumber = context.score.number;
      var userInitialScore = context.score.user_score;
      var maxScore = context.score.max_score;

      var successHandler = function (userScore) {
        userScore = parseInt(userScore);
        var newTotal = (initialTotal - userInitialScore + userScore);

        var newNumber = initialNumber;
        /* the user did not score */
        if (!userInitialScore && userScore) {
          newNumber++;
        }
        /* the user removed his or her score */
        if (userInitialScore && !userScore) {
          newNumber--;
        }

        var newAverage;
        var newMessage;
        if (!newNumber) {
          newAverage = 0;
          newMessage = 'No scores yet';
        } else {
          newAverage = Math.floor(newTotal / newNumber);
          newMessage = newAverage + '/' + maxScore + ' out of ' + newNumber + ' users, total: ' + newTotal;
        }
        jQuery.fn.raty.start(newAverage, '#score-average-stars');
        jQuery('#score-average-desc em').html(newMessage);
      };

      jQuery(document).ready(function() {
          jQuery('#score-average-stars').raty({
            number: maxScore,
            readOnly:   true,
            start:      context.score.average,
            half:     true,
            path:       '/soc/content/' + melange.config.app_version + '/images/gsoc',
            starHalf:   'proposal-rate-star-half.png',
            starOff:    'proposal-rate-star-off.png',
            starOn:     'proposal-rate-star-on.png'
          });
      });

      hintList = [];
      for(var i = 0; i < maxScore; i++) {
        hintList[i] = '' + (i + 1) + ' star(s)';
      }

      $('#score-add-stars').raty({
          cancel: true,
          cancelPlace:'right',
          cancelOff: 'proposal-rate-cancel-off.png',
          cancelOn: 'proposal-rate-cancel-on.png',
          cancelHint: 'Remove my rating',
          click: function (value) {
              jQuery.post(context.score.score_action, {value: value, xsrf_token: window.xsrf_token});
              successHandler(value);
          },
          half:   false,
          path:       '/soc/content/' + melange.config.app_version + '/images/gsoc',
          number: maxScore,
          start:      context.score.user_score,
          starHalf:   'proposal-rate-star-half.png',
          starOff:    'proposal-rate-star-off.png',
          starOn:     'proposal-rate-star-on.png',
          hintList:   hintList
      });
    }
  }
);
