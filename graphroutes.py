#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Graph analysis on test routes
"""
__license__ = None

import argparse
import logging
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stanalysis.graphbuilder import build_graph
import stanalysis.graphtools as graphtools

log = logging.getLogger(__name__)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('output', metavar='graph.pickle',
                        help='Ouput graph file')
    parser.add_argument(
        '--connection',
        default='postgresql://osm:osm@localhost/osrm',
        help='Postgres connection string.  Default %(default)s'
    )
    parser.add_argument('--prune', action='store_true',
                        help='Collapse redundant edges, prune tails')

    parser.add_argument('--verbose', action='store_true',
                        help='Increase logging level')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING)

    log.info("Creating DB engine")
    engine = create_engine(args.connection, echo=False)

    log.info("Creating DB session")
    Session = sessionmaker(bind=engine)
    session = Session()

    g = build_graph(session)

    if args.prune:
        log.info("Collapsing edges")
        pruned = graphtools.collapse_degree_2_vtxs(g)
        log.info("Removed %i edges", pruned)
        log.info("Snipping tails")
        snipped = graphtools.delete_degree_1_vtxs(g)
        log.info("Removed %i tails", snipped)

    log.info("Saving graph to %s", args.output)
    g.save(args.output)

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))
