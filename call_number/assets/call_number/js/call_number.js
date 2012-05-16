function BrowseDisplay(call_number) {
  var data = 'call_number=' + call_number;
  $.ajax({
    url:'/apps/call_number/json/browse',
    data:data,
    success: function(response) {
      $('#call-number-browser').replaceWith(response['html']);
    }
  });
}

// Function copied from https://gist.github.com/1848558
function CNtypeahead(ev) {
  ev.stopPropagation();
  ev.preventDefault();

  if($.inArray(ev.keyCode,[40,38,9,13,27]) === -1) {
    var self = $(this);
    self.data('typeahead').source = [];
    if( !self.data('active') && self.val().length > 0) {

      self.data('active',true);

      var data = 'q=' + $(this).val();

      $.ajax({
        url:'/call_number/json/search',
        data: data,
        success: function(response) {
          self.data('typeahead').source = response['result'];
          self.trigger('keyup');
          self.data('active', false);
          if($.inArray('record',response) > 0) {
            BrowseDisplay(token);
          }
          
        }
      }); 
    }
  }
}
