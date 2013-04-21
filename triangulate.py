#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run a Delaunuy triangulation on the important intersections
"""
__license__ = None

import argparse
import logging
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
    parser = argparse.ArgumentParser(prog=prog)

    defaults = {
        "quiet": 0,
        "silent": False,
        "verbose": 0,
        "take": 1000,
    }

    parser.add_argument("input", metavar="scoredroutes.hdf5",
                        help="input file")
    parser.add_argument("output", metavar="triangulation.json",
                        help="output GeoJSON file")
    parser.add_argument("-q", "--quiet", dest="quiet",
                        default=defaults["quiet"], action="count",
                        help="decrease the logging verbosity")
    parser.add_argument("-s", "--silent", dest="silent",
                        default=defaults["silent"], action="store_true",
                        help="silence the logger")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        default=defaults["verbose"], action="count",
                        help="increase the logging verbosity")
    parser.add_argument("-n", "--take", dest="take",
                        default=defaults["take"], type=int,
                        help="Number of final nodes to create")

    args = parser.parse_args(args=argv[1:])
    return args


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
    args = parseargs(argv)
    level = logging.WARNING - ((args.verbose - args.quiet) * 10)
    if args.silent:
        level = logging.CRITICAL + 1

    format = "%(message)s"
    handler = logging.StreamHandler(err)
    handler.setFormatter(logging.Formatter(format))
    log.addHandler(handler)
    log.setLevel(level)

    node_list = []

    with tables.openFile(args.input, 'r') as store:
        ranking = store.root.osrm.nodeweights
        for row in ranking.iterrows():
            if len(node_list) == args.take:
                break
            node_list.append([
                row['id'],
                row['lat'],
                row['lon']
            ])

    # Now, let's triangulate the points.
    node_list = np.array(node_list, dtype=int)

    log.info("Triangulating %i nodes

    return 0

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))

