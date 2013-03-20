describe('melange', function() {
   beforeEach(function() {
     jasmine.getFixtures().fixturesPath = 'tests/app/soc/content/js';
     loadFixtures('melange_fixture.html');
   });
   it('should be defined', function(){
      expect(melange).toBeDefined();
   });
});