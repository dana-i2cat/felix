from threading import Thread
from expedient.clearinghouse.aggregate.models import *
from expedient.common.clients import xmlrpc, geni

"""
author: msune, CarolinaFernandez

Agent monitoring thread.
"""

class AggregateMonitoringThread(Thread):
    
    __method = None
    __param = None

    """
    Make sure Agent is up and running
    and updates status
    """
    def __update_aggregate_status(self, aggregate):
        manager_type = "geni"
        try:
            agg = aggregate.as_leaf_class()
            # Get protocol or try no authentication at all
            if "://" in agg.client.url:
                agg_xmlrpc_server_protocol = agg.client.url.split("://")[0]
                # Fill aggregate XMLRPC server URI
                agg_xmlrpc_server_url = "".join(agg.client.url.split("://")[1:])
            else: 
                agg_xmlrpc_server_protocol = "http"
                agg_xmlrpc_server_url = ":".join(agg.client.url.split("://")[1:])
            print "------ agg_xmlrpc_server_url: ", agg_xmlrpc_server_url
            agg_xmlrpc_server = "%s://" % agg_xmlrpc_server_protocol
            if "https://" in agg_xmlrpc_server and \
                all([ x in agg.client.__dict__ for x in ["username", "password"] ]):
                manager_type = "ofelia"
                agg_xmlrpc_server += agg.client.username + ":" + agg.client.password + "@"
            agg_xmlrpc_server += agg_xmlrpc_server_url
            
            # Server address and port for the aggregate
            agg_server_address = agg_xmlrpc_server_url.split(":")[0]
            agg_server_port = agg_xmlrpc_server_url.split(":")[1].split("/")[0]
            try:
                agg_server_address_endpoint = "/".join(agg_xmlrpc_server_url.split(":")[1].split("/")[1:])
            except:
                agg_server_address_endpoint = "RPC2"

            # OFELIA AMs
            if manager_type == "ofelia":
                try:
                    agg_info = xmlrpc.XmlRpcClient.call_method(agg_xmlrpc_server, "get_am_info", "")
                    # Save fields only for OF AMs
                    if aggregate.leaf_name == "OpenFlowAggregate":
                        aggregate.openflowaggregate.vlan_auto_assignment = agg_info["vlan_auto_assignment"]
                        aggregate.openflowaggregate.flowspace_auto_approval = agg_info["flowspace_auto_approval"]
                        # Save specific OpenFlowAggregate object
                        aggregate.openflowaggregate.straightSave()
                        aggregate.available = True
                    # Basic method within API
    #                print "Aggregate " + aggregate.name + " did not offer information about automatic VLAN and flowspace granting"
                    try:
                        # Older OF AM APIs shall not contain 'get_am_info' method. Try 'ping' in that case:
                        xmlrpc_result = xmlrpc.XmlRpcClient.call_method(agg_xmlrpc_server, "ping", "hello")
                        aggregate.available = True
                    except Exception as e:
                        print "Exception when performing 'ping' on aggregate manager: %s" % str(agg_xmlrpc_server)
                except Exception as e:
                    print "Exception when performing 'get_am_info' on aggregate manager: %s" % str(agg_xmlrpc_server)
            # GENI AMs
            elif manager_type == "geni":
                try:
                    print "agg_server_address: ", agg_server_address
                    client = geni.GENIClient(agg_server_address, agg_server_port, agg_server_address_endpoint)
                    geni_result = client.call_method("GetVersion")
                    aggregate.available = True
                except Exception as e:
                    print "Exception when performing 'GetVersion' on resource manager: %s" % str(agg_xmlrpc_server)
            print "Aggregate: %s => ALIVE" % aggregate.name
            
            #aggregate.save(permittee_kw = user.first_name)
            aggregate.straightSave()
        except Exception as e:
            #If fails for some reason mark as unreachable
            print e
            aggregate.available = False
            #aggregate.save(permittee_kw = user.first_name)
            print "Aggregate: %s => DEAD" % aggregate.name
            aggregate.straightSave()
    
    @staticmethod
    def monitor_aggregate_in_new_thread(param):
        thread = AggregateMonitoringThread()    
        thread.startMethod(param)
        return thread

    def startMethod(self,param):
        self.__method = self.__update_aggregate_status 
        self.__param = param
        self.start()

    def run(self):    
        self.__method(self.__param)
