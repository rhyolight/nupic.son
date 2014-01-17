/*
 * Copyright 2014 the Melange authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

(function (melange) {
  /** @lends melange.analytics */

  if (melange === undefined) {
    throw new Error("Melange not loaded");
  }

  /** Package that handles all analytics related functions.
    * @name melange.analytics
    * @namespace melange.analytics
    */
  melange.analytics = {};

  melange.analytics.initAnalytics = function(ga_tracking_num) {
    var _gaq = _gaq || [];
    _gaq.push(['_setAccount', ga_tracking_num]);
    _gaq.push(['_setDomainName', 'none']);
    _gaq.push(['_setAllowLinker', true]);
    _gaq.push(['_trackPageview']);

    // Add pixel ratio if applicable.
    if (window.devicePixelRatio) {
      _gaq.push(['_setCustomVar', 1, 'Pixel Ratio', window.devicePixelRatio, 2 ]);
    }

    var ga = document.createElement('script');

    ga.type = 'text/javascript';
    ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(ga, s);
  };
}(window.melange));
