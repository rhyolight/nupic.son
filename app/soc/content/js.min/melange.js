(function(){var d=window.melange=function(){return new d};if(window.jQuery===undefined)throw new Error("jQuery package must be loaded exposing jQuery namespace");var f=d;f.config={};f.init=function(a){if(a)f.config=jQuery.extend(f.config,a)};f.clone=function(a){return jQuery.extend(true,{},a)};f.setOptions=function(a){switch(a.debug){case true:f.logging.setDebug();break;case false:f.logging.unsetDebug();break;default:f.logging.setDebug()}a.debugLevel&&f.logging.setDebugLevel(a.debugLevel)};f.tinyMceConfig=
function(a,b){var e={basic:{height:400,width:500,mode:"exact",relative_urls:0,remove_script_host:0,theme:"advanced",theme_advanced_path:false,theme_advanced_resizing:false,theme_advanced_resizing_max_height:600,theme_advanced_resizing_max_width:600,theme_advanced_statusbar_location:"bottom",theme_advanced_toolbar_align:"left",theme_advanced_toolbar_location:"top",theme_advanced_buttons1:["bold,italic,underline,fontsizeselect,|,bullist,numlist,outdent,","indent,|,undo,redo,|,justifyleft,justifycenter,justifyright,|,link,unlink,anchor"].join(),
theme_advanced_buttons2:"",theme_advanced_buttons3:"",theme_advanced_source_editor_width:700},advanced:{gecko_spellcheck:"true",theme_advanced_blockformats:"p,div,h1,h2,h3,h4,h5,h6,blockquote,dt,dd,code,samp",theme_advanced_buttons1:["bold,italic,underline,strikethrough,hr,","|,fontselect,formatselect,fontsizeselect,forecolor"].join(),theme_advanced_buttons3:"",theme_advanced_buttons2:["undo,redo,|,justifyleft,justifycenter,justifyright,|,","link,unlink,anchor,code,image,|,bullist,numlist,outdent,indent"].join(),
theme_advanced_fonts:["Andale Mono=andale mono,times;","Arial=arial,helvetica,sans-serif;","Arial Black=arial black,avant garde;","Book Antiqua=book antiqua,palatino;","Comic Sans MS=comic sans ms,sans-serif;","Courier New=courier new,courier;","Georgia=georgia,palatino;","Helvetica=helvetica;","Impact=impact,chicago;","Symbol=symbol;","Tahoma=tahoma,arial,helvetica,sans-serif;","Terminal=terminal,monaco;","Times New Roman=times new roman,times;","Trebuchet MS=trebuchet ms,geneva;","Verdana=verdana,geneva;",
"Webdings=webdings;","Wingdings=wingdings,zapf dingbats"].join()}},c=e.basic;b!==undefined&&b!==null&&e[b]!==undefined&&jQuery.extend(c,e[b]);a=a.join(",");return jQuery.extend(c,{elements:a})};f.loadGoogleApi=function(a,b,e,c){if(!a||!b)throw new TypeError("modulename must be defined");a={name:a,version:b,settings:e};jQuery.extend(a.settings,{callback:c});google.load(a.name,a.version,a.settings)};(function(){d.cookie=window.melange.cookie=function(){return new d.cookie};var a=d.cookie;a.MELANGE_USER_PREFERENCES=
"melange_user_preferences";a.getCookie=function(b){var e={lists_configuration:{}};b=jQuery.cookie(b);try{b=JSON.parse(b);if(b===null)throw"null_cookie";}catch(c){b=e}return b};a.saveCookie=function(b,e,c,g){jQuery.cookie(b,JSON.stringify(e),{expires:c,path:g})}})();(function(){d.error=window.melange.error=function(){return new d.error};var a=d.error;a.createErrors=function(b){jQuery.each(b,function(){d.error[this]=Error})};a.createErrors(["DependencyNotSatisfied","notImplementedByChildClass"])})();
(function(){d.logging=window.melange.logging=function(){return new d.logging};var a=d.logging,b=false,e=5;a.setDebug=function(){b=true};a.unsetDebug=function(){b=false};a.isDebug=function(){return b?true:false};a.setDebugLevel=function(c){if(isNaN(c))throw new d.error.TypeError("melange.logging.setDebugLevel: parameter must be a number");if(c<=0)c=1;if(c>=6)c=5;e=c};a.getDebugLevel=function(){return e};a.debugDecorator=function(c){c.log=function(g,h){d.logging.isDebug()&&e>=g&&console.debug(h)};return c}})();
(function(){d.templates=window.melange.templates=function(){return new d.templates};var a=d.logging.debugDecorator(d.templates);d.error.createErrors([]);var b=[];a.setContextToLast=function(e){var c=b[b.length-1];c.context=jQuery.extend(c.context,e)};a._baseTemplate=function(){this.context={};b.push(this)}})()})();window.melange=window.melange.logging.debugDecorator(window.melange);
