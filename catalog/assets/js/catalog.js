function CatalogViewModel() {
  self = this;
  self.contextHeading = ko.observable("Default Content Heading");
  self.errorMessage = ko.observable();
  self.pageNumber = ko.observable(1);
  self.activeNext = ko.observable(true);
  self.activePrevious = ko.observable(true);
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
  self.showError = ko.observable(false);

  // Handlers for Search
  self.searchResults = ko.observableArray(); 

  self.newSearch = function() {
   self.pageNumber(1);
   self.runSearch();
  }

  self.runSearch = function() {
    self.showError(false);
    self.searchResults.removeAll();
    var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var data = {
      csrfmiddlewaretoken: csrf_token,
//      q_type: self.searchType(),
      q: self.searchQuery(),
      page: self.pageNumber()
    }
    $.post('/apps/catalog/search', 
           data,
           function(server_response) {
            if(server_response['result'] == 'error'){
             self.showError(true);
             self.errorMessage("Error with search: " + server_response['text']);
             return;
            }
            
            self.resultSize(server_response["total"]);
            if(server_response["total"] < 5) {
              self.resultEndSlice(server_response["total"]);
              self.activeNext(false);
            } else {
               var calcEndSlice = parseInt(server_response['page']) * 5;
               if(calcEndSlice >= parseInt(server_response["total"])) {
                 calcEndSlice = parseInt(server_response["total"]);
                 self.activeNext(false);
               } else {
                 self.activeNext(true);
               }
               self.resultEndSlice(calcEndSlice);  
            }

            var startSlice = parseInt(self.resultEndSlice()) - 5;
            if(startSlice < 1) { 
              startSlice = 1; 
              self.activePrevious(false);
            } else {
              self.activePrevious(true);
            }
            self.resultStartSlice(startSlice); 
            self.pageNumber(server_response['page']); 
                       
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
   var current_page = parseInt(self.pageNumber());
   self.pageNumber(current_page + 1);
   self.runSearch();
    
  }

  self.prevResultsPage = function() {
   self.pageNumber(parseInt(self.pageNumber()) - 1);
   self.runSearch();
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

