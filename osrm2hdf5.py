#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert OSRM binary files into an HDF5 file

This script converts node and edge binary data in `OSRM`_ format into
HDF5 tables using the :mod:`tables` package.

.. _OSRM: https://github.com/DennisOSRM/
    Project-OSRM/wiki/OSRM-normalized-file-format

There are three tables in the output file:

  * blah
  * rah
  * gah
"""
__license__ = None

import logging
import optparse
import struct
import sys
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


def parseargs(argv):
    """Parse command line arguments.

    :param argv: a list of command line arguments, usually :data:`sys.argv`.

    Valid options are related to the desired verbosity.
    There should be two additional left over arguments, the input
    .osrm file and output .hd5 file.
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

    log.info("Opening output file %s", output_file)
    with tables.File(output_file, mode='w') as outputfd:
        group = outputfd.createGroup('/', 'osrm', "OSRM graph")

        _NODE_PACKING = struct.Struct('<iiIbbbb')

        class OSRMNode(tables.IsDescription):
            id = tables.UInt32Col()
            lon = tables.Int32Col()
            lat = tables.Int32Col()
            #  01 xx xx xx in case of bollard and
            #  xx 01 xx xx in case of traffic light
            bollard = tables.BoolCol()
            traffic_light = tables.BoolCol()

        nodes = outputfd.createTable(group, 'nodes', OSRMNode, "Nodes")
        with open(input_file, 'rb') as inputfd:
            # Read the number of nodes
            n_nodes = struct.unpack_from('<I', inputfd.read(4))[0]
            log.info("Detected %i nodes in this file", n_nodes)

            node = nodes.row
            report_every = n_nodes / 100
            for i in range(n_nodes):
                data = inputfd.read(_NODE_PACKING.size)
                unpacked = _NODE_PACKING.unpack(data)
                node['lat'], node['lon'], node['id'], node['bollard'], \
                    node['traffic_light'], _, _ = unpacked
                node.append()
                if i % report_every == 0:
                    log.info("Finished %i/%i nodes", i, n_nodes)

        _EDGE_PACKING = struct.Struct('<IIihihIbbbb')

        class OSRMEdge(tables.IsDescription):
            node_a = tables.UInt32Col()
            node_b = tables.UInt32Col()
            distance = tables.Int32Col()
            bidirectional = tables.BoolCol()
            weight = tables.Int32Col()
            edge_type = tables.Int16Col()
            name_id = tables.UInt32Col()
            roundabout = tables.BoolCol()
            ignore = tables.BoolCol()
            restricted = tables.BoolCol()

        edges = outputfd.createTable(group, 'edges', OSRMEdge, "Edges")
        with open(input_file, 'rb') as inputfd:
            # Read the number of nodes
            n_nodes = struct.unpack_from('<I', inputfd.read(4))[0]
            # Seek to edge section
            inputfd.seek(n_nodes * _NODE_PACKING.size + 4, 0)
            n_edges = struct.unpack_from('<I', inputfd.read(4))[0]
            log.info("Detected %i edges in this file", n_edges)

            edge = edges.row
            report_every = n_edges / 100
            for i in range(n_edges-1):
                if i % report_every == 0:
                    log.info("Finished %i/%i edges", i, n_edges)
                data = inputfd.read(_EDGE_PACKING.size)
                if not data:
                    # EOF
                    break
                if len(data) < _EDGE_PACKING.size:
                    raise IOError(
                        "edge #%i, expected length %i, got %i, (%s)" %
                        (i, _EDGE_PACKING.size, len(data), data))
                unpacked = _EDGE_PACKING.unpack(data)
                edge['node_a'] = unpacked[0]
                edge['node_b'] = unpacked[1]
                edge['distance'] = unpacked[2]
                edge['bidirectional'] = unpacked[3]
                edge['weight'] = unpacked[4]
                edge['edge_type'] = unpacked[5]
                edge['name_id'] = unpacked[6]
                edge['roundabout'] = unpacked[7]
                edge['ignore'] = unpacked[8]
                edge['restricted'] = unpacked[9]
                edge.append()
    return 0

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))
