var svg = d3.select("svg#sankey"),
  width = +svg.attr("width"),
  height = +svg.attr("height");

var metasvg = d3.select("svg#metapaths"),
  width = +svg.attr("width"),
  height = +svg.attr("height");

var formatNumber = d3.format(",.0f"),
  format = function(d) {
    return formatNumber(d) + " TWh";
  },
  color = d3.scaleOrdinal(d3.schemeCategory10);

var sankey = d3.sankey()
  .nodeWidth(15)
  .nodePadding(10)
  .extent([
    [1, 1],
    [width - 200, height - 6]
  ])
  .iterations(0)
  .nodeId(function(d) {
    return d.name
  });

var link = svg.append("g")
  .attr("class", "links")
  .attr("fill", "none")
  .attr("stroke", "#000")
  .attr("stroke-opacity", 0.4)
  .selectAll("path");

var node = svg.append("g")
  .attr("class", "nodes")
  .attr("font-family", "sans-serif")
  .attr("font-size", 10)
  .selectAll("g");

d3.json("/data/test-metapaths.json", function(error, metapaths){
    console.log((metapaths))
    var metapaths = {
'index':	0,
'path_string':	'DISO-DISO-DISO-PHYS',
'count':	1640,
'sample_path':	['Alacrima',
 'Familial dysautonomia',
 'Elevated serum creatinine',
 'Post translational protein modification'],
'path_type':	['DISO', 'DISO', 'DISO', 'PHYS']
}
  // metapaths = metapaths.filter(function(d) { return d.query == 'alacrima:pathway_3'})
  // console.log(metapaths.query)

  // var metapaths = metapaths.count
    console.log((metapaths))
  var x_pos = 150
  var x_width = x_pos*0.65
  var y_pos = 25

  metasvg
  .selectAll('.example')
  .data(metapaths.sample_path)
  .enter().append('text.example')
  .attr('x', function(d, i) { return i * x_pos})
  .attr('y', 100)
  .text(function(d) { return d})

  metasvg
  .selectAll('rect')
  .data(metapaths.path_type)
  .enter().append('rect.node-type')
  .attr('x', function(d, i) { return i * x_pos})
  .attr('width', x_width)
  .attr('y', 0)
  .attr('height', 50)

  metasvg
  .selectAll('text.node-type')
  .data(metapaths.path_type)
  .enter().append('text.node-type')
  .attr('x', function(d, i) { return i * x_pos + x_width/2})
  .attr('y', y_pos)
  .text(function(d) { return d})

  metasvg
  .selectAll('line.node-type')
  .data(metapaths.path_type)
  .enter().append('line.node-type')
  .attr('x1', function(d, i) { return i * x_pos + x_width })
  .attr('x2', function(d, i) { return (i + 1) * x_pos })
  .attr('y1', y_pos)
  .attr('y2', y_pos)
  .attr("marker-end", "url(#triangle)");

  metasvg
  .selectAll('line.example')
  .data(metapaths.sample_path)
  .enter().append('line.example')
  .attr('x1', function(d, i) { return i * x_pos + x_width })
  .attr('x2', function(d, i) { return (i + 1) * x_pos })
  .attr('y1', 100)
  .attr('y2', 100)
  .attr("marker-end", "url(#triangle)");

  metasvg.append("svg:defs").append("svg:marker")
      .attr("id", "triangle")
      .attr("refX", 12)
      .attr("refY", 6)
      .attr("markerWidth", 30)
      .attr("markerHeight", 30)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M 0 0 12 6 0 12 3 6");
})

