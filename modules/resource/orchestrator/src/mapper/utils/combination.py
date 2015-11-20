class PathFinderTNtoSDNCombinationUtils(object):

    @staticmethod
    def compute_combinations_stp_pairs(src_stps, dst_stps):
        # Find all possible combinations (order-independent)
        #import itertools
        #full_stps = [src_stps, dst_stps]
        #_, list_idx = min((val, idx) for (idx, val) in enumerate(full_stps))
        #min_list = full_stps[list_idx]
        #max_list = full_stps[len(full_stps)-1-list_idx]
        #combinations_src_dst_stps = [zip(x,max_list) for x in itertools.combinations(min_list, len(max_list))]
        combinations_src_dst_stps = [ (s,d) for s in src_stps for d in dst_stps ]
        return combinations_src_dst_stps

    @staticmethod
    def yield_combinations_stp_pairs(src_stps, dst_stps):
        # Find all possible combinations (order-independent)
        for src in src_stps:
            for dst in dst_stps:
                yield (src, dst)
