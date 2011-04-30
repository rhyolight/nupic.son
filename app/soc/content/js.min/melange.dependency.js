(function(){if(window.melange===undefined)throw new Error("Melange not loaded");var e=window.melange;e.dependency=window.melange.dependency=function(){return new e.dependency};var g=e.logging.debugDecorator(e.dependency);e.error.createErrors([]);g.templateWithContext=function(f,c){this.script_template=f;this.context=c};g.cssFile=function(f){this.css=f};var a={},b="/js/"+e.config.app_version+"/",h="/soc/content/"+e.config.app_version+"/js/",l="/soc/content/"+e.config.app_version+"/css/";a.google=e.config.google_api_key!==
undefined?["http://www.google.com/jsapi?key="+e.config.google_api_key]:["http://www.google.com/jsapi"];a.jquery=e.config.is_local!==undefined&&e.config.is_local===true?[b+"jquery/jquery-1.5.js"]:["https://ajax.googleapis.com/ajax/libs/jquery/1.5/jquery.min.js"];a.json=[b+"json/json2.js"];a.tinymce=["/tiny_mce/tiny_mce.js"];a.purr=[b+"jquery/jquery-purr.js"];a.counter=[b+"jquery/jquery-counter.js"];a.spin=[b+"jquery/jquery-spin-1.1.1.js"];a.bgiframe=[b+"jquery/jquery-bgiframe.js"];a.ajaxQueue=[b+"jquery/jquery-ajaxQueue.js"];
a.progressbar=[b+"jquery/jquery-progressbar.js"];a.uniform=[b+"jquery/jquery-uniform.js"];a.raty=[b+"jquery/jquery.raty.js"];a.cluetip=[b+"jquery/jquery.cluetip.js"];a.dimensions=[b+"jquery/jquery.dimensions.js"];a.jqueryui={};a.jqueryui.core=e.config.is_local!==undefined&&e.config.is_local===true?[new g.cssFile(l+"jquery-ui/jquery.ui.all.css"),b+"jquery/jquery-ui.core.js"]:[new g.cssFile(l+"jquery-ui/jquery.ui.merged.css"),b+"jquery/jquery-ui.core.js"];a.jqueryui.datepicker=[a.jqueryui.core,null,
b+"jquery/jquery-ui.datepicker.js"];a.jqueryui.position=[a.jqueryui.core,null,b+"jquery/jquery-ui.position.js"];a.jqueryui.widget=[a.jqueryui.core,null,b+"jquery/jquery-ui.widget.js"];a.jqueryui.button=[a.jqueryui.widget,null,b+"jquery/jquery-ui.button.js"];a.jqueryui.autocomplete=[a.jqueryui.position,a.jqueryui.widget,null,b+"jquery/jquery-ui.autocomplete.js"];a.jqueryui.dialog=[a.jqueryui.position,a.jqueryui.widget,null,b+"jquery/jquery-ui.dialog.js"];a.jqueryui.checkboxes=[a.jqueryui.core,b+"jquery/jquery.ui-checkboxes.js"];
a.jqgrid=[a.jqueryui.core,null,new g.cssFile(l+"v2/gsoc/ui.jqgrid.css"),b+"jquery/jquery-jqgrid.locale-en.js",null,b+"jquery/jquery-jqgrid.base.js",null,b+"jquery/jquery-jqgrid.custom.js",b+"jquery/jquery-jqgrid.setcolumns.js"];a.jqgridediting=[a.jqgrid,null,b+"jquery/jquery-jqgrid.common.js",b+"jquery/jquery-jqgrid.fmatter.js",b+"jquery/jquery-jqgrid.formedit.js",null,b+"jquery/jquery-jqgrid.searchFilter.js",b+"jquery/jquery-jqgrid.inlinedit.js",null,b+"jquery/jquery-jqgrid.jqDnR.js",null,b+"jquery/jquery-jqgrid.jqModal.js"];
a.cookie=[b+"jquery/jquery-cookie.js"];a.jlinq=[b+"jlinq/jLinq-2.2.1.js"];a.melange={};a.melange.main=[a.google,a.cookie,null,h+"melange.js"];a.melange.datetimepicker=[a.jqueryui.datepicker,null,h+"melange.datetimepicker.js"];a.melange.duplicates=[a.progressbar,null,h+"duplicate-slots.js"];a.melange.form=[];a.melange.list=[a.jqgrid,a.jlinq,new g.cssFile(l+"v2/gsoc/others.css"),null,a.jqueryui.dialog,a.jqueryui.button,a.jqgridediting,null,h+"melange.list.js",null,function(){window.melange_list_queue!==
undefined&&window.melange_list_queue instanceof Array&&jQuery.each(window.melange_list_queue,function(f,c){c()})}];a.melange.tooltip=[a.purr,null];a.melange.autocomplete=[a.jqueryui.autocomplete,null,h+"melange.autocomplete.js"];a.melange.graph=[a.google,null,h+"melange.graph.js"];a.melange.uploadform=[h+"upload-form.js"];a.melange.blog=[a.google,null,h+"melange.blog.js"];a.melange.action=[a.dimensions,a.cluetip,a.jqueryui.checkboxes,null,h+"melange.action.js"];a.melange.map=[h+"melange.map.js"];
g.s=a;var m=function(f){for(var c=[],k=0,d=f.length;k<d;k++){var i=f[k];if(typeof i==="object"&&i instanceof Array){i=m(i);c=c.concat(i)}else c.push(i)}return c};g.loadScripts=function(f){f=m(f);for(var c=[],k=[],d=0,i=f.length;d<i;d++){var j=f[d];if(typeof j=="string")jQuery.inArray(j,c)===-1&&c.push(j);else if(j instanceof g.cssFile){if(jQuery.inArray(j.css,k)===-1){c.push(j);k.push(j.css)}}else c.push(j)}d=0;for(i=c.length;d<i;d++)if(typeof c[d]=="string")$LAB=$LAB.script(c[d]);else if(c[d])if(typeof c[d]==
"object"&&c[d]instanceof g.templateWithContext)$LAB=$LAB.script(c[d].script_template).wait(function(n){return function(){e.templates.setContextToLast(n)}}(c[d].context)).wait();else if(typeof c[d]=="object"&&c[d]instanceof g.cssFile)jQuery("<link>",{href:c[d].css,media:"screen",rel:"stylesheet",type:"text/css"}).appendTo("head");else{if(typeof c[d]=="function")$LAB=$LAB.wait(c[d])}else $LAB=$LAB.wait()}})();
