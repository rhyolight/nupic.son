(function(){if(window.melange===undefined)throw new Error("Melange not loaded");window.melange.getUploadUrl=function(){var a="?";if(window.location.href.indexOf("?")!==-1)a="&";return jQuery.ajax({async:false,cache:false,url:[window.location.href,a,"fmt=json"].join(""),error:function(c,d,b){alert("Could not retrieve upload url: '"+b+"'.")}}).responseText}})(jQuery);
