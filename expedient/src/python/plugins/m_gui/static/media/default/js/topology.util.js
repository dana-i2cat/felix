var selectedResource = {id: "", location: "", port: 0, layer: "", type: "", link: ""};

function selectNode(node, layer)
{
	selectedResource["id"] = node.nodeValue;
	selectedResource["location"] = node.location;
	selectedResource["type"] = node.type;
	selectedResource["layer"] = layer;
};

function selectLink(link)
{
	selectedResource["link"] = link;
}

function viewSDN(port)
{
	selectedResource["port"] = port;
  var param = sliceId + "," + selectedResource["id"] + "," + selectedResource["port"] + "," + 
              selectedResource["location"] + "," + 
              selectedResource["layer"] + "," + selectedResource["type"];
	var url = "../../../sdn/" + encodeURIComponent(param);

	var expand = document.getElementById("networkResources");
	if($("span", expand).attr("class") == "closed")
		expand.click();

	document.getElementById("frameNetwork").src = url;
	window.location.href = "#resourceDetails";
};

function viewCP()
{
  var param = sliceId + "," + selectedResource["id"] + "," + 
              selectedResource["location"] + "," +
              selectedResource["layer"] + "," + selectedResource["type"];
	var url = "../../../cp/" + encodeURIComponent(param);

	var expand = document.getElementById("computationalResources");
	if($("span", expand).attr("class") == "closed")
		expand.click();

	document.getElementById("frameCp").src = url;
	window.location.href = "#resourceDetails";
};

function viewSE(port)
{
	selectedResource["port"] = port;
  var param = sliceId + "," + selectedResource["id"] + "," + selectedResource["port"] + "," + 
              selectedResource["location"] + "," + 
              selectedResource["layer"] + "," + selectedResource["type"];
	var url = "../../../se/" + encodeURIComponent(param);

	var expand = document.getElementById("networkResources");
	if($("span", expand).attr("class") == "closed")
		expand.click();

	document.getElementById("frameNetwork").src = url;
	window.location.href = "#resourceDetails";
}

