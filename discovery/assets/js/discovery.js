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
