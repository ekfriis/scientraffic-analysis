'''

Test the OSRM GeoAlchemy models.

'''

#from nose.tools import eq_
def eq_(a, b):
    if a != b:
        raise AssertionError("%s != %s" % (a, b))


from stanalysis.tests.mockdb import create_tables, drop_tables, session
from stanalysis.models import OSRMNode, OSRMEdge


def test_insert_node():
    drop_tables()
    create_tables()
    new_node = OSRMNode(1, 3400000, 11800000, False, False)
    session.add(new_node)


def test_insert_edge():
    pass

if __name__ == "__main__":
    test_insert_node()
