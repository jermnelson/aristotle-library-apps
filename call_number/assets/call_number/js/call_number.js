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

function CallNumberItem(bib_link,title,authors,location,call_number) {
  this.bib_link = bib_link;
  this.authors = authors;
  this.call_number=call_number;
  this.location=location;
  this.title = title;
}

function CallNumberAppViewModel() {
  var self = this;

  self.browseNext = function() {
    var last_position = self.nextItems().length -1;
    var data = 'q=' +  self.nextItems()[last_position].call_number+ "&type=" + self.chosenNumberType()["number_type"];
    $.ajax({
      data: data,
      dataType: 'json',	    
      url: '/apps/call_number/json/widget_search',
      success: function(data) {
        self.updateWidget(data);
      }
    });

  }

  self.browsePrevious = function() {
    var data = 'q=' +  self.previousItems()[0].call_number+ "&type=" + self.chosenNumberType()["number_type"];
    $.ajax({
      data: data,
      dataType: 'json',	    
      url: '/apps/call_number/json/widget_search',
      success: function(data) {
        self.updateWidget(data);
      }
    });

  }

  self.callNumberTypes = [
    { name: "LOC Call Number", number_type: "lccn" },
    { name: "Government Call Number", number_type: "govdoc" },
    { name: "Local Call Number", number_type: "local"}, 
    { name: "ISBN", number_type: "isbn" },
    { name: "ISSN", number_type: "issn" }]; 

  self.chosenNumberType = ko.observable();
  self.currentTitle = ko.observable();
  self.currentAuthors = ko.observable();
  self.currentCallNumber = ko.observable()
  self.newSearchQuery = ko.observable(); 

  self.nextItems = ko.observableArray([]);
  self.previousItems = ko.observableArray([]);


  self.loadCallNumber = function(call_number,num_type) {
   var data = 'q=' + call_number + "&type=" + num_type;
    $.ajax({
      data: data,
      dataType: 'json',	    
      url: '/apps/call_number/json/widget_search',
      success: function(data) {
        self.updateWidget(data);
      }
    });
  }

  self.searchCallNumber = function() {
    self.loadCallNumber(ko.toJS(self.newSearchQuery()),self.chosenNumberType()["number_type"]);
  }


 self.updateWidget = function(data) {
   self.nextItems.removeAll();
   self.previousItems.removeAll();
   var previousRecs = data['previousRecs'];
   if(previousRecs) {
     for(row in previousRecs) {
       rec = previousRecs[row];
       var bib_link = "/apps/discovery/" + rec['work_key'];
       self.previousItems.push(new CallNumberItem(bib_link,rec['title'],rec['authors'],' ',rec['call_number']));
     }
   }
   var current = data['current'];
   self.currentTitle(current['title']);
   self.currentAuthors(current['authors'])
   self.currentCallNumber(current['call_number']);
   var nextRecs = data['nextRecs'];
   if(nextRecs) {
     for(row in nextRecs) {
       rec = nextRecs[row];
       var bib_link = "/apps/discovery/" + rec['work_key'];
       self.nextItems.push(new CallNumberItem(bib_link,rec['title'],rec['authors'],' ',rec['call_number']));
     }
   }
 }


}
