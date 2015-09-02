class Node(object):
    """
    A base class for all the nodes in the graph.
    """
    
    COMPUTE_NODE_TYPE = 'compute_node'
    SDN_NODE_TYPE = 'sdn_node'
    TRANSPORT_NODE_TYPE = 'transport_node'
    UNKNOWN_NODE_TYPE = 'unknown_node'
    
    def __init__(self, uid, typee=UNKNOWN_NODE_TYPE):
        self.uid_ = uid
        self.type_ = typee
    
    def __repr__(self):
        return "(%s,%s)" % (self.type_, self.uid_)


class CNode(Node):
    """
    This node represents a Computational (IT) resource.
    """
    
    def __init__(self, uid):
        super(CNode, self).__init__(uid, Node.COMPUTE_NODE_TYPE)


class SDNNode(Node):
    """
    This node represents a SDN resource.
    """
    
    def __init__(self, uid):
        super(SDNNode, self).__init__(uid, Node.SDN_NODE_TYPE)


class TNode(Node):
    """
    This node represents a Transport (NSI) resource.
    """
    
    def __init__(self, uid):
        super(TNode, self).__init__(uid, Node.TRANSPORT_NODE_TYPE)