d3.json("/data/sm.json", function(error, paths) {
  d3.json("/data/test.json", function(error, test) {
    if (error) throw error;
    // console.log(paths['NFE2L1:ENGASE'])

    console.log(test)
    // path1 = paths['NFE2L1:ENGASE']

    // TODO: put everything into a dict and then join?
    var nested = {};

//     var ngrps = _.groupBy(path1.nodes, 'id')
//     nested['nodes'] = _.map(ngrps, function(group) {
//       return {
//         node_id: group[0].node_id,
//         node_name: group[0].node_name,
//         node_type: group[0].node_type,
//         n: group.length
//       };
//     })
//
//     var egrps = _.groupBy(path1.links, 'source_id')
// console.log('edges')
//     console.log(egrps)
//     nested['links'] = _.map(egrps, function(group) {
//       return {
//         source_id: group[0].source_id,
//         target_id: group[0].target_id
//       };
//     })
//
//     console.log(nested)

    energy = test;
    // energy['NGLY1-ENGASE']

    sankey(energy)
    console.log(energy)

    link = link
      .data(energy.links)
      .enter().append("path")
      .attr("d", d3.sankeyLinkHorizontal())
      .attr('opacity', 0.05)
      .attr("stroke-width", function(d) {
        return Math.max(1, d.width);
      });

    link.append("title")
      .text(function(d) {
        return d.source.name + " → " + d.target.name + "\n" + format(d.value);
      });

    node = node
      .data(energy.nodes)
      .enter().append("g");

    node.append("rect")
      .attr("id", function(d) {
        return d.name;
      })
      .attr("x", function(d) {
        return d.x0;
      })
      .attr("y", function(d) {
        return d.y0;
      })
      .attr("height", function(d) {
        return d.y1 - d.y0;
      })
      .attr("width", function(d) {
        if (d.n > 400) {
          return 15;
        } else {
          return d.n * .6;
        }
      })
      // .attr("fill", function(d) { return color(d.name.replace(/ .*/, "")); })
      .attr("fill", function(d) {
        return '#ff6574';
      })
      .attr("stroke", "#000");

    node.append("text")
      .attr("x", function(d) {
        return d.x0 - 6;
      })
      .attr("y", function(d) {
        return (d.y1 + d.y0) / 2;
      })
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .text(function(d) {
        return d.name;
      })
      .filter(function(d) {
        return d.x0 < width / 2;
      })
      .attr("x", function(d) {
        return d.x1 + 6;
      })
      .attr("text-anchor", "start");

    node.append("title")
      .text(function(d) {
        return d.name + "\n" + format(d.value);
      });

    node.selectAll('text').on('click', function() {
      d3.select(this).classed('off', !d3.select(this).classed('off'))
    })

    node.selectAll('rect').on('click', function() {
      d3.select(this).classed('off', !d3.select(this).classed('off'))
    })

    node.selectAll('rect').on('mouseover', function() {
      sel_id = this.id;

      d3.selectAll('.links path')
        .filter(function(d) {
          return d.source.name == sel_id | d.target.name == sel_id;
        })
        .classed('highlight', true);

    }).on('mouseout', function() {
      sel_id = this.id;

      d3.selectAll('.links path')
        .filter(function(d) {
          return d.source.name == sel_id | d.target.name == sel_id;
        })
        .classed('highlight', false);

    })
  })
});

// // -- Determine sizing for plot
//
// // --- Setup margins for svg object
// var margin = {
//   top: 55,
//   right: 40,
//   bottom: 0,
//   left: 160
// }
//
// bufferH = 0; // number of pixels to space between vis and IC/EC nav bar
// maxH = window.innerHeight;
// // Available starting point for the visualization
// maxW = window.innerWidth;
// //
// // // Set max height to be the entire height of the window, minus top/bottom buffer
// var width = maxW - margin.left - margin.right,
//   height = maxH - margin.top - margin.bottom;
//
// var svg = d3.select('body')
// .append('svg')
//   .attr("width", width + margin.left + margin.right)
//   .attr("height", height + margin.top + margin.bottom)
//   .append("g.plot")
//   .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
//
// var plot = svg.selectAll('.plot');
//
// var sgraph = d3.sankey()
//     .nodeWidth(15)
//     .nodePadding(10)
//     .extent([[1, 1], [width - 1, height - 6]]);
//
//
//     var link = svg.append("g")
//         .attr("class", "links")
//         .attr("fill", "none")
//         .attr("stroke", "#000")
//         .attr("stroke-opacity", 0.2)
//       .selectAll("path");
//
//     var node = svg.append("g")
//         .attr("class", "nodes")
//         .attr("font-family", "Lato")
//         .attr("font-size", 10)
//       .selectAll("g");
//
//
//
// // !! DATA DEPENDENT SECTION
// // --- Load data, populate vis ---
//
//
// d3.json('/data/energy.json', function(error, graph) {
//     // graph.forEach(function(d) {
//     //   d.n = +d.n;
//     //   d.node_num = +d.node_num;
//     // })
//     console.log(graph)
// console.log()
//     sgraph
//     .nodes(graph.nodes)
//     .links(graph.links);
//
// console.log(sgraph)
//     node = node
//         .data(graph.nodes)
//         .enter().append("g").append("text")
//       .attr("x", function(d) { return d.x0 - 6; })
//       .attr("y", function(d) { return (d.y1 + d.y0) / 2; })
//       .attr("dy", "0.35em")
//       .attr("text-anchor", "end")
//       .text(function(d) { return d.name; })
//     .filter(function(d) { return d.x0 < width / 2; })
//       .attr("x", function(d) { return d.x1 + 6; })
//       .attr("text-anchor", "start");
//             link = link
//         .data(graph.links)
//         .enter().append("path")
//           .attr("d", d3.sankeyLinkHorizontal())
//           .attr("stroke-width", 10);
// })
