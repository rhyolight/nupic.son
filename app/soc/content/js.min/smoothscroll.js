var ss={fixAllLinks:function(){for(var b=document.getElementsByTagName("a"),c=0;c<b.length;c++){var a=b[c];if(a.href&&a.href.indexOf("#")!=-1&&(a.pathname==location.pathname||"/"+a.pathname==location.pathname)&&a.search==location.search)ss.addEvent(a,"click",ss.smoothScroll)}},smoothScroll:function(b){if(window.event)target=window.event.srcElement;else if(b)target=b.target;else return;if(target.nodeName.toLowerCase()!="a")target=target.parentNode;if(target.nodeName.toLowerCase()=="a"){anchor=target.hash.substr(1);
for(var c=document.getElementsByTagName("a"),a=null,d=0;d<c.length;d++){var e=c[d];if(e.name&&e.name==anchor){a=e;break}}a||(a=document.getElementById(anchor));if(!a)return true;c=a.offsetLeft;d=a.offsetTop;for(a=a;a.offsetParent&&a.offsetParent!=document.body;){a=a.offsetParent;c+=a.offsetLeft;d+=a.offsetTop}clearInterval(ss.INTERVAL);cypos=ss.getCurrentYPos();ss_stepsize=parseInt((d-cypos)/ss.STEPS);ss.INTERVAL=setInterval("ss.scrollWindow("+ss_stepsize+","+d+',"'+anchor+'")',10);if(window.event){window.event.cancelBubble=
true;window.event.returnValue=false}if(b&&b.preventDefault&&b.stopPropagation){b.preventDefault();b.stopPropagation()}}},scrollWindow:function(b,c,a){wascypos=ss.getCurrentYPos();isAbove=wascypos<c;window.scrollTo(0,wascypos+b);iscypos=ss.getCurrentYPos();isAboveNow=iscypos<c;if(isAbove!=isAboveNow||wascypos==iscypos){window.scrollTo(0,c);clearInterval(ss.INTERVAL);location.hash=a}},getCurrentYPos:function(){if(document.body&&document.body.scrollTop)return document.body.scrollTop;if(document.documentElement&&
document.documentElement.scrollTop)return document.documentElement.scrollTop;if(window.pageYOffset)return window.pageYOffset;return 0},addEvent:function(b,c,a,d){if(b.addEventListener){b.addEventListener(c,a,d);return true}else if(b.attachEvent)return b.attachEvent("on"+c,a);else alert("Handler could not be removed")}};ss.STEPS=25;ss.addEvent(window,"load",ss.fixAllLinks);