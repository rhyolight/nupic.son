(function(){function l(){d=jQuery(e).text();f=jQuery(g).text()}function m(){if(google.maps.BrowserIsCompatible()){var c,h=n,i=true;a=new google.maps.Map2(document.getElementById(j));a.addControl(new google.maps.SmallMapControl);a.addControl(new google.maps.MapTypeControl);o=new google.maps.ClientGeocoder;if(jQuery(e).text()!==""&&jQuery(g).text()!==""){l();h=p;i=true}c=new google.maps.LatLng(d,f);a.setCenter(c,h);k=new google.maps.Marker(c,{draggable:false});i&&a.addOverlay(k)}}var b=window.melange;
this.prototype=new b.templates._baseTemplate;this.prototype.constructor=b.templates._baseTemplate;b.templates._baseTemplate.apply(this,arguments);console.log(this);var a,k,o,d=0,f=0,n=1,p=13,j="profile_map",e="#latitude",g="#longitude";jQuery(function(){jQuery("#form_row_publish_location").append("<div id='"+j+"'></div>");b.loadGoogleApi("maps","2",{},m)})})();
