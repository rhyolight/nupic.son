(function(){if(window.melange===undefined)throw new Error("Melange not loaded");var f=window.melange;f.dependency=window.melange.dependency=function(){return new f.dependency};var g=f.logging.debugDecorator(f.dependency);f.error.createErrors([]);g.templateWithContext=function(d,b){this.script_template=d;this.context=b};g.cssFile=function(d){this.css=d};var a={};a.google=f.config.google_api_key!==undefined?["http://www.google.com/jsapi?key="+f.config.google_api_key]:["http://www.google.com/jsapi"];
a.jquery=f.config.is_local!==undefined&&f.config.is_local===true?["/jquery/jquery-1.5.js"]:["http://ajax.googleapis.com/ajax/libs/jquery/1.5/jquery.min.js"];a.json=["/json/json2.js"];a.tinymce=["/tiny_mce/tiny_mce.js"];a.purr=["/jquery/jquery-purr.js"];a.spin=["/jquery/jquery-spin-1.1.1.js"];a.bgiframe=["/jquery/jquery-bgiframe.js"];a.ajaxQueue=["/jquery/jquery-ajaxQueue.js"];a.autocomplete=[new g.cssFile("/soc/content/css/jquery-autocomplete-090304.css"),"/jquery/jquery-autocomplete.js"];a.thickbox=
["/jquery/jquery-thickbox.js"];a.progressbar=["/jquery/jquery-progressbar.js"];a.uniform=["/jquery/jquery-uniform.js"];a.jqueryui=[new g.cssFile("/soc/content/css/v2/gsoc/jquery-ui.css"),"/jquery/jquery-ui.core.js"];a.jqgrid=[a.jqueryui,null,new g.cssFile("/soc/content/css/v2/gsoc/ui.jqgrid.css"),"/jquery/jquery-jqgrid.locale-en.js",null,"/jquery/jquery-jqgrid.base.js",null,"/jquery/jquery-jqgrid.custom.js","/jquery/jquery-jqgrid.setcolumns.js"];a.jqgridediting=[a.jqgrid,null,"/jquery/jquery-jqgrid.common.js",
"/jquery/jquery-jqgrid.formedit.js",null,"/jquery/jquery-jqgrid.searchFilter.js","/jquery/jquery-jqgrid.inlinedit.js",null,"/jquery/jquery-jqgrid.jqDnR.js",null,"/jquery/jquery-jqgrid.jqModal.js"];a.cookie=["/jquery/jquery-cookie.js"];a.jlinq=["/jlinq/jLinq-2.2.1.js"];a.melange={};a.melange.main=[a.google,null,"/soc/content/js/melange-091015.js"];a.melange.datetimepicker=[a.jqueryui,null,"/jquery-ui.datetimepicker.js",null,"/soc/content/js/datetimepicker-090825.js",null,"/soc/content/js/datetime-loader-090825.js"];
a.melange.menu=[a.cookie,null,"/soc/content/js/menu-110128.js"];a.melange.duplicates=[a.progressbar,null,"/soc/content/js/duplicate-slots-090825.js"];a.melange.form=[];a.melange.list=[a.jqgrid,a.jlinq,null,a.jqgridediting,null,"/soc/content/js/melange.list-110204.js"];a.melange.tooltip=[a.purr,null];a.melange.autocomplete=[a.autocomplete,null,"/soc/content/js/melange.autocomplete-110227.js"];a.melange.graph=[a.google,null,"/soc/content/js/melange.graph-100501.js"];a.melange.uploadform=["/soc/content/js/upload-form-101205.js"];
a.melange.blog=[a.google,null,"/soc/content/js/melange.blog-090825.js"];g.s=a;var i=function(d){for(var b=[],c=0,h=d.length;c<h;c++){var e=d[c];if(typeof e==="object"&&e instanceof Array){e=i(e);b=b.concat(e)}else b.push(e)}return b};g.loadScripts=function(d){d=i(d);for(var b=[],c=0,h=d.length;c<h;c++){var e=d[c];if(typeof e=="string")jQuery.inArray(e,b)===-1&&b.push(e);else b.push(e)}c=0;for(h=b.length;c<h;c++)if(typeof b[c]=="string")$LAB=$LAB.script(b[c]);else if(b[c])if(typeof b[c]=="object"&&
b[c]instanceof g.templateWithContext)$LAB=$LAB.script(b[c].script_template).wait(function(j){return function(){f.templates.setContextToLast(j)}}(b[c].context)).wait();else if(typeof b[c]=="object"&&b[c]instanceof g.cssFile)jQuery("<link>",{href:b[c].css,media:"screen",rel:"stylesheet",type:"text/css"}).appendTo("head");else{if(typeof b[c]=="function")$LAB=$LAB.wait(b[c])}else $LAB=$LAB.wait()}})();
