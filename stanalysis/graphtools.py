'''

Tools for converting the edge frequency columns into graphs.

'''


import logging

import igraph

log = logging.getLogger(__name__)


def delete_degree_1_vtxs(graph):
    """ Remove all tails (i.e. non-loop) paths from a graph.

    Returns number of tails removed.

    """
    tails = graph.vs.select(_degree_eq=1)
    graph.delete_vertices(tails)
    return len(tails)


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
    # find all non-thruway nodes, connected to the ends.
    for component, string in string_edges:
        in_node = None
        out_node = None
        for end_idx, indegree, outdegree in string:
            predecessors = graph.predecessors(end_idx)
            successors = graph.successors(end_idx)

            for neighbor in predecessors:
                neighbor_vtx = graph.vs[neighbor]
                if neighbor_vtx.degree() > 2 or is_bollard(neighbor_vtx):
                    assert(in_node is None)
                    in_node = neighbor

            for neighbor in successors:
                neighbor_vtx = graph.vs[neighbor]
                if neighbor_vtx.degree() > 2 or is_bollard(neighbor_vtx):
                    assert(out_node is None)
                    out_node = neighbor

        # add an edge skipping over all the thru nodes
        log.debug("Connecting %s => %s", in_node, out_node)
        new_edges.append((in_node, out_node))

    log.info("Making %i new edge connections", len(new_edges))
    graph.add_edges(new_edges)

    # Now delete all the thru_nodes
    log.info("Deleting %i thru-nodes", len(thru_nodes))
    graph.delete_vertices(thru_nodes)
    return len(thru_nodes)
