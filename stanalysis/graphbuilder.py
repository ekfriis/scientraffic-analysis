"""

Convert the flattened edge-frequency data in the database
into iGraph format.

"""

import logging

import igraph
import numpy as np

from stanalysis.models import OSRMEdgeFrequencies, OSRMEdge

log = logging.getLogger(__name__)


def query_data(session):
    """Query the database to get the essential graph info

    Generates a list of tuples of (start_node, end_node, frequency)
    """
    query = session.query(
        OSRMEdge.source, OSRMEdge.sink,
        OSRMEdgeFrequencies.freq,
        OSRMEdgeFrequencies.forward).join(OSRMEdgeFrequencies)
    for start, end, freq, forward in query:
        if forward:
            yield (start, end, freq)
        else:
            yield (end, start, freq)


def build_graph(session):
    log.info("Querying data")
    data = np.array(list(query_data(session)), dtype=int)

    # Map OSM node ID => graph vertex index
    node_idx_lookup = {}
    unique_nodes = np.unique(data[:, (0, 1)])
    for i, node_id in enumerate(unique_nodes):
        node_idx_lookup[node_id] = i
    log.info("Found %i nodes", len(node_idx_lookup))

    g = igraph.Graph(directed=True)
    g.add_vertices(len(node_idx_lookup))
    g.vs["osm_id"] = unique_nodes
    del unique_nodes

    log.info("Adding %i edges", len(data))
    g.add_edges([
        (node_idx_lookup[start], node_idx_lookup[end])
        for start, end in data[:, (0, 1)]])
    log.info("Setting edge weights")
    g.es['weight'] = data[:2]
    return g
