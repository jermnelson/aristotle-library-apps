function loadDetail(slide_id) {
  alert("Slides are " + slides);
  var slide = slides[slide_id];
  
  $('#main-content h1').attr('text',slide['title']);

}

function frbrDisplay() {
  var paper = Raphael("frbr-redis-ds-illustration");

  paper.clear();
  var work = paper.rect(10,10,40,40);
  work.attr("stroke","#600");
  //var expr = paper.rect(15,15,45,45);
  //var manifestation = paper.rect(20,20,50,50);
  //var item = paper.rect(25,25,55,55);
  
}

function salvoAnimation() {
 $('#brand-remix').hide();
	
}

function salvoAnimation2(action) {
 if(action == 'start') {
   $(".content").css('opacity',0.1);
   $("footer").css('opacity',0.1);
   $('#charles-stross-galatic-cataloger').show('slow');
 } else {
   $('#charles-stross-galatic-cataloger').fadeOut('slow');
   $(".content").css('opacity',1);
   $("footer").css('opacity',1);
 }
}

