#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs many randomly selected routes in a region
"""
__license__ = None

import argparse
from concurrent import futures
import functools
import itertools
import logging
import math

import numpy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import stanalysis.routerunner as rr
import stanalysis.models as models

log = logging.getLogger(__name__)


if __name__ == "__main__":  # pragma: nocover
    parser = argparse.ArgumentParser()
    parser.add_argument('N', type=int, help='Number of routes to run')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--verbose', action='store_true',
                        help='Increase log output')
    parser.add_argument('--echo', action='store_true',
                        help='Print all SQL activity')
    dbgroup = parser.add_argument_group('postgis db')
    dbgroup.add_argument(
        '--dbconnection',
        default='postgresql://osm:osm@localhost/osrm',
        help='Postgres connection string.  Default %(default)s'
    )
    dbgroup.add_argument('--mode', choices=['recreate', 'update'],
                         default='update',
                         help='If "recreate", the tables will be dropped')
    group = parser.add_argument_group('OSRM server')
    group.add_argument('--host', default='localhost',
                       help="OSRM server host. Default %(default)s")
    group.add_argument('--port', default='8080',
                       help="OSRM server port. Default %(default)s")
    parser.add_argument(
        '--threads', type=int, default=2,
        help='Number of concurrent threads'
    )

    args = parser.parse_args()

    if args.seed is not None:
        log.info("Setting random seed to %i", args.seed)
        numpy.random.seed(args.seed)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING)

    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(
        logging.WARNING)

    log.info("Creating DB engine")
    engine = create_engine(args.dbconnection, echo=args.echo)

    log.info("Creating DB session")
    Session = sessionmaker(bind=engine)
    session = Session()

    if args.mode == 'recreate':
        log.info("Dropping existing OSRM tables")
        models.OSRMRoute.metadata.drop_all(engine)
        models.OSRMRouteStep.metadata.drop_all(engine)
    log.info("Creating OSRM tables")
    models.Base.metadata.create_all(engine)
    models.Base.metadata.create_all(engine)

    log.info("Querying list of all nodes")
    nodes = []
    for x in session.query(
            models.OSRMNode.lat, models.OSRMNode.lon).yield_per(1000):
        nodes.append(x)
    nodes = numpy.array(nodes, dtype=int)

    log.info("Spawning %i workers", args.threads)
    with futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        route_runner = functools.partial(
            rr.run_route, host=args.host, port=args.port)
        # execute some jobs
        route_count = 0
        # Do the future mapping in chunks, to prevent memory
        # blowup.  I don't understand why the executor keeps
        # so much crap around.
        chunk_size = 1000
        nchunks = max(int(math.ceil(args.N / chunk_size)), 1)
        for ichunk in range(nchunks):
            log.info("Processing %i route block %i/%i",
                     chunk_size, ichunk + 1, nchunks)
            routes_to_run = rr.generate_random_choices_exponential(
                chunk_size, nodes)
            commit_every = 20
            for route in executor.map(route_runner, routes_to_run):

                coords, query_url, steps = route

                if not len(steps):
                    log.error("No steps returned for route: %s", coords)
                    continue

                route_hash = models.OSRMRoute.hash_route(
                    tuple(coords[0]),
                    tuple(coords[1]),
                )
                ormified_route = models.OSRMRoute(
                    route_hash=route_hash,
                    start_lat=coords[0][0],
                    start_lon=coords[0][1],
                    end_lat=coords[1][0],
                    end_lon=coords[1][1],
                    duration=steps[:, 1].sum(),
                    nsteps=len(steps),
                    query=query_url,
                )

                session.add(ormified_route)

                def get_pair_steps(x):
                    """Generate iterator over each step in list"""
                    return itertools.izip(x[:-1], x[1:])

                ormed_steps = []
                for j, (startn, endn) in enumerate(
                        get_pair_steps(steps)):
                    start_id, _, start_lat, start_lon = startn
                    end_id, _, end_lat, end_lon = endn
                    ormified_step = models.OSRMRouteStep(
                        route_hash=route_hash,
                        step_idx=j,
                        edge_id=models.OSRMEdge.hash_edge(start_id, end_id),
                        forward=models.OSRMEdge.is_forward(start_id, end_id),
                    )
                    ormed_steps.append(ormified_step)
                session.add_all(ormed_steps)
                session.commit()
                route_count += 1
                log.info("Committed route %i with %i steps",
                         route_count, len(ormed_steps))
                if route_count == args.N:
                    break
            log.info("Committed %i routes", route_count)
