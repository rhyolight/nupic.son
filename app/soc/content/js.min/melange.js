(function(){var c=window.melange=function(){return new c};if(window.jQuery===undefined)throw new Error("jQuery package must be loaded exposing jQuery namespace");var e=c;e.config={};e.init=function(a){if(a)e.config=jQuery.extend(e.config,a)};e.clone=function(a){return jQuery.extend(true,{},a)};e.setOptions=function(a){switch(a.debug){case true:e.logging.setDebug();break;case false:e.logging.unsetDebug();break;default:e.logging.setDebug()}a.debugLevel&&e.logging.setDebugLevel(a.debugLevel)};e.tinyMceConfig=
function(a){a=a.join(",");return jQuery.extend({theme_advanced_toolbar_align:"left",theme_advanced_resizing:true,theme_advanced_statusbar_location:"bottom",theme_advanced_path:false,relative_urls:0,theme_advanced_toolbar_location:"top",theme_advanced_buttons1:"bold,italic,underline,strikethrough,|,fontsizeselect,forecolor,|,bullist,numlist,outdent,indent",theme_advanced_buttons3:"",theme_advanced_buttons2:"undo,redo,|,justifyleft,justifycenter,justifyright,|,link,unlink,anchor,code",remove_script_host:0,
theme:"advanced",mode:"exact"},{elements:a})};e.loadGoogleApi=function(a,b,f,d){if(!a||!b)throw new TypeError("modulename must be defined");a={name:a,version:b,settings:f};jQuery.extend(a.settings,{callback:d});google.load(a.name,a.version,a.settings)};(function(){c.cookie=window.melange.cookie=function(){return new c.cookie};var a=c.cookie;a.MELANGE_USER_PREFERENCES="melange_user_preferences";a.getCookie=function(b){var f={lists_configuration:{}};b=jQuery.cookie(b);try{b=JSON.parse(b);if(b===null)throw"null_cookie";
}catch(d){b=f}return b};a.saveCookie=function(b,f,d,g){jQuery.cookie(b,JSON.stringify(f),{expires:d,path:g})}})();(function(){c.error=window.melange.error=function(){return new c.error};var a=c.error;a.createErrors=function(b){jQuery.each(b,function(){c.error[this]=Error})};a.createErrors(["DependencyNotSatisfied","notImplementedByChildClass"])})();(function(){c.logging=window.melange.logging=function(){return new c.logging};var a=c.logging,b=false,f=5;a.setDebug=function(){b=true};a.unsetDebug=function(){b=
false};a.isDebug=function(){return b?true:false};a.setDebugLevel=function(d){if(isNaN(d))throw new c.error.TypeError("melange.logging.setDebugLevel: parameter must be a number");if(d<=0)d=1;if(d>=6)d=5;f=d};a.getDebugLevel=function(){return f};a.debugDecorator=function(d){d.log=function(g,h){c.logging.isDebug()&&f>=g&&console.debug(h)};return d}})();(function(){c.templates=window.melange.templates=function(){return new c.templates};var a=c.logging.debugDecorator(c.templates);c.error.createErrors([]);
var b=[];a.setContextToLast=function(f){var d=b[b.length-1];d.context=jQuery.extend(d.context,f)};a._baseTemplate=function(){this.context={};b.push(this)}})()})();window.melange=window.melange.logging.debugDecorator(window.melange);
