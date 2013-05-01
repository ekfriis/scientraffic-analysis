'''

Test the OSRM GeoAlchemy models.

'''

import logging
logging.basicConfig(level=logging.WARNING)


#from nose.tools import eq_
def eq_(a, b):
    if a != b:
        raise AssertionError("%s != %s" % (a, b))


from geoalchemy import WKTSpatialElement
from stanalysis.tests.mockdb import create_tables, drop_tables, Session
from stanalysis.models import OSRMNode, OSRMEdge


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
    the_edge = OSRMEdge(10, 1, 2, 5, 5, False)
    session.add(the_edge)
    session.commit()
    result = session.query(OSRMEdge).join(OSRMEdge.source_node).\
        filter(OSRMNode.lat == 1).all()
    eq_(len(result), 1)
    eq_(result[0].source_node.lon, 2)
    eq_(result[0].source_node.bollard, True)
    session.commit()
    session.close()
    drop_tables()

if __name__ == "__main__":
    test_insert_node()
    #test_insert_edge()
