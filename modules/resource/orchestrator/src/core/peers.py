class AllowedPeers:
    """
    Defines the type of allowed peers.
    """
    PEER_CRM = "virtualisation"
    PEER_SDNRM = "sdn_networking"
    PEER_TNRM = "transport_network"
    PEER_SERM = "stitching_entity"
    PEER_RO = "island_ro"

    @staticmethod
    def get_peers_key():
        return list(filter((lambda x: x.startswith("PEER_")), AllowedPeers.__dict__))

    @staticmethod
    def get_peers_type():
        return list(AllowedPeers.__dict__.get(x) for x in AllowedPeers.get_peers_key())

    @staticmethod
    def get_peers():
        keys = AllowedPeers.get_peers_key()
        peers = dict()
        for key in keys:
            peers[key] = AllowedPeers.__dict__.get(key)
        return peers
