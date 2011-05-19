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
 * @author <a href="mailto:fadinlight@gmail.com">Mario Ferraro</a>
 */

(function() {
  var template_name = "survey";

  melange.template[template_name] = function(_self, context) {
  };

  melange.template[template_name].prototype = new melange.templates._baseTemplate();
  melange.template[template_name].prototype.constructor = melange.template[template_name];
  melange.template[template_name].apply(
    melange.template[template_name],
    [melange.template[template_name], melange.template[template_name].prototype.context]
  );
}());
