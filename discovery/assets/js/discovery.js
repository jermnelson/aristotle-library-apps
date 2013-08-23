function DiscoveryViewModel() {
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
  self.searchType = ko.observable("kw");
  self.searchRLSP = function() {
    var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var data = {
      csrfmiddlewaretoken: csrf_token,
      q_type: self.searchType(),
      q: self.searchQuery()
    }
    $.post('/apps/discovery/search', 
           data,
           function(server_response) {
            if(server_response['result'] != "error") { 
             self.searchResults.removeAll();
             if(server_response["works"].length > 0) {
               self.showResults(true);
               for(work_num in server_response['works']) {
                 var work = server_response['works'][work_num];
                 self.searchResults.push(work);
               } 
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



function displaySimpleGraph(json_resources) {
 var svg = d3.select("#discovery-results").append("svg:svg");
 svg.attr("width",200).attr("height",280);
 var circle = svg.append("svg:circle")
              .attr("cx",40)
	      .attr("cy",50)
	      .attr("r",12)
	      .attr("fill","#aaa")
              .attr("stroke","#666")
              .attr("stroke-width","1.5px");
}

function displayForceDirectedGraph(json_resources) {
  var width = 960, height = 500;

  var color = d3.scale.category20();

  var force = d3.layout.force()
      .charge(-120)
      .linkDistance(30)
      .size([width, height]);

var svg = d3.select("").append("svg")
    .attr("width", width)
    .attr("height", height);

d3.json(json_resources, function(error, graph) {
  force
      .nodes(graph.nodes)
      .links(graph.links)
      .start();

  var link = svg.selectAll("line.link")
      .data(graph.links)
    .enter().append("line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return Math.sqrt(d.value); });

  var node = svg.selectAll("circle.node")
      .data(graph.nodes)
    .enter().append("circle")
      .attr("class", "node")
      .attr("r", 5)
      .style("fill", function(d) { return color(d.group); })
      .call(force.drag);

  node.append("title")
      .text(function(d) { return d.name; });

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });
});
}
