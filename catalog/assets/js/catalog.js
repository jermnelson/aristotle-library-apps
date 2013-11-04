function CatalogViewModel() {
  self = this;
  self.contextHeading = ko.observable("Default Content Heading");

  self.searchChoices = ko.observableArray([
   { name: "Keyword", action: "kwSearch" },
   { name: "Author", action: "auSearch" },
   { name: "Title", action: "tSearch" },
   { name: "Journal Title", action: "jtSearch" },
   { name: "LC Subject", action: "lcSearch" },
   { name: "Medical Subject", action: "medSearch" },
   { name: "Children's Subject", action: "NoneSearch" },
   { name: "LC Call Number", action: "lccnSearch" },
   { name: "Gov Doc Number", action: "govSearch" },
   { name: "ISSN/ISBN", action: "isSearch" },
   { name: "Dewey Call Number", action: "dwSearch" },
   { name: "Medical Call Number", action: "medcSearch" },
   { name: "OCLC Number", action: "oclcSearch" }]);
 
  self.searchQuery = ko.observable();

  // Handlers for Search
  self.searchResults = ko.observableArray(); 

  self.runSearch = function() {
    var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var data = {
      csrfmiddlewaretoken: csrf_token,
//      q_type: self.searchType(),
      q: self.searchQuery()
    }
    $.post('/apps/catalog/search', 
           data,
           function(server_response) {
            if(server_response['result'] != "error") { 
             self.searchResults.removeAll();
            self.resultSize(server_response["total"]);
            if(server_response["total"] < 5) {
              self.resultEndSlice(server_response["total"]);
            }             
             if(server_response["instances"].length > 0) {
               self.showResults(true);
               for(instance_num in server_response['instances']) {
                 var instance = server_response['instances'][instance_num];
                 self.searchResults.push(instance);
               } 
              $(".instance-action").popover({ html: true });
             } else {
              self.contextHeading("Search Returned 0 Works"); 
             }
           } else {
             self.contextHeading("Error with Search " + self.searchQuery());
             self.searchQuery(server_response['text']);
             alert("Error with search\n" + server_response['text']);
           }
        });

  }

  // Handlers for Results
  self.displayFilters = function() {
   if(self.showFilters() == true) {
     self.showFilters(true);
   } else {
     self.showFilters(false);
   }

  }

  self.findInLibrary = function(instance) {
    var info = "<p>" + instance['title'] + " is located at " + instance['instanceLocation'] + "</p>";
    $('#' + instance['instance_key']).popover({content: info, html: true}); 
    $('#' + instance['instance_key']).popover('show');
    alert("Item title is " + instance['title']);

  }

  self.itemDetails = function(instance) {
    alert("Should display instance popover for " + instance['instance_key']);

  }

  self.nextResultsPage = function() {
   var start_position = self.resultStartSlice();
   var end_position = self.resultEndSlice();
   for(i=start_position; i<= self.resultEndSlice(); i++) {
      self.searchResults()[i-1]['isActive']= false;
   }
   for(i=end_position+1; i <= end_position+6; i++) {
      self.searchResults()[i-1]['isActive'] = true;

   }
  }

  self.prevResultsPage = function() {

  }

  self.resultPaneSize = ko.observable("col-md-10");

  self.resultStartSlice = ko.observable(1);
  self.resultEndSlice = ko.observable(5);
  self.resultSize = ko.observable(5);

  self.showFilters = ko.observable(false);
  self.showResults = ko.observable(false);

  self.auSearch = function() {
  }
  self.childSubjectSearch = function() {
  }
  self.dwSearch = function() {
  }
  self.govSearch = function() {
  }
  self.isSearch = function() {
  }
  self.jtSearch = function() {

  }
  self.kwSearch = function() {
  }
  self.lcSearch = function() {

  }
  self.lccnSearch = function() {

  }
  self.medSearch = function() {

  }
  self.medcSearch = function() {

  }
  self.oclcSearch = function() {

  }
  self.tSearch = function() {

  }
}