function makeDescription(param)
{
	var cnt;
	var ret = "";
	var lt = "&lt;";
	var gt = "&gt;";
	var br = lt + "br/" + gt;
	var div1_s = lt + "div id=\"grid\"" + gt;
	var tbl_s = lt + "table" + gt;
	var tbl_body_s = lt + "tbody" + gt;
	var tbl_body_e = lt + "/tbody" + gt;
	var tbl_e = lt + "/table" + gt;
	var div_e = lt + "/div" + gt + lt + "/div" + gt + br;
	switch (param.type)
	{
	case "switch":
		var dpid = "Switch Datapath ID:" + br + param.name + br + br;
		var port = "Switch Ports:" + br;
		var div2_s = lt + "div id=\"grid_data_network\"" + gt;
		var tbl_th = lt + "thead" + gt + lt + "tr" + gt + 
		                  lt + "th width=\"30px\"" + gt + "port" + lt + "/th" + gt + 
		                  lt + "th width=\"40px\"" + gt + "status" + lt + "/th" + gt + 
		                  lt + "th width=\"40px\"" + gt + "detail" + lt + "/th" + gt + 
		                  lt + "/tr" + gt + lt + "/thead" + gt;
		var tbl_data = "";
		for (cnt=0; cnt<param.ports.length; cnt++)
		{
			tbl_data += lt + "tr" + gt;
			tbl_data += lt + "td width=\"30px\"" + gt + param.ports[cnt].port + lt + "/td" + gt;
			if (param.ports[cnt].status == "DOWN")
				tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#FF0000\"" + gt + param.ports[cnt].status + lt + "/font" + gt + lt + "/td" + gt;
			else
				tbl_data += lt + "td width=\"40px\"" + gt + param.ports[cnt].status + lt + "/td" + gt;
			tbl_data += lt + "td width=\"40px\"" + gt + lt + "A href=" + "\"JavaScript:viewSDN('"+ param.ports[cnt].port +"')\"" + gt + "view" + lt + "/A" + gt + lt + "/td" + gt;
			tbl_data += lt + "/tr" + gt;
		}
		var con = "";
		var cons = "";
		if (param.connections.length > 0)
		{
			con = "Connections:";
			for (cnt=0; cnt<param.connections.length; cnt++)
			{
				cons += br + "Port " + param.connections[cnt].port + " to " + param.connections[cnt].destkind + br +
				        param.connections[cnt].dest;
	      cons += (param.connections[cnt].destkind == "switch" || param.connections[cnt].destkind == "se")?(" at port " + param.connections[cnt].destport):"";
			}
		}
		ret = dpid + port + 
		      div1_s + div2_s + tbl_s + tbl_th + tbl_body_s + tbl_data + tbl_body_e + tbl_e + div_e +
		      con + cons;
		break;
	case "se":
		var dpid = "Stitching Entity Name:" + br + param.name + br + br;
		var port = "Stitching Entity Ports:" + br;
		var div2_s = lt + "div id=\"grid_data_network\"" + gt;
		var tbl_th = lt + "thead" + gt + lt + "tr" + gt + 
		                  lt + "th width=\"30px\"" + gt + "port" + lt + "/th" + gt + 
		                  lt + "th width=\"40px\"" + gt + "status" + lt + "/th" + gt + 
		                  lt + "th width=\"40px\"" + gt + "detail" + lt + "/th" + gt + 
		                  lt + "/tr" + gt + lt + "/thead" + gt;
		var tbl_data = "";
		for (cnt=0; cnt<param.ports.length; cnt++)
		{
			tbl_data += lt + "tr" + gt;
			tbl_data += lt + "td width=\"30px\"" + gt + param.ports[cnt].port + lt + "/td" + gt;
			if (param.ports[cnt].status == "DOWN")
				tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#FF0000\"" + gt + param.ports[cnt].status + lt + "/font" + gt + lt + "/td" + gt;
			else
				tbl_data += lt + "td width=\"40px\"" + gt + param.ports[cnt].status + lt + "/td" + gt;
			tbl_data += lt + "td width=\"40px\"" + gt + lt + "A href=" + "\"JavaScript:viewSE('"+ param.ports[cnt].port +"')\"" + gt + "view" + lt + "/A" + gt + lt + "/td" + gt;
			tbl_data += lt + "/tr" + gt;
		}
		var con = "";
		var cons = "";
		if (param.connections.length > 0)
		{
			con = "Connections:";
			for (cnt=0; cnt<param.connections.length; cnt++)
			{
				cons += br + "Port " + param.connections[cnt].port + " to " + param.connections[cnt].destkind + br +
				        param.connections[cnt].dest;
	      cons += (param.connections[cnt].destkind == "switch" || param.connections[cnt].destkind == "se")?(" at port " + param.connections[cnt].destport):"";
			}
		}
		ret = dpid + port + 
		      div1_s + div2_s + tbl_s + tbl_th + tbl_body_s + tbl_data + tbl_body_e + tbl_e + div_e +
		      con + cons;
		break;
	case "server":
		var id = "Server:" + br + param.name + br + br;
		var div2_s = lt + "div id=\"grid_data_cp\"" + gt;
		var tbl_th = lt + "thead" + gt + lt + "tr" + gt + 
		                  lt + "th width=\"40px\"" + gt + "status" + lt + "/th" + gt + 
		                  lt + "th width=\"40px\"" + gt + "detail" + lt + "/th" + gt + 
		                  lt + "/tr" + gt + lt + "/thead" + gt;
		var tbl_data = "";
		tbl_data += lt + "tr" + gt;
		if (param.status == "DOWN")
			tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#FF0000\"" + gt + param.status + lt + "/font" + gt + lt + "/td" + gt;
		else
			tbl_data += lt + "td width=\"40px\"" + gt + param.status + lt + "/td" + gt;
		tbl_data += lt + "td width=\"40px\"" + gt + lt + "A href=" + "\"JavaScript:viewCP()\"" + gt + "view" + lt + "/A" + gt + lt + "/td" + gt;
		tbl_data += lt + "/tr" + gt;
		var vms = "No VMs in this Server" + br + br;
    if (param.vms.length != 0)
    {
      vms = "VMs (" + param.vms.length + "):" + br;
      for (cnt=0; cnt<param.vms.length; cnt++)
			{
				vms += (cnt != 0)?",":"";
        vms += param.vms[cnt].name;
			}
      vms += br + br;
    }
		var con = "";
		var cons = "";
		if (param.connections.length > 0)
		{
			con = "VMs Interfaces:";
			for (cnt=0; cnt<param.connections.length; cnt++)
			{
				cons += br + param.connections[cnt].name + " to " + param.connections[cnt].destkind + br +
				        param.connections[cnt].dest + " at port " + param.connections[cnt].destport;
			}
		}
		ret = id + 
		      div1_s + div2_s + tbl_s + tbl_th + tbl_body_s + tbl_data + tbl_body_e + tbl_e + div_e +
		      vms + con + cons;
		break;
	case "vm":
		var id = "VM:" + br + param.name + br + br;
		var div2_s = lt + "div id=\"grid_data_cp\"" + gt;
		var tbl_th = lt + "thead" + gt + lt + "tr" + gt + 
		                  lt + "th width=\"40px\"" + gt + "status" + lt + "/th" + gt + 
		                  lt + "th width=\"40px\"" + gt + "detail" + lt + "/th" + gt + 
		                  lt + "/tr" + gt + lt + "/thead" + gt;
		var tbl_data = "";
		tbl_data += lt + "tr" + gt;
		if (param.status == "DOWN")
			tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#FF0000\"" + gt + param.status + lt + "/font" + gt + lt + "/td" + gt;
		else
			tbl_data += lt + "td width=\"40px\"" + gt + param.status + lt + "/td" + gt;
		tbl_data += lt + "td width=\"40px\"" + gt + lt + "A href=" + "\"JavaScript:viewCP()\"" + gt + "view" + lt + "/A" + gt + lt + "/td" + gt;
		tbl_data += lt + "/tr" + gt;
		var con = "";
		var cons = "";
		if (param.connections.length > 0)
		{
			con = "Interfaces:";
			for (cnt=0; cnt<param.connections.length; cnt++)
			{
				cons += br + param.connections[cnt].name + " to " + param.connections[cnt].destkind + br +
				        param.connections[cnt].dest + " at port " + param.connections[cnt].destport;
			}
		}
		ret = id + 
		      div1_s + div2_s + tbl_s + tbl_th + tbl_body_s + tbl_data + tbl_body_e + tbl_e + div_e +
		      con + cons;
		break;
	}
	return ret;
}

