'''

Test the edge frequency table access/insertion/joins

'''

import logging
from nose.tools import eq_
logging.basicConfig(level=logging.WARNING)

log = logging.getLogger(__name__)

from stanalysis.tests.mockdb import test_db_session
from stanalysis.models import OSRMEdgeFrequencies, OSRMNode, OSRMEdge


def test_freq_backref():
    with test_db_session() as session:
        node1 = OSRMNode(1, 1, 2, True, False)
        node2 = OSRMNode(2, 3, 4, False, False)
        session.add(node1)
        session.add(node2)
        the_edge = OSRMEdge(1, 2, 5, 5, False)
        session.add(the_edge)
        session.commit()

        the_freq = OSRMEdgeFrequencies(
            edge=OSRMEdge.hash_edge(1, 2),
            forward=True,
            freq=10,
            geom=None
        )
        session.add(the_freq)
        the_freq_backward = OSRMEdgeFrequencies(
            edge=OSRMEdge.hash_edge(1, 2),
            forward=False,
            freq=11,
            geom=None
        )
        session.add(the_freq_backward)
        session.commit()

        results = session.query(OSRMEdgeFrequencies).all()
        eq_(len(results), 2)
        eq_(results[0].freq, 10)
        eq_(results[0].forward, True)
        # test join
        eq_(results[0].edgeobj.source, 1)
        eq_(results[0].edgeobj.sink, 2)
