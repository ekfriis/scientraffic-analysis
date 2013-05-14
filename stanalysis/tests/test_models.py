'''

Test the OSRM GeoAlchemy models.

'''

import logging
from nose.tools import eq_
logging.basicConfig(level=logging.WARNING)

log = logging.getLogger(__name__)


from geoalchemy import WKTSpatialElement
from stanalysis.tests.mockdb import test_db_session
from stanalysis.models import OSRMNode, OSRMEdge, OSRMRoute, OSRMRouteStep


def test_insert_node():
    with test_db_session() as session:
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
        eq_(len(results[0].in_edges), 0)
        eq_(len(results[0].out_edges), 0)
        # check if we can spatial query it
        covering_box = WKTSpatialElement(
            'POLYGON((117 33, 119 33, 119 35, 117 35, 117 33))')
        eq_(session.query(OSRMNode).filter(
            OSRMNode.geom.covered_by(covering_box)).count(), 1)
        noncovering_box = WKTSpatialElement(
            'POLYGON((117 38, 119 38, 119 39, 117 39, 117 38))')
        eq_(session.query(OSRMNode).filter(
            OSRMNode.geom.covered_by(noncovering_box)).count(), 0)


def test_insert_edge():
    with test_db_session() as session:
        node1 = OSRMNode(1, 1, 2, True, False)
        node2 = OSRMNode(2, 3, 4, False, False)
        session.add(node1)
        session.add(node2)
        the_edge = OSRMEdge(1, 2, 5, 5, False)
        session.add(the_edge)
        session.commit()
        result = session.query(OSRMEdge).join(OSRMEdge.source_node).\
            filter(OSRMNode.lat == 1).all()
        eq_(len(result), 1)
        eq_(result[0].source_node.lon, 2)
        eq_(result[0].source_node.bollard, True)
        eq_(result[0].source_node.out_edges[0].distance, 5)
        eq_(len(result[0].source_node.in_edges), 0)
        eq_(len(result[0].sink_node.in_edges), 1)
        eq_(len(result[0].source_node.out_edges), 1)
        eq_(len(result[0].sink_node.out_edges), 0)


def test_insert_osrm_route():
    with test_db_session() as session:
        route_hash = OSRMRoute.hash_route(1)
        route = OSRMRoute(route_hash=route_hash, start_lat=2, start_lon=3,
                          end_lat=4, end_lon=5, duration=6, nsteps=7,
                          query='a long query string that you can set')
        session.add(route)
        session.commit()
        result = session.query(OSRMRoute).filter(
            OSRMRoute.route_hash == OSRMRoute.hash_route(2)).all()
        eq_(len(result), 0)
        result = session.query(OSRMRoute).filter(
            OSRMRoute.route_hash == OSRMRoute.hash_route(1)).all()
        eq_(len(result), 1)
        eq_(result[0].start_lat, 2)
        eq_(result[0].nsteps, 7)
        eq_(result[0].query, 'a long query string that you can set')


def test_insert_osrm_routestep():
    with test_db_session() as session:
        route_hash = OSRMRoute.hash_route(1)
        route = OSRMRoute(route_hash=route_hash, start_lat=2, start_lon=3,
                          end_lat=4, end_lon=5, duration=6, nsteps=7)
        session.add(route)
        node1 = OSRMNode(1, 1, 2, True, False)
        node2 = OSRMNode(2, 3, 4, False, False)
        node3 = OSRMNode(3, 5, 6, False, False)
        session.add(node1)
        session.add(node2)
        session.add(node3)

        edge1 = OSRMEdge(1, 2, 5, 0.3, True)
        edge2 = OSRMEdge(2, 3, 6, 0.3, True)

        session.add(edge1)
        session.add(edge2)

        step1 = OSRMRouteStep(route_hash=route_hash, step_idx=0,
                              edge_id=OSRMEdge.hash_edge(1, 2),
                              forward=OSRMEdge.is_forward(1, 2))

        step2 = OSRMRouteStep(route_hash=route_hash, step_idx=1,
                              edge_id=OSRMEdge.hash_edge(3, 2),
                              forward=OSRMEdge.is_forward(3, 2))

        session.add(step1)
        session.add(step2)
        session.commit()
        result = session.query(OSRMRoute).filter(
            OSRMRoute.route_hash == route_hash).all()
        eq_(len(result), 1)
        eq_(result[0].start_lat, 2)
        eq_(result[0].nsteps, 7)

        steps = session.query(OSRMRouteStep).all()
        eq_(steps[0].edge_id, OSRMEdge.hash_edge(1, 2))
        eq_(steps[0].edge_id, OSRMEdge.hash_edge(2, 1))  # commutes
        eq_(steps[0].step_idx, 0)
        eq_(steps[0].forward, True)
        eq_(steps[1].step_idx, 1)
        eq_(steps[1].forward, False)
        eq_(steps[0].edge.source_node.lon, 2)
        eq_(steps[0].edge.source_node.lat, 1)

if __name__ == "__main__":
    test_insert_node()
    test_insert_edge()
