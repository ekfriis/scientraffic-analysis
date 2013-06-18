'''

Tools for converting the edge frequency columns into graphs.

'''


import logging

import igraph

log = logging.getLogger(__name__)


def output_weights(graph, vtx_idx):
    """ Get the weights of a vertex' outgoing edges """
    out_edges = graph.incident(vtx_idx, mode=igraph.OUT)
    return graph.es[out_edges]["weight"]


def delete_degree_1_vtxs(graph):
    """ Remove all tails (i.e. non-loop) paths from a graph.

    Returns number of tails removed.

    """
    tails = graph.vs.select(_degree_eq=1)
    graph.delete_vertices(tails)
    return len(tails)


def delete_degree_0_vtxs(graph):
    """ Remove all isolated points.

    Returns number of points removed.

    """
    loners = graph.vs.select(_degree_eq=0)
    graph.delete_vertices(loners)
    return len(loners)


def is_bollard(vtx):
    """ Returns true if the vtx is pure-source or pure-sink """
    return vtx.degree() and (not vtx.indegree() or not vtx.outdegree())


def collapse_degree_2_vtxs(graph):
    """ Collapse degree 2 vertices in a graph

    The essentially this converts one-way thru-nodes into an edge.
    Returns number of nodes removed.
    """
    # Find list of all thru-nodes
    thru_nodes = graph.vs.select(_degree_eq=2, _indegree_gt=0, _outdegree_gt=0)
    log.info("Found %i thru-nodes", len(thru_nodes))
    subgraph = graph.subgraph(thru_nodes.indices)
    subgraph.vs["original_idx"] = thru_nodes.indices

    # The 1-2 end nodes on each thru-way string
    string_edges = []

    # separate thruways
    components = subgraph.components(mode=igraph.WEAK)
    log.info("Found %i weakly-connected components in subgraph",
             len(components))

    for icomp, component in enumerate(components):
        tips = subgraph.vs[component].select(_degree_lt=2)
        assert(0 < len(tips) < 3)
        string_edges.append(
            (icomp,  # for debugging
             zip(
                 tips["original_idx"],
                 graph.vs[tips["original_idx"]].indegree(),
                 graph.vs[tips["original_idx"]].outdegree())))

    log.info("Identified end-nodes of thru-node strings")

    new_edges = []
    new_weights = []
    # find all non-thruway nodes, connected to the ends.
    for component, string in string_edges:
        in_node = None
        out_node = None
        # These should be the same, as flow is conserved.
        in_weight = None
        out_weight = None
        for end_idx, indegree, outdegree in string:
            predecessors = graph.predecessors(end_idx)
            successors = graph.successors(end_idx)

            for neighbor in predecessors:
                neighbor_vtx = graph.vs[neighbor]
                if neighbor_vtx.degree() > 2 or is_bollard(neighbor_vtx):
                    assert(in_node is None)
                    in_node = neighbor
                    edge = graph.get_eid(in_node, end_idx)
                    in_weight = graph.es[edge]["weight"]

            for neighbor in successors:
                neighbor_vtx = graph.vs[neighbor]
                if neighbor_vtx.degree() > 2 or is_bollard(neighbor_vtx):
                    assert(out_node is None)
                    out_node = neighbor
                    edge = graph.get_eid(end_idx, out_node)
                    out_weight = graph.es[edge]["weight"]

        # add an edge skipping over all the thru nodes
        log.debug("Connecting %s => %s, with weight %s (%s)",
                  in_node, out_node, in_weight, out_weight)
        new_edges.append((in_node, out_node))
        new_weights.append(in_weight)
        if in_weight != out_weight:
            log.error("The inbound edge %s does not equal the outbound %s",
                      in_weight, out_weight)

    log.info("Making %i new edge connections", len(new_edges))
    graph.add_edges(new_edges)
    #print graph.es["weight"], graph.es["weight"][:-len(new_edges)]
    #print graph.es["weight"][:-len(new_edges)] + new_weights
    graph.es["weight"] = graph.es["weight"][:-len(new_edges)] + new_weights
    #print graph.es[-2].tuple
    #print graph.es[-1].tuple

    # Now delete all the thru_nodes
    log.info("Deleting %i thru-nodes", len(thru_nodes))
    graph.delete_vertices(thru_nodes)
    return len(thru_nodes)


