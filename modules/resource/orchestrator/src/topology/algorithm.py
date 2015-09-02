from delegate.geni.v3 import exceptions
import networkx as nwx


class AlgorithmManager:
    """
    This object can be used to run the Dijkstra (or any other) algorithm
       in a graph composed of FELIX resources (C-R, SDN-R and T-R).
    """
    def __init__(self):
        self.__g = nwx.MultiDiGraph()

    def add_node(self, node):
        self.__g.add_node(node)

    def add_nodes(self, node_list):
        self.__g.add_nodes_from(node_list)

    def add_unidir_link(self, src_node, dst_node, weight=1):
        self.__g.add_edge(src_node, dst_node, weight=weight)

    def add_bidir_link(self, node1, node2, weight=1):
        self.__g.add_edge(node1, node2, weight=weight)
        self.__g.add_edge(node2, node1, weight=weight)

    def str_nodes(self):
        return "(%d,%s)" % (self.__g.number_of_nodes(), self.__g.nodes())

    def str_links(self):
        return "(%d,%s)" % (self.__g.size(), self.__g.edges())

    def run_djikstra(self, src_node, dst_node):
        try:
            return nwx.dijkstra_path(self.__g, src_node, dst_node)

        except nwx.NetworkXNoPath as e:
            raise exceptions.TopologyError(str(e))

    # Add methods to build an "ERO" from the path.
