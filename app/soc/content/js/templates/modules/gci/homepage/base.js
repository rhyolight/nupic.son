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
    function initialize() {
      var blog = new BlogPreview(document.getElementById("blog-feed"));
      blog.show(context.feed_url, 3, "What's New");
    }

    if (typeof context.feed_url !== "undefined") {
      jQuery(
        function () {
          google.load("feeds","1", {callback:initialize});
        }
      );
    }
    melange.clock.loadClock(context.complete_percentage);
  }
);
