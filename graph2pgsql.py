#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert simplified graph back into Postgres form.
"""
__license__ = None

import argparse
import logging
import sys

import igraph
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import stanalysis.models as models
from stanalysis.graphbuilder import export_nodes

log = logging.getLogger(__name__)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='graph.pickle',
                        help='Input graph file')
    parser.add_argument(
        '--connection',
        default='postgresql://osm:osm@localhost/osrm',
        help='Postgres connection string.  Default %(default)s'
    )
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

    log.info("Creating OSRM tables")
    models.Base.metadata.create_all(engine)
    session.query(models.OSRMRouteNode).delete()

    g = igraph.read(args.input)

    export_nodes(g, session)

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main(sys.argv))
