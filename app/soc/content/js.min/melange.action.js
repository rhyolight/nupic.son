(function(){if(window.melange===undefined)throw new Error("Melange not loaded");var b=window.melange;b.action=window.melange.action=function(){return new b.action};var d=b.logging.debugDecorator(b.action);b.error.createErrors([]);d.createFloatMenu=function(){var a=null;jQuery(document).ready(function(){a=parseInt(jQuery("#floatMenu").css("top").substring(0,jQuery("#floatMenu").css("top").indexOf("px")));jQuery(window).scroll(function(){offset=a+jQuery(document).scrollTop()+"px";jQuery("#floatMenu").animate({top:offset},
{duration:500,queue:false})})})};d.toggleButton=function(a,f,g,h,e){var c=h;jQuery(window).load(function(){jQuery("."+f+" :checkbox#"+a).iphoneStyle({checkedLabel:e.checked,uncheckedLabel:e.unchecked}).change(function(){jQuery.post(g,{value:c,xsrf_token:window.xsrf_token},function(){if(c=="checked")c="unchecked";else if(c=="unchecked")c="checked"})})})};d.createOnChangeButton=function(){var a=jQuery(".onchange :checkbox").iphoneStyle();setInterval(function(){a.attr("checked",!a.is(":checked")).change();
jQuery("span#status").html(a.is(":checked").toString())},2500)};d.createCluetip=function(){jQuery(document).ready(function(){jQuery("a.load-tooltip").cluetip({local:true,cursor:"pointer",showTitle:false,tracking:true,dropShadow:false})})}})();
