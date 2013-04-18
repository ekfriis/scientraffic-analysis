#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs many randomly selected routes in a region
"""
__license__ = None

from concurrent import futures
import functools
import itertools
import logging
import optparse
import sys

import numpy as np
import requests
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


def generate_routes(N, nodetable):
    """Generate start and end nodes for trips

    Generates pairs of (lat, lon) tuples corresponding to the
    start and end points for the route.

    :param N: number of trips to generate
    :param node_set: a :class:`tables.Table` containing OSRM nodes

    TODO: make this prefer short distances
    """
    for _ in range(N):
        start_row_idx = np.random.randint(0, nodetable.nrows-1)
        end_row_idx = np.random.randint(0, nodetable.nrows-1)
        start_row = nodetable[start_row_idx]
        end_row = nodetable[end_row_idx]
        yield ((start_row['lat'], start_row['lon']),
               (end_row['lat'], end_row['lon']))


def run_route(coords, host='localhost', port=5000):
    """Query an OSRM server for a route

    Returns the (decoded) JSON `output from OSRM`_.

    .. _output from OSRM: https://github.com/DennisOSRM/
        Project-OSRM/wiki/Output-json

    :param coords: 2-tuple of starting & ending (lat, lon)
    """
    startpt, endpt = coords

    # we can't uses the requests params feature, since it
    # will escape the commas.
    url = 'http://{host}:{port}/viaroute?loc={loc1}'\
        '&loc={loc2}&instructions=false&raw=true'.format(
            host=host, port=port,
            loc1=','.join(str(x / 100000.) for x in startpt),
            loc2=','.join(str(x / 100000.) for x in endpt),
        )
    response = requests.get(url)
    if response.status_code != 200:
        log.error("Route lookup with %s failed with %i.",
                  url, response.status_code)
        return None
    return np.array(response.json()['raw_data'], dtype=int)


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
        "threads": 2,
        "nroutes": 1000,
        "host": 'localhost',
        "port": '5000',
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
    parser.add_option("-t", "--threads", dest="threads",
                      default=defaults["threads"], type=int,
                      help="number of concurrent requests")
    parser.add_option("-n", "--nroutes", dest="nroutes",
                      default=defaults["nroutes"], type=int,
                      help="number of routes to run")
    parser.add_option("-c", "--host", dest="host",
                      default=defaults["host"], type=str,
                      help="OSRM server address")
    parser.add_option("-p", "--port", dest="port",
                      default=defaults["port"], type=int,
                      help="OSRM server port")

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

        # Create output format
        class OSRMRouteStep(tables.IsDescription):
            route_idx = tables.UInt32Col()
            idx_in_route = tables.UInt16Col()
            start_node = tables.UInt32Col()
            end_node = tables.UInt32Col()
            duration = tables.UInt16Col()
            start_lat = tables.Int32Col()
            start_lon = tables.Int32Col()

        group = outputfd.createGroup('/', 'routes', "OSRM routes")
        steps = outputfd.createTable(
            group, 'steps', OSRMRouteStep, "Steps")
        row = steps.row

        with tables.File(input_file, 'r') as inputfd:
            nodetable = inputfd.root.osrm.nodes
            log.info("Detected %i nodes", nodetable.nrows)

            nthrds = opts.threads
            log.info("Spawning %i compute processes", nthrds)
            with futures.ProcessPoolExecutor(max_workers=nthrds) as executor:
                route_runner = functools.partial(
                    run_route, host=opts.host, port=opts.port)
                # execute some jobs
                route_count = 0
                # Do the future mapping in chunks, to prevent memory
                # blowup.  I don't understand why the executor keeps
                # so much crap around.
                nchunks = opts.nroutes / 1000
                for ichunk in range(nchunks):
                    log.info("Processing 1k route block %i/%i",
                             ichunk + 1, nchunks)
                    for route in executor.map(
                            route_runner,
                            generate_routes(1000, nodetable)):

                        def get_pair_steps(x):
                            """Generate iterator over each step in list"""
                            return itertools.izip(x[:-1], x[1:])

                        for j, (startn, endn) in enumerate(
                                get_pair_steps(route)):
                            row['route_idx'] = route_count
                            row['idx_in_route'] = j
                            row['start_node'] = startn[0]
                            row['end_node'] = endn[0]
                            row['duration'] = startn[1]
                            row['start_lat'] = startn[2]
                            row['start_lon'] = startn[3]
                            row.append()
                        route_count += 1
                        steps.flush()

    return 0

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))