function showLinkTooltip(param)
{
	var cnt;
	var ret = "";
	var lt = "&lt;";
	var gt = "&gt;";
	var br = lt + "br/" + gt;
	var div1_s = lt + "div id=\"grid\"" + gt;
	var tbl_s = lt + "table" + gt;
	var tbl_body_s = lt + "tbody" + gt;
	var tbl_body_e = lt + "/tbody" + gt;
	var tbl_e = lt + "/table" + gt;
	var div_e = lt + "/div" + gt + lt + "/div" + gt + br;
	var linkname = param
	var linkitem;

//	var id = "SDN link:" + br + param.name + br + br;
	var id = "SDN link:" + br + lt + "select id=\"sdn_link\" style=\"width:150px\" onchange=\"showLinkTooltip(value)\"" + gt;
	for (cnt=0; cnt<selectedResource["link"].linkItem.length; cnt++)
	{
		if (linkname == "")
			linkname = selectedResource["link"].linkItem[cnt].name;
		id += lt + "option value=" + selectedResource["link"].linkItem[cnt].name;
		if (linkname == selectedResource["link"].linkItem[cnt].name)
		{
	    id += " selected";
			linkitem = selectedResource["link"].linkItem[cnt];
		}
    id += gt + selectedResource["link"].linkItem[cnt].name + lt + "/option" + gt;
	}
	id += lt + "/select" + gt + br;
	id += "id:" + br + linkitem.id + br + br;

	var con = "Connections:" + br;
	var con1 = linkitem.source.name + " at port " + linkitem.source.port + " to " + br;
	var con2 = linkitem.target.name + " at port " + linkitem.target.port + br + br;

	var div2_s = lt + "div id=\"grid_data_link\"" + gt;
	var tbl_th = lt + "thead" + gt + lt + "tr" + gt + 
	                  lt + "th width=\"40px\"" + gt + "status" + lt + "/th" + gt + 
	                  lt + "th width=\"40px\"" + gt + "detail" + lt + "/th" + gt + 
	                  lt + "/tr" + gt + lt + "/thead" + gt;
	var tbl_data = "";
	tbl_data += lt + "tr" + gt;
	if (linkitem.status == "DOWN")
		tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#FF0000\"" + gt + linkitem.status + lt + "/font" + gt + lt + "/td" + gt;
	else
		tbl_data += lt + "td width=\"40px\"" + gt + linkitem.status + lt + "/td" + gt;
	tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#808080\"" + gt + "view" + lt + "/td" + gt;
	tbl_data += lt + "/tr" + gt;

	var demo = "for demo's information:" + br;
	var demo_div2_s = lt + "div id=\"grid_data_demo\"" + gt;
	var demo_tbl_th = lt + "thead" + gt + lt + "tr" + gt + 
	                  lt + "th colspan=2 width=\"80px\"" + gt + "link item" + lt + "/th" + gt + 
	                  lt + "th width=\"40px\"" + gt + "status" + lt + "/th" + gt + 
	                  lt + "/tr" + gt + lt + "/thead" + gt;
	var demo_tbl_data = "";
	for (cnt=0; cnt<linkitem.aggre_link.length; cnt++)
	{
		demo_tbl_data += lt + "tr" + gt;
		if (linkitem.aggre_link[cnt].interface != "")
		{
			demo_tbl_data += lt + "td width=\"40px\"" + gt + linkitem.aggre_link[cnt].name + lt + "/td" + gt;
			demo_tbl_data += lt + "td width=\"40px\"" + gt + linkitem.aggre_link[cnt].interface + lt + "/td" + gt;
		}
		else
		{
			demo_tbl_data += lt + "td colspan=2 width=\"80px\"" + gt + linkitem.aggre_link[cnt].name + lt + "/td" + gt;
		}
		if (linkitem.aggre_link[cnt].status == "DOWN")
			demo_tbl_data += lt + "td width=\"40px\"" + gt + lt + "font color=\"#FF0000\"" + gt + linkitem.aggre_link[cnt].status + lt + "/font" + gt + lt + "/td" + gt;
		else
			demo_tbl_data += lt + "td width=\"40px\"" + gt + linkitem.aggre_link[cnt].status + lt + "/td" + gt;
		demo_tbl_data += lt + "/tr" + gt;
	}

	ret = id + con + con1 + con2 +
	      div1_s + div2_s + tbl_s + tbl_th + tbl_body_s + tbl_data + tbl_body_e + tbl_e + div_e + 
	      demo + demo_div2_s + tbl_s + demo_tbl_th + tbl_body_s + demo_tbl_data + tbl_body_e + div_e;

	if (param == "")
		tooltip.show($('<div/>').html(ret).text());
	else
		tooltip.update($('<div/>').html(ret).text());
}

