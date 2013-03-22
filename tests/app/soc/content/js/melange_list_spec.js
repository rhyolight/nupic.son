describe('melange list', function() {
   beforeEach(function() {
     jasmine.getFixtures().fixturesPath = 'tests/app/soc/content/js';
     loadFixtures('melange_list_fixture.html');
   });
   it('should be defined', function(){
      expect(melange.list).toBeDefined();
   });
});