def collapse_bidirectional_streets(graph):
    """ Collapse nodes which are degree 4, but are on a two way street.

    This is a more intense operation than just collapsing unidirectional
    strings.

    Returns number of nodes removed.
    """
    # Find list of all thru-nodes
    cand_thru_nodes = graph.vs.select(
        _degree_eq=4, _indegree_eq=2, _outdegree_eq=2)
    log.info("Found %i candidate bidirectional thru-nodes",
             len(cand_thru_nodes))
    # Now filter these to the ones that are only related to two nodes.
    thru_nodes = [idx for idx in cand_thru_nodes.indices if
                  set(graph.successors(idx)) == set(graph.predecessors(idx))]
    log.info("%i are true thru-ways", len(thru_nodes))
    del cand_thru_nodes
    subgraph = graph.subgraph(thru_nodes)
    subgraph.vs["original_idx"] = thru_nodes
    thru_nodes = set(thru_nodes)  # for easy membership testing later.

    # The 1-2 end nodes on each thru-way string
    string_edges = []

    # separate thruways
    components = subgraph.components(mode=igraph.WEAK)
    log.info("Found %i weakly-connected components in subgraph",
             len(components))

    for icomp, component in enumerate(components):
        tips = subgraph.vs[component].select(_degree_lt=3)
        assert(0 < len(tips) < 3)

        original_idxs = tips["original_idx"]
        in_degrees = graph.vs[tips["original_idx"]].indegree()
        out_degrees = graph.vs[tips["original_idx"]].outdegree()
        predecessors = [set(graph.predecessors(idx)) for idx in original_idxs]
        successors = [set(graph.successors(idx)) for idx in original_idxs]

        string_edges.append(
            (icomp,  zip(original_idxs,
                         in_degrees,
                         out_degrees,
                         predecessors,
                         successors)))

    log.info("Identified end-nodes of thru-node strings")

    new_edges = []
    new_weights = []

    # find all non-thruway nodes, connected to the ends.
    for component, string in string_edges:
        assert(0 < len(string) < 3)

        def get_flow_info(end_info):
            """ Figure out the input/output flows of a string end"""
            end_idx = end_info[0]
            # The node from the full graph which flows *INTO*
            # the end of the string
            end_in = end_info[3].difference(thru_nodes)
            # The node from the full graph which flows *OUT OF*
            # the end of the string
            end_out = end_info[4].difference(thru_nodes)
            # Check if we are a single solitariy thru-node.
            # In this case both tips are the same node.
            if len(end_in) == 2:
                assert(end_in == end_out)
                end_out = end_in.pop()
                end_in = end_in.pop()
            else:
                assert(len(end_in) == 1)
                assert(len(end_out) == 1)
                # get the single element, done with these sets.
                end_in = end_in.pop()
                end_out = end_out.pop()

            in_flow_idx = graph.get_eid(end_in, end_idx)
            out_flow_idx = graph.get_eid(end_idx, end_out)
            return (end_in, graph.es[in_flow_idx]["weight"],
                    end_out, graph.es[out_flow_idx]["weight"])

        # 'Top' & 'Bottom' are arbirtary labels for each end of the symmetric
        # string.
        top_flow = get_flow_info(string[0])
        bottom_flow = get_flow_info(string[min(0, len(string))])

        # add an edge skipping over all the thru nodes
        log.debug("Connecting top-bottom %s => %s, with weight %s (%s)",
                  top_flow[0], bottom_flow[2], top_flow[1], bottom_flow[3])
        new_edges.append((top_flow[0], bottom_flow[2]))
        new_weights.append(top_flow[1])
        if top_flow[1] != bottom_flow[3]:
            log.error("The top-bottom inbound edge %s != outbound %s",
                      top_flow[1], bottom_flow[3])

        log.debug("Connecting bottom-top %s => %s, with weight %s (%s)",
                  bottom_flow[0], top_flow[2], bottom_flow[1], top_flow[3])
        new_edges.append((bottom_flow[0], top_flow[2]))
        new_weights.append(bottom_flow[1])
        if bottom_flow[1] != top_flow[3]:
            log.error("The bottom-top inbound edge %s != outbound %s",
                      bottom_flow[1], top_flow[3])

    log.info("Making %i new edge connections", len(new_edges))
    graph.add_edges(new_edges)
    graph.es["weight"] = graph.es["weight"][:-len(new_edges)] + new_weights

    # Now delete all the thru_nodes
    log.info("Deleting %i thru-nodes", len(thru_nodes))
    graph.delete_vertices(thru_nodes)
    return len(thru_nodes)


def identify_rendudant_nodes(g):
    """Flag nodes which can only be reached from a single upstream node

    Returns number of nodes made redundant.

    A node is redundant if it can only be reached from another node.

    You need significant statistics to do this in practice, otherwise
    you could remove nodes which also have other inputs that are
    rare.

    """
    g.vs["redundant"] = False
    redundant = 0
    for vtx in g.vs.select(_indegree_eq=1):
        pre = vtx.predecessors()[0]
        if pre.outdegree() > 1:
            redundant += 1
            vtx["redundant"] = True
    # travel up the chain to the first non-redundant node, if
    # outflow > X of total, is redundant.
    return redundant
