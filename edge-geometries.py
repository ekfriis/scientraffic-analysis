#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

Build the OSRM Edge geometires

'''

import argparse
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from stanalysis.models import OSRMEdgeGeom, build_edge_geometries

log = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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

    log.info("Dropping existing geometry tables")
    OSRMEdgeGeom.metadata.drop_all(engine)
    OSRMEdgeGeom.metadata.create_all(engine)

    log.info("Building geometires")
    build_edge_geometries(session)
    log.info("Committing")
    session.commit()

    log.info("Done.")
