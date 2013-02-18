function DBFinderAppViewModel() {
  var self = this;

  self.subjectSelect = ko.observable();
  
  self.chosenSubject = function() { alert("In chosenSubject"); }
 

}
