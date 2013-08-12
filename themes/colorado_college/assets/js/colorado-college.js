var  DiscoveryViewModel = function () {
  var self = this;
  self.DiscoveryHome = ko.observable(true);
  self.DisplayListButton = ko.observable("btn"); 
  self.DisplayThumbnailButton = ko.observable("btn disabled");
  self.QueryPhrase = ko.observable();
  self.QueryType = ko.observable();
  self.ResultsMessage = ko.observable([]);
  self.SearchResults = ko.observableArray();
  self.SearchResultsPane = ko.observable(false);
  self.SortByAlphaButton = ko.observable("btn");
  self.SortByRelevanceButton = ko.observable("btn disabled");
  self.SortByDateButton = ko.observable("btn");

  // Functions
  self.CloseThumbnail = function() {
    alert("Should close thumbnail");
  };

  self.DisplayList = function() {
   self.DisplayThumbnailButton("btn");
   self.DisplayListButton("btn disabled");
  };

  self.DisplayThumbnail = function() {
    self.DisplayThumbnailButton("btn disabled");
    self.DisplayListButton("btn");
  };

  
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
        var message = data['works'].length + " Results for <em>" + data['query'] + '</em>';
        self.ResultsMessage(message);
        for(i in data['works']) {
          var work = data['works'][i];
          self.SearchResults.push(work);
        }
      }
     });
  };
  self.SortByAlpha = function() {
    var results = self.SearchResults;
    results.sort(function(left,right) { return left.WorkTitle == right.WorkTitle ? 0: (left.WorkTitle < right.WorkTitle ? -1 : 1) });
    self.SortByAlphaButton("btn disabled");
    self.SortByRelevanceButton("btn");
    self.SortByDateButton("btn");
    
  }
  
  self.SortByDate = function() {
    self.SortByDateButton("btn disabled");
    self.SortByRelevanceButton("btn");
    self.SortByAlphaButton("btn"); 
  }

  self.SortByRelevance = function() {
    self.SortByDateButton("btn");
    self.SortByRelevanceButton("btn disabled");
    self.SortByAlphaButton("btn"); 

  }

}

var CreativeWorkViewModel = function() {
  var self = this;
  self.csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value; 

  self.AnnotateWork = function() {
    $('#annotateEntity').modal(show=true);
  }
  
  self.AnnotationBody = ko.observable();
  self.AnnotationType = ko.observable();
  self.IsPrivateAnnotation = ko.observable();

  self.SaveAnnotation = function() {
    var data = {
      body: self.AnnotationBody(),
      type: self.AnnotationType(),
      is_private: self.IsPrivateAnnotation()};
    alert("In save Annotation " + data);

  }

  self.SaveWork = function() {
    var data = {
      action: 'patron_annotation',
      key: work_redis_key,
      csrfmiddlewaretoken: self.csrf_token};
    $.ajax({
      url: '/apps/discovery/save',
      data: data,
      type: 'POST',
      dataType: 'json',
      success: function(data) {
        alert(data['msg']);
      }
      
    });
  }

}
