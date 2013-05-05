'''

Test the OSRM GeoAlchemy models.

'''

import logging
from nose.tools import eq_
logging.basicConfig(level=logging.WARNING)


from geoalchemy import WKTSpatialElement
from stanalysis.tests.mockdb import create_tables, drop_tables, Session
from stanalysis.models import OSRMNode, OSRMEdge, OSRMRoute, OSRMRouteStep


def test_insert_node():
    drop_tables()
    create_tables()
    session = Session()
    new_node = OSRMNode(1, 3400000, 11800000, False, False)
    session.add(new_node)
    session.commit()
    # check if we can query it
    results = session.query(OSRMNode).filter_by(osm_id=1).all()
    eq_(len(results), 1)
    eq_(results[0].lat, 3400000)
    eq_(results[0].lon, 11800000)
    eq_(results[0].bollard, False)
    eq_(results[0].traffic_light, False)
    # check if we can spatial query it
    covering_box = WKTSpatialElement(
        'POLYGON((117 33, 119 33, 119 35, 117 35, 117 33))')
    eq_(session.query(OSRMNode).filter(
        OSRMNode.geom.covered_by(covering_box)).count(), 1)
    noncovering_box = WKTSpatialElement(
        'POLYGON((117 38, 119 38, 119 39, 117 39, 117 38))')
    eq_(session.query(OSRMNode).filter(
        OSRMNode.geom.covered_by(noncovering_box)).count(), 0)
    session.commit()
    session.close()
    drop_tables()


def test_insert_edge():
    drop_tables()
    create_tables()
    session = Session()
    node1 = OSRMNode(1, 1, 2, True, False)
    node2 = OSRMNode(2, 3, 4, False, False)
    session.add(node1)
    session.add(node2)
    the_edge = OSRMEdge(1, 2, 5, 5, False, 3)
    session.add(the_edge)
    session.commit()
    result = session.query(OSRMEdge).join(OSRMEdge.source_node).\
        filter(OSRMNode.lat == 1).all()
    eq_(len(result), 1)
    eq_(result[0].source_node.lon, 2)
    eq_(result[0].source_node.bollard, True)
    eq_(result[0].name_id, 3)
    session.commit()
    session.close()
    drop_tables()


def test_insert_osrm_route():
    drop_tables()
    create_tables()
    session = Session()
    route_hash = hex(hash(1))
    route = OSRMRoute(route_hash=route_hash, start_lat=2, start_lon=3,
                      end_lat=4, end_lon=5, duration=6, nsteps=7)
    session.add(route)
    session.commit()
    result = session.query(OSRMRoute).filter(
        OSRMRoute.route_hash == hex(hash(2))).all()
    eq_(len(result), 0)
    result = session.query(OSRMRoute).filter(
        OSRMRoute.route_hash == hex(hash(1))).all()
    eq_(len(result), 1)
    eq_(result[0].start_lat, 2)
    eq_(result[0].nsteps, 7)
    session.close()
    drop_tables()


def test_insert_osrm_routestep():
    drop_tables()
    create_tables()
    session = Session()
    route_hash = hex(hash(1))
    route = OSRMRoute(route_hash=route_hash, start_lat=2, start_lon=3,
                      end_lat=4, end_lon=5, duration=6, nsteps=7)
    session.add(route)
    step1 = OSRMRouteStep(route_hash=route_hash, step_idx=0,
                          start_lat=1, start_lon=2, end_lat=2, end_lon=3,
                          geom=OSRMRouteStep.build_geometry(1, 2, 2, 3))
    step2 = OSRMRouteStep(route_hash=route_hash, step_idx=1,
                          start_lat=1, start_lon=2, end_lat=2, end_lon=3,
                          geom=OSRMRouteStep.build_geometry(1, 2, 2, 3))
    session.add(step1)
    session.add(step2)
    session.commit()
    result = session.query(OSRMRoute).filter(
        OSRMRoute.route_hash == route_hash).all()
    eq_(len(result), 1)
    eq_(result[0].start_lat, 2)
    eq_(result[0].nsteps, 7)
    eq_(len(result[0].steps), 2)
    eq_(result[0].steps[1].end_lon, 3)
    eq_(result[0].steps[1].route.duration, 6)
    session.close()
    drop_tables()

if __name__ == "__main__":
    test_insert_node()
    test_insert_edge()
