jQuery(function(){jQuery("#menu li.expandable, #menu li.expandable-collapsed").find("a").each(function(){jQuery(this).text().indexOf("(new)")>-1&&jQuery(this).css("color","red")});jQuery("#side #menu li.expandable > a, #side #menu li.expandable-collapsed > a").dblclick(function(){window.location=jQuery(this).attr("href")});var b=function(){var a=jQuery(this);if(a.parent("li:last").hasClass("expandable")){a.find("img").attr("src","/soc/content/images/plus.gif").end().parent().children("ul").toggle();
jQuery(this).parent("li:last").addClass("expandable-collapsed").removeClass("expandable")}else{a.find("img").attr("src","/soc/content/images/minus.gif").end().parent().children("ul").toggle();jQuery(this).parent("li:last").addClass("expandable").removeClass("expandable-collapsed")}};jQuery("#side #menu li[class^=expandable] > span").toggle(b,b);(function(){jQuery("#side #menu li.expandable > span").contents().before('<img src="/soc/content/images/minus.gif" />');jQuery("#side #menu li.expandable-collapsed > span").contents().before('<img src="/soc/content/images/plus.gif" />');
jQuery("#side #menu li.expandable-collapsed > ul").toggle()})()});