/* Useful functions*/
function SetNodeColor(nodes)
{
	nodes.forEach(function(d) {
		if (d.status == "DOWN") {
		    d.color = "#FF0000";
		}
		else if (d.available != "False") {
		    d.color = color(d.group%(nNetworks));
		} else {
		    d.color = "#CCC";
		}
	});
};

function SetLinkColor(links)
{
  if (links == undefined)
		return;
	links.forEach(function(d) {
		if (d.status == "DOWN") {
		    d.color = "#FF0000";
		}
		else {
		    d.color = color(d.group%(nNetworks));
		}
	});
};

/*
function getLinkStyle(d, attr){
        rsc_ids = d.value.split("-");
        if(attr=="click"){
                id0 = rsc_ids[0];
                id1 = rsc_ids[1];
                if (id1.indexOf("eth") != -1){
                     $(":checkbox#"+id0).click();
                }
                else{           
                if((! $(":checkbox#"+id0+":checked").length && ! $(":checkbox#"+id1+":checked").length) || ($(":checkbox#"+id0+":checked").length && $(":checkbox#"+id1+":checked").length)){
                        $(":checkbox#"+id0).click();
                        $(":checkbox#"+id1).click();
                }
                else if ($(":checkbox#"+id0+":checked").length){
                        $(":checkbox#"+id1).click();
                }
                else{
                        $(":checkbox#"+id0).click();    
                }
                }
        }else if(attr=="mouseover"){
                var values = {stroke: "#00BFFF", strokewidth: "2" };
                return values;
        }else{
		if( ($(":checkbox#"+rsc_ids[0]+":checked").length && rsc_ids[1].indexOf("eth") != -1) ||($(":checkbox#"+rsc_ids[0]+":checked").length && $(":checkbox#"+rsc_ids[1]+":checked").length)){
                        if (attr == "stroke")
                                return "#666";
                        else
                                return 2;
                }else{
                        if (attr == "stroke")
                                return "#ccc";
                        else
                                return 2;
                }
        }
}
*/
function getBaseNodeColor(d){
	var group = 0;
	group = d.group;
	var basecolor = d3.rgb(d.color.toString().toString());
	if ((d.color != "#FF0000") && (d.color != "#CCC"))
		basecolor = basecolor.darker(.15*group);
	return basecolor;
//	return d3.rgb(d.color.toString().toString()).darker(.15*group);
}
/*
function getNodeCircleStyle(d, attr){
        selected_len = $(":checkbox:checked.node_id_"+d.nodeValue).length;
        all_len = $(":checkbox:.node_id_"+d.nodeValue).length;
	selected_server = $(".server_node_"+d.nodeValue+".connected").length;
        if(attr == "drag"){
                return d3.rgb(d.color.toString()).brighter(5);
	}else if(attr=="click"){
		 if(selected_len == all_len) {
                        $(":checkbox:checked.node_id_"+d.nodeValue).click();
			return getBaseNodeColor(d);
                 }else{
                        $(":checkbox:not(:checked).node_id_"+d.nodeValue).click();
			return d3.rgb(d.color.toString()).darker(5);
                }
        }else if (attr == "dragstop" && selected_len == 0){
		return getBaseNodeColor(d);
        }else{
                        if (attr == "fill"){
                                return getBaseNodeColor(d);
                        } else{
				if (selected_len != 0){
	                                return d3.rgb(d.color.toString()).darker(5);
				}else{
					return getBaseNodeColor(d);
				}
                        }
        }
};
*/
function getNodesIsland(d){
	var nNodes = 0;
	data.nodes.forEach(function(o, i){
		if(o.group == d){
			nNodes++;
		}
	});
	return nNodes;
}
