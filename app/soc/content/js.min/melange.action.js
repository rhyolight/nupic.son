(function(){if(window.melange===undefined)throw new Error("Melange not loaded");var c=window.melange;c.action=window.melange.action=function(){return new c.action};var a=c.logging.debugDecorator(c.action);c.error.createErrors([]);a.createFloatMenu=function(){var b=null;$(document).ready(function(){b=parseInt($("#floatMenu").css("top").substring(0,$("#floatMenu").css("top").indexOf("px")));$(window).scroll(function(){offset=b+$(document).scrollTop()+"px";$("#floatMenu").animate({top:offset},{duration:500,
queue:false})})})};a.createToggleButton=function(){$(window).load(function(){$(".on_off :checkbox").iphoneStyle({checkedLabel:"Yes",uncheckedLabel:"No"});$(".disabled :checkbox").iphoneStyle({checkedLabel:"Yes",uncheckedLabel:"No"});$(".long :checkbox").iphoneStyle({checkedLabel:"Enable",uncheckedLabel:"Disable"});var b=$(".onchange :checkbox").iphoneStyle();setInterval(function(){b.attr("checked",!b.is(":checked")).change();$("span#status").html(b.is(":checked").toString())},2500)})};a.createCluetip=
function(){$(document).ready(function(){$("a.load-tooltip").cluetip({local:true,cursor:"pointer",showTitle:false,tracking:true,dropShadow:false})})};a.createActionBox=function(){a.createCluetip();a.createToggleButton()}})();
