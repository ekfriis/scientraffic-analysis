#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

Script to upload OSRM binary data into PostGIS

'''

import argparse
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from stanalysis.osrmbinary import unpack_osrm_nodes, unpack_osrm_edges
from stanalysis.models import OSRMNode, OSRMEdge, Base

log = logging.getLogger(__name__)


def upload_osrm_binary(binaryfd, dbsession, merge=False, commit_every=1000):
    ''' Upload OSRM data into the db

    :param: binaryfd - a file descript pointing to the .osrm data
    :param: dbsession - an active :class:`sqlalchemy.Session`
    '''

    insert_method = dbsession.add if not merge else dbsession.merge
    log.info("Loading OSRM node data")
    nodes_added = 0
    for node in unpack_osrm_nodes(binaryfd):
        ormified = OSRMNode(node.id, node.lat, node.lon,
                            node.bollard, node.traffic_light)
        insert_method(ormified)
        nodes_added += 1
        if nodes_added % commit_every == 0:
            log.info("Added %i nodes", nodes_added)
            dbsession.commit()
    dbsession.commit()
    log.info("Added %i nodes", nodes_added)

    log.info("Loading OSRM edge data")
    edges_added = 0
    for edge in unpack_osrm_edges(binaryfd):
        ormified = OSRMEdge(
            edge.node_a,
            edge.node_b,
            edge.distance,
            edge.weight,
            edge.bidirectional
        )
        insert_method(ormified)
        edges_added += 1
        if edges_added % commit_every == 0:
            log.info("Added %i edges", edges_added)
            dbsession.commit()
    dbsession.commit()
    log.info("Added %i edges", edges_added)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('osrm_file', metavar='input.osrm',
                        type=argparse.FileType('rb'),
                        help='Input .osrm binary file')
    parser.add_argument(
        '--connection',
        default='postgresql://osm:osm@localhost/osrm',
        help='Postgres connection string.  Default %(default)s'
    )
    parser.add_argument('--mode', choices=['append', 'recreate', 'update'],
                        default='recreate',
                        help='If "recreate", the tables will be dropped')
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

    if args.mode == 'recreate':
        log.info("Dropping existing OSRM tables")
        Base.metadata.drop_all(engine)
    if args.mode in ('append', 'recreate'):
        log.info("Creating OSRM tables")
        Base.metadata.create_all(engine)

    upload_osrm_binary(args.osrm_file, session, args.mode == 'update')

    log.info("Done.")
