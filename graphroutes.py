#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Graph analysis on test routes
"""
__license__ = None

from collections import Counter
import logging
import math
import optparse
import sys

import igraph
import numpy as np
import tables

# NullHandler was added in Python 3.1.
try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Add a do-nothing NullHandler to the module logger to prevent "No handlers
# could be found" errors. The calling code can still add other, more useful
# handlers, or otherwise configure logging.
log = logging.getLogger(__name__)
log.addHandler(NullHandler())


def build_vtx_ranker(g):
    """Build a closure which ranks connective of vertices in g

    :param g: a :class:`igraph.Graph`
    """

    def adj_weights(vtx_idx):
        """Return weights of edges adjacent to vtx"""
        return sorted(g.es.select(g.adjacent(vtx_idx))['weight'], reverse=True)

    def weight_score(weights):
        """Determine how an intersection scores, based on it's weights

        We want to prioritize intersections like:
            [45, 67, 112]
        over
            [1, 1102, 1103]
        while respecting that this:
            [15, 940, 955]
        is probably pretty good too.
        """
        #return sum((2 * i + 1) * math.log(x+1)
                   #for i, x in enumerate(weights[1:]))
        return sum(math.log(x+1)
                   for i, x in enumerate(weights[1:]))

    def predicate(vtx_idx):
        return weight_score(adj_weights(vtx_idx))

    return predicate


def steplist_2_igraph(stepstore, take_fraction=0.1):
    """Convert a steplist into an igraph

    :param stepstore: a :class:`pandas.HDFStore` containing
    the route step counts.
    :param take_fraction: what fraction of the steps to keep
    """
    # Get the HDF5 table
    steps = stepstore.root.routes.steps

    log.info("Grouping observed edges by start and end")

    node_2_latlon = {}

    edge_counts = Counter()
    for row in steps.iterrows():
        start_node = int(row['start_node'])
        edge_counts[(start_node, int(row['end_node']))] += 1
        if start_node not in node_2_latlon:
            lat = row['start_lat']
            lon = row['start_lon']
            node_2_latlon[start_node] = (lat, lon)

    top_n_percent = np.array(edge_counts.most_common(
        int(len(edge_counts) * take_fraction)))

    # Find unique nodes
    nodes = {}
    for (startn, endn), weight in top_n_percent:
        nodes[startn] = -1
        nodes[endn] = -1

    log.info("Found %i unique nodes", len(nodes))

    # Map them to consecutive integers
    # (the graph vertex ids)
    for idx, nodeid in enumerate(nodes.keys()):
        nodes[nodeid] = idx

    edges = []
    edge_weights = []
    for (start, end), weight in top_n_percent:
        edges.append((nodes[start], nodes[end]))
        edge_weights.append(weight)
    del top_n_percent

    graph = igraph.Graph()
    graph.add_vertices(len(nodes))
    graph.vs["id"] = nodes.keys()
    graph.vs["lat"] = [node_2_latlon[id][0] for id in nodes.keys()]
    graph.vs["lon"] = [node_2_latlon[id][1] for id in nodes.keys()]

    log.info("Adding %i edges", len(edges))
    graph.add_edges(edges)
    graph.es['weight'] = edge_weights
    return graph


def parseargs(argv):
    """Parse command line arguments.

    :param argv: a list of command line arguments, usually :data:`sys.argv`.

    Valid options are related to the desired verbosity.
    There should be two additional left over arguments, the input
    .osrm file and output .hdf5 file containing the routes.
    """
    prog = argv[0]
    parser = optparse.OptionParser(prog=prog)
    parser.allow_interspersed_args = False

    defaults = {
        "quiet": 0,
        "silent": False,
        "verbose": 0,
    }

    # Global options.
    parser.add_option("-q", "--quiet", dest="quiet",
                      default=defaults["quiet"], action="count",
                      help="decrease the logging verbosity")
    parser.add_option("-s", "--silent", dest="silent",
                      default=defaults["silent"], action="store_true",
                      help="silence the logger")
    parser.add_option("-v", "--verbose", dest="verbose",
                      default=defaults["verbose"], action="count",
                      help="increase the logging verbosity")

    (opts, args) = parser.parse_args(args=argv[1:])
    return (opts, args)


def main(argv, out=None, err=None):
    """Read in an .osrm file and produce a .hdf5 file.

    Returns 0 if successfull, 1 on error.

    :param argv: a list of command line arguments, usually :data:`sys.argv`.
    :param out: stream to write messages; :data:`sys.stdout` if None.
    :param err: stream to write error messages; :data:`sys.stderr` if None.
    """
    if out is None:  # pragma: nocover
        out = sys.stdout
    if err is None:  # pragma: nocover
        err = sys.stderr
    (opts, args) = parseargs(argv)
    level = logging.WARNING - ((opts.verbose - opts.quiet) * 10)
    if opts.silent:
        level = logging.CRITICAL + 1

    format = "%(message)s"
    handler = logging.StreamHandler(err)
    handler.setFormatter(logging.Formatter(format))
    log.addHandler(handler)
    log.setLevel(level)

    if len(args) != 2:
        log.error("You must specify an [input] and [output] file")
        return 1

    input_file, output_file = args[0], args[1]

    with tables.openFile(input_file, 'r') as store:
        g = steplist_2_igraph(store, take_fraction=0.25)

    intersection_vertices = g.vs.select(_degree_gt=2)
    log.info("Found %i intersection vertices", len(intersection_vertices))

    ranker = build_vtx_ranker(g)

    log.info("Computing intersection scores")
    # Now find the best vertices
    vtx_scores = np.array(
        [ranker(vertex.index) for vertex in intersection_vertices])

    vtx_order = np.argsort(vtx_scores)

    log.info("Opening output file %s", output_file)
    with tables.File(output_file, mode='w') as outputfd:

        # Define output format & location
        class NodeWeight(tables.IsDescription):
            id = tables.UInt32Col()
            score = tables.FloatCol()
            lat = tables.Int32Col()
            lon = tables.Int32Col()

        group = outputfd.createGroup('/', 'osrm', "OSRM routes")
        weights = outputfd.createTable(
            group, 'nodeweights', NodeWeight, "Steps")
        row = weights.row

        for vtx_idx in vtx_order:
            vtx = intersection_vertices[int(vtx_idx)]
            row['id'] = vtx['id']
            row['lat'] = vtx['lat']
            row['lon'] = vtx['lon']
            row['score'] = vtx_scores[vtx_idx]
            row.append()

    return 0

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))
