describe('melange.action', function() {
  beforeEach(function() {
    jasmine.getFixtures().fixturesPath = 'tests/app/soc/content/js';
    loadFixtures('melange_action_fixture.html');
    window.xsrf_token = 'dummy_token';
  });

  it('should be defined', function(){
     expect(melange.action).toBeDefined();
  });

  describe('createCluetip', function() {
    it('should call cluetip with the right parameters', function() {
       spyOn(jQuery.fn, 'cluetip');
       melange.action.createCluetip();
       expect(jQuery.fn.cluetip).toHaveBeenCalled();
       expect(jQuery.fn.cluetip.calls[0].object).toEqual(jQuery('a.load-tooltip'));
       var parameters = jQuery.fn.cluetip.mostRecentCall.args[0];
       expect(parameters.local).toEqual(true);
       expect(parameters.cursor).toEqual('pointer');
       expect(parameters.showTitle).toEqual(false);
       expect(parameters.tracking).toEqual(true);
       expect(parameters.dropShadow).toEqual(false);
    });
  });

  describe('createCluetip', function() {
    it('should create an hidden cluetip div that displays the right content on mouse over', function() {
       melange.action.createCluetip();

       var $tooltipDiv = jQuery('#example-tooltip');
       var $cluetipDiv = jQuery('#cluetip');
       expect($cluetipDiv.length).toEqual(1);
       expect($cluetipDiv.is(':visible')).toEqual(false);

       jQuery('#tooltip-link').trigger('mouseover');
       expect($cluetipDiv.is(':visible')).toEqual(true);

       var $tooltipInsideCluetip = $cluetipDiv.find('#example-tooltip');
       expect($tooltipInsideCluetip.length).toEqual(1);
       expect($tooltipInsideCluetip.is(':visible')).toEqual(true);
       expect($tooltipInsideCluetip.html()).toEqual($tooltipDiv.html());
    });
  });

  describe('toggleButton', function() {
    var buttonId = 'OnOffChecked';
    var buttonType = 'on_off';
    var buttonUrl = 'http://fake-url';
    var buttonState ='checked';
    var buttonCheckedLabel = 'Label Checked';
    var buttonUncheckedLabel = 'Label Unchecked';
    var buttonSelector = '.' + buttonType + ' :checkbox#' + buttonId;

    function callToggleButton(callback) {
      melange.action.toggleButton(
        buttonId,
        buttonType,
        buttonUrl,
        buttonState,
        {
          checked: buttonCheckedLabel,
          unchecked: buttonUncheckedLabel
        },
        callback
      );
    }

    it('should create a button with the correct labels', function() {
      spyOn(jQuery.fn, 'iphoneStyle').andCallThrough();
      callToggleButton();
      expect(jQuery.fn.iphoneStyle).toHaveBeenCalled();
      expect(jQuery.fn.iphoneStyle.calls[0].object).toEqual(jQuery(buttonSelector));
      var parameters = jQuery.fn.iphoneStyle.mostRecentCall.args[0];
      expect(parameters.checkedLabel).toEqual(buttonCheckedLabel);
      expect(parameters.uncheckedLabel).toEqual(buttonUncheckedLabel);
    });

    it('should call the proper URL with the proper parameters and call the bound callback', function() {
      var post_returned = false;
      var callback = jasmine.createSpy();
      spyOn(jQuery, 'ajax').andCallFake(function(e) {
        e.success({});
        post_returned = true;
      });
      callToggleButton(callback);

      jQuery('#' + buttonId).trigger('change');

      waitsFor(function() {
        return post_returned === true;
      });

      runs(function() {
        expect(jQuery.ajax.mostRecentCall.args[0]['url']).toEqual(buttonUrl);
        var parameters = jQuery.ajax.mostRecentCall.args[0]['data'];
        expect(parameters.id).toEqual(buttonId);
        expect(parameters.value).toEqual(buttonState);
        expect(parameters.xsrf_token).toEqual(window.xsrf_token);
        expect(callback).toHaveBeenCalled();
      });
    });

    it('should not crash with an undefined callback', function() {
      var post_returned = false;
      spyOn(jQuery, 'ajax').andCallFake(function(e) {
        e.success({});
        post_returned = true;
      });
      callToggleButton();

      jQuery(buttonSelector).trigger('change');

      waitsFor(function() {
        return post_returned === true;
      });
    });

    it('should not crash with a callback which is not a function', function() {
      var post_returned = false;
      spyOn(jQuery, 'ajax').andCallFake(function(e) {
        e.success({});
        post_returned = true;
      });
      callToggleButton(12);

      jQuery('#' + buttonId).trigger('change');

      waitsFor(function() {
        return post_returned === true;
      });
    });
  });
});