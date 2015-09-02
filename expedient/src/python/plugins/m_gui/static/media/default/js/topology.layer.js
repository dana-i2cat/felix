function layer_object(param)
{
	var networks = param.networks,
	    pad = 5,
	    height = param.height,
      width = param.width,
      layername = param.layername,
      y = param.y,
      tn_view = (typeof param.tn === "undefined")?false:true,
      tn_height = (tn_view == false)?0:param.tn.height;

	//Islands area generation
	var nx = networks,
	    ny = 1,
	    foci_layer = [];

	var aw = Math.floor((width-(nx+1)*pad)/nx),
	    ah = Math.floor((height-tn_height-(ny+1)*pad)/ny);

	var nodeInitialPos = [];
	var dataislands_layer = [];
	var datatns = [];
	var svg_layer;
	var islands;
	var iellipses;
	var ilabels;
	var tns;

	this.nodes;
	this.links;
	this.links_popup;
	this.node;
	this.link;
	this.link_popup;

	var islandsLocs = []

	for (i=0; i<networks; i++)
	{
		tx0 = pad + (pad + aw)*(Math.floor(i%nx));
		ty0 = pad + (pad + ah)*(Math.floor(i/nx));
		foci_layer[i] = {x0: tx0, x1: tx0 + aw, y0: ty0, y1: ty0 + ah};
		foci.push(foci_layer[i]);
	}

	this.redraw = function(trans, cur_zoom)
	{
		svg_layer.transition()
			.duration(500)
			.attr('x', function(d){ return d.x; })
			.attr('y', function(d){ return d.y; })
			.attr("transform", "translate(" + trans +")" + "scale(" + cur_zoom + ")");
	};

	this.dragMap = function(d, posx, posy, cur_zoom)
	{
		svg_layer.attr('x', function(d) { return d.x; })
			.attr('y', function(d) { return d.y; })
			.attr("transform", "translate(" + posx + "," + posy + ") scale (" + cur_zoom + ")")
	};

	this.setdata = function(data)
	{
		this.nodes = data.nodes;
		this.links = data.links;
		this.links_popup = data.links_popup;

		// Set color for each node
		SetNodeColor(this.nodes);
		SetLinkColor(this.links_popup);
	};

	this.setlocation = function(dataislands)
	{
		for (i = 0; i<= networks; i++)
		{
			islandsLocs[i] = EMPTY_ISLAND;
		}
		for (i = 0; i< this.nodes.length; i++){
			nodeInitialPos[i] = [this.nodes[i].x, this.nodes[i].y];
			if (islandsLocs[this.nodes[i].group] == EMPTY_ISLAND){
				islandsLocs[this.nodes[i].group] = this.nodes[i].locationName;
			}
		}

		// cover the all islands
		var aw_physical = Math.floor((width-(nIslands+1)*pad)/nIslands);
	  var ah_physical = Math.floor((height*.8-(ny+1)*pad)/ny);
		var left_edge_first_island = (pad+(pad+aw_physical))/2 - (aw_physical/2 + ah_physical/2)/2
		switch (layername)
		{
		case "physical":
			for (i = 0; i < networks; i++)
			{
				dataislands_layer[i] = {rx: (aw/2 + ah/2)/2, ry: ah/2, cx:(foci_layer[i].x0+foci_layer[i].x1)/2, cy:(foci_layer[i].y0+foci_layer[i].y1)/2, group: i+1, location: islandsLocs[i+1]};
				dataislands.push(dataislands_layer[i]);
			}
			if (tn_view == true)
			{
				var nx_tn = 1;
				var aw_tn = Math.floor((width-(nx_tn+1)*pad)/nx_tn),
				    ah_tn = Math.floor((tn_height-(ny+1)*pad)/ny);
				tx0 = pad + (pad + aw_tn)*(Math.floor(nx_tn%nx_tn));
				ty0 = height-tn_height + pad;
				var cx = (tx0+tx0+aw_tn)/2;
				var cy = (ty0+ty0+ah_tn)/2;
				datatns[0] = {rx: cx - left_edge_first_island , ry: ah_tn/2, cx:cx, cy:cy, group: networks+1, location: "tn"};
			}
			break;
		case "slice":
			var cx = (foci_layer[0].x0+foci_layer[0].x1)/2;
			var cy = (foci_layer[0].y0+foci_layer[0].y1)/2;
			dataislands_layer[0] = {rx: cx - left_edge_first_island , ry: ah/2, cx:cx, cy:cy, group: 0, location: islandsLocs[0]};
			dataislands.push(dataislands_layer[0]);
			break;
		}
	};

	this.genarate = function(svg)
	{
		svg_layer = svg.append("svg")
			.attr("y", y)
			.attr("width", width)
			.attr("height", height)
			.append("g")

		// islands
		islands = svg_layer.selectAll(".island")
			.data(dataislands_layer)
			.enter().append("g")
			.attr("class", "island")

		iellipses = islands.append("ellipse")
			.attr("rx", function(d) { return d.rx; })
			.attr("ry", function(d) { return d.ry; })
			.attr("cx",function(d) { return d.cx; })
			.attr("cy", function(d) { return d.cy; })
			.style("fill", function(d) { return color(d.group%(nNetworks)); })
			.style("stroke", function(d) { return color(d.group%(nNetworks));}) 
			.style("opacity", 0.3)
			.style("stroke-opacity", 0.7)

		ilabels = islands.append("text")
			.attr("text-anchor", "middle")
			.attr("y", function(d){ return d.cy + d.ry*0.9})
			.attr("x", function(d){ return d.cx})
			.attr("font-color", function(d) { return d3.rgb(color(d.group%(nNetworks))).darker(5); })
			.style("opacity",1)
			.style("cursor", "default")
			.text(function(d) { return d.location });

		// tns
		if (tn_view == true)
		{
			tns = svg_layer.selectAll(".tn")
				.data(datatns)
				.enter().append("g")
				.attr("class", "tn")

			tns.append("ellipse")
				.attr("rx", function(d) { return d.rx; })
				.attr("ry", function(d) { return d.ry; })
				.attr("cx",function(d) { return d.cx; })
				.attr("cy", function(d) { return d.cy; })
				.style("fill", function(d) { return color(d.group%(nNetworks)); })
				.style("stroke", function(d) { return color(d.group%(nNetworks));}) 
				.style("opacity", 0.3)
				.style("stroke-opacity", 0.7)

			tns.append("text")
				.attr("text-anchor", "middle")
				.attr("y", function(d){ return d.cy + d.ry*0.9})
				.attr("x", function(d){ return d.cx})
				.attr("font-color", function(d) { return d3.rgb(color(d.group%(nNetworks))).darker(5); })
				.style("opacity", 1)
				.style("cursor", "default")
				.text(function(d) { return d.location });
		}

		// links
		this.link = svg_layer.selectAll(".link")
			.data(this.links)
			.attr("class", "link")
			.enter().append("line")
			.style("stroke", function(d)
			{
				var stroke = "#ccc";
				switch(d.status)
				{
				case "UP":
					break;
				case "DOWN":
					stroke = "#FF0000"
					break;
				}
				return stroke;
			});

		switch (layername)
		{
		case "physical":
			break;
		case "slice":
			// popup links
			this.link_popup = svg_layer.selectAll(".link_popup")
				.data(this.links_popup)
				.attr("class", "link_popup")
				.enter().append("line")
				.style("stroke-width", "10px")
				.style("opacity", "0.0")
				.on("mouseover", function (d, i){
					selectLink(d);
					showLinkTooltip("");
					$("#selected_node_info").html("Selected " + d.type + " link at " + d.locationName);
					$("#selected_node_info").css("background-color", d.color );
					$("#selected_node_info").css("text-shadow", "-3px 2px 4px #eee");
					$("#selected_node_info").show();
				})
				.on("mouseout", function(){
					$("#selected_node_info").css("background-color", "#ebf5ff");
					tooltip.hide();
				});
			break;
		}

		// nodes
		this.node = svg_layer.selectAll(".node")
			.data(this.nodes)
			.enter().append("g")
			.attr("class", "node")
			.attr("cursor", "move")
			.call(force.drag)
			.call(d3.behavior.drag()
			.on("dragstart", function(d, i, e) {
				d.fixed = false;
				force.stop();
			})
			.on("drag", function(d, i) {
				d.px += d3.event.dx;
				d.py += d3.event.dy;
				d.x += d3.event.dx;
				d.y += d3.event.dy;
				tick(layername);
			})
			.on("dragend", function(d, i) {
				tick(layername);
				force.stop();
			})
		);

		this.node.append("circle")
			.attr("r", function(d) { return d.radius; })
			.style("stroke", function(d){return getBaseNodeColor(d);})
			.style("fill", function(d){return getBaseNodeColor(d);});

		this.node.append("image")
			.attr("xlink:href", function(d) { return d.image; })
			.attr("x", -8)
			.attr("y", -8)
			.attr("width", 16)
			.attr("height", 16)
			.attr("opacity", function(d) { return d.available=="False"?0.8:1; })

		this.node.append("text")
			.attr("dx", 12)
			.attr("dy", ".35em")
			.text(function(d) { return d.name });

		this.node.on("mouseover", function (d, i){
				if (d.type != "tn")
				{
		      // Ugly hack to decode HTML
					selectNode(d, layername);
					tooltip.show($('<div/>').html(d.description).text());
					$("#selected_node_info").html("Selected " + d.type + " at " + d.locationName);
					$("#selected_node_info").css("background-color", d.color );
					$("#selected_node_info").css("text-shadow", "-3px 2px 4px #eee");
					$("#selected_node_info").show();
				}})
			.on("mouseout", function(){
				$("#selected_node_info").css("background-color", "#ebf5ff");
        tooltip.hide();
			});
	};

	this.forceon = function()
	{
		// nodes
		switch (layername)
		{
		case "physical":
			this.node.each(this.collide(.5));
			break;
		case "slice":
			break;
		}
		this.node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")";})
			.attr("cx", function(d) { return d.x; })
			.attr("cy", function(d) { return d.y; });

		// links
		switch (layername)
		{
		case "physical":
			this.link.attr("x1", function(d) { return d.source.x; })
				.attr("y1", function(d) { return d.source.y; })
				.attr("x2", function(d) { return d.target.x; })
				.attr("y2", function(d) { return d.target.y; });
			break;
		case "slice":
			// slice's link are not set position
			var nodes = this.nodes;
			this.link.attr("x1", function(d) { return nodes[d.source].x; })
				.attr("y1", function(d) { return nodes[d.source].y; })
				.attr("x2", function(d) { return nodes[d.target].x; })
				.attr("y2", function(d) { return nodes[d.target].y; });
			this.link_popup.attr("x1", function(d) { return nodes[d.source].x; })
				.attr("y1", function(d) { return nodes[d.source].y; })
				.attr("x2", function(d) { return nodes[d.target].x; })
				.attr("y2", function(d) { return nodes[d.target].y; });
			break;
		}
	}

	this.tick = function()
	{
		// nodes
		switch (layername)
		{
		case "physical":
			this.node.each(this.collide(.5));
			break;
		case "slice":
			break;
		}
		this.node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")";})
			.attr("cx", function(d) { return d.x; })
			.attr("cy", function(d) { return d.y; });

		// links
		switch (layername)
		{
		case "physical":
			this.link.attr("x1", function(d) { return d.source.x; })
				.attr("y1", function(d) { return d.source.y; })
				.attr("x2", function(d) { return d.target.x; })
				.attr("y2", function(d) { return d.target.y; });
			break;
		case "slice":
			// slice's link are not set position
			var nodes = this.nodes;
			this.link.attr("x1", function(d) { return nodes[d.source].x; })
				.attr("y1", function(d) { return nodes[d.source].y; })
				.attr("x2", function(d) { return nodes[d.target].x; })
				.attr("y2", function(d) { return nodes[d.target].y; });
			this.link_popup.attr("x1", function(d) { return nodes[d.source].x; })
				.attr("y1", function(d) { return nodes[d.source].y; })
				.attr("x2", function(d) { return nodes[d.target].x; })
				.attr("y2", function(d) { return nodes[d.target].y; });
			break;
		}
	}

	this.animate = function()
	{
		iellipses.attr("rx", function(d) { return d.rx; })
			.style("display","block")
			.attr("ry", function(d) { return d.ry; })
			.attr("cx",function(d) { return d.cx; })
			.attr("cy", function(d) { return d.cy; })
			.style("fill", function(d) { return color(d.group%nNetworks); })
			.style("stroke", function(d) { return color(d.group%nNetworks);}) 
			.style("opacity", 0.3)
			.style("stroke-opacity", 0.7)

		ilabels.attr("text-anchor", "middle")
			.attr("y", function(d){ return d.cy + d.ry*0.9})
			.attr("x", function(d){ return d.cx})
			.attr("font-color", function(d) { return d3.rgb(color(d.group%nNetworks)).darker(5); })
			.style("opacity",1)
			.text(function(d) { return d.location });

		if (allways_domain != "True")
		{
			iellipses.transition()
				.style("stroke-width",3)
				.style("stroke", function(d) { return d3.rgb(color(d.group%nNetworks)).brighter(10);})
				.duration(1500)
			iellipses.transition()
				.delay(1500)
				.style("opacity",0)
				.duration(3000)
			ilabels.transition()
				.delay(1500)
				.style("opacity",0)
				.duration(3000);
		}
	}

	this.collide = function(alpha) {
	  var quadtree = d3.geom.quadtree(this.nodes);
	  return function(d) {
	    var r = d.radius + radius.domain()[1] + padding,
	        nx1 = d.x - r,
	        nx2 = d.x + r,
	        ny1 = d.y - r,
	        ny2 = d.y + r;
	    quadtree.visit(function(quad, x1, y1, x2, y2) {
	      if (quad.point && (quad.point !== d)) {
	        var x = d.x - quad.point.x,
	            y = d.y - quad.point.y,
	            l = Math.sqrt(x * x + y * y),
	            r = d.radius + quad.point.radius + (d.color !== quad.point.color) * padding;
	        if (l < r) {
	          l = (l - r) / l * alpha;
	          d.x -= x *= l;
	          d.y -= y *= l;
	          quad.point.x += x;
	          quad.point.y += y;
	        }
	      }
	      return x1 > nx2
	          || x2 < nx1
	          || y1 > ny2
	          || y2 < ny1;
	    });
	  };
	};

};
