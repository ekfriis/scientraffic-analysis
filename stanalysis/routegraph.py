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


def collapse_degree_2_vtxs(graph):
    """ Collapse degree 2 vertices in a graph

    The essentially this converts one-way thru-nodes into an edge.
    Returns number of nodes removed.
    """
    # Find list of all thru-nodes
    thru_nodes = graph.vs.select(_degree_eq=2)
    subgraph = graph.subgraph(thru_nodes, )
    subgraph.vs["original_idx"] = thru_nodes.indices

    # The 1-2 end nodes on each thru-way string
    string_edges = []

    # separate thruways
    components = subgraph.components(mode=igraph.WEAK)

    for component in components:
        tips = subgraph.vs[component].select(_degree_lt=2)
        assert(0 < len(tips) < 3)
        string_edges.append(zip(
            tips["original_idx"],
            graph.vs[tips["original_idx"]].indegree(),
            graph.vs[tips["original_idx"]].outdegree(),
        ))

    # find all non-thruway nodes, connected to the ends.
    for string in string_edges:
        in_node = None
        out_node = None
        for end_idx, indegree, outdegree in string:
            predecessors = graph.predecessors(end_idx)
            successors = graph.successors(end_idx)
            for neighbor in predecessors:
                if graph.degree(neighbor) > 2:
                    assert(in_node is None)
                    in_node = neighbor
            for neighbor in successors:
                if graph.degree(neighbor) > 2:
                    assert(out_node is None)
                    out_node = neighbor

        # add an edge skipping over all the thru nodes
        graph.add_edge(in_node, out_node)

    # Now delete all the thru_nodes
    graph.delete_vertices(thru_nodes)
    return len(thru_nodes)
