#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run a Delaunuy triangulation on the important intersections
"""
__license__ = None

import logging
import optparse
import sys

import tables
import shapely
import numpy as np
from scipy.spatial import Delaunay

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
        "take": 1000,
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
    parser.add_option("-n", "--take", dest="take",
                      default=defaults["take"], type=int,
                      help="Number of final nodes to create")

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

    if len(args) != 3:
        log.error("You must specify an [input] and [output] file")
        return 1

    input_file, node_info, output_file = args[0], args[1], args[2]

    nodes = {}

    with tables.openFile(input_file, 'r') as store:
        ranking = store.root.osrm.nodewights
        for id in ranking.id[:min(args.take, ranking.nrows)]:
            nodes[id] = {}

    # Get the lat/lon and other meta data
    with tables.openFile(node_info, 'r') as store:
        node_info = store.root.osrm.nodes
        for node in nodes.keys():
            node_rows = node_info.getWhereList("id == %i" % node)
            if len(node_rows) != 1:
                log.error("Found wrong number of rows %i for node %i",
                          len(node_rows), node)
                continue
            lat = node_info[node_rows[0]]['lat']
            lon = node_info[node_rows[0]]['lon']
            nodes[node] = {
                'lat': lat,
                'lon': lon,
            }

    # Now, let's triangulate the points.
    node_list = np.ndarray(
        [[id, v['lat'], v['lon']] for id, v in nodes.iteritems()], dtype=int)
    import pdb
    pdb.set_trace()


    return 0

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))
