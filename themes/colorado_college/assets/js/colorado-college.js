var  DiscoveryViewModel = function () {
  var self = this;
  self.DiscoveryHome = ko.observable(true);
  self.QueryPhrase = ko.observable();
  self.QueryType =  ko.observable();
  self.ResultsMessage = ko.observable([]);
  self.SearchResults = ko.observableArray();
  self.SearchResultsPane = ko.observable(false);
  self.SearchSubmit = function() {
    var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    self.SearchResults([]);
    var data = { 
      csrfmiddlewaretoken: csrf_token,
      q_type: self.QueryType(),
      q: self.QueryPhrase()};
       
    $.ajax({
      url : "/apps/discovery/search",
      type : "POST",
      data : data,
      dataType : "json",
      success: function(data) {
        self.DiscoveryHome(false); 
        self.SearchResultsPane(true);
        var message = "Results for <em>" + data['query'] + '</em>';
        self.ResultsMessage(message);
        for(i in data['works']) {
          var work = data['works'][i];
          self.SearchResults.push(work);
        }
      }
     });
  };

} 
