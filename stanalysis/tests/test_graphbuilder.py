'''

Test building the route-frequency graph from the database

'''

import logging
import igraph
import math
from nose.tools import eq_, assert_almost_equal
logging.basicConfig(level=logging.WARNING)

log = logging.getLogger(__name__)

from stanalysis.tests.mockdb import test_db_session
from stanalysis.models import OSRMEdgeFrequencies, OSRMNode, \
    OSRMEdge, OSRMRouteNode
from stanalysis.graphbuilder import build_graph, export_nodes
import stanalysis.graphtools as gt


def test_build_graph():
    with test_db_session() as session:
        # Make a y-shaped graph
        node1 = OSRMNode(1, 1, 2, True, False)
        node2 = OSRMNode(2, 3, 4, False, False)
        node3 = OSRMNode(3, 5, 6, False, False)
        node4 = OSRMNode(4, 7, 8, False, False)
        session.add(node1)
        session.add(node2)
        session.add(node3)
        session.add(node4)

        edge_12 = OSRMEdge(1, 2, 5, 5, False)
        edge_23 = OSRMEdge(2, 3, 5, 5, False)
        edge_24 = OSRMEdge(2, 4, 5, 5, False)

        session.add_all([edge_12, edge_23, edge_24])

        session.commit()

        freq_12 = OSRMEdgeFrequencies(
            edge=OSRMEdge.hash_edge(1, 2),
            forward=True,
            freq=12,
            geom=None
        )
        freq_21 = OSRMEdgeFrequencies(
            edge=OSRMEdge.hash_edge(2, 1),
            forward=False,
            freq=21,
            geom=None
        )
        freq_34 = OSRMEdgeFrequencies(
            edge=OSRMEdge.hash_edge(3, 2),
            forward=True,
            freq=32,
            geom=None
        )
        freq_24 = OSRMEdgeFrequencies(
            edge=OSRMEdge.hash_edge(2, 4),
            forward=True,
            freq=24,
            geom=None
        )

        session.add_all(
            [freq_12, freq_21, freq_34, freq_24])
        session.commit()

        results = session.query(OSRMEdgeFrequencies).all()
        eq_(len(results), 4)
        eq_(results[0].edgeobj.source, 1)
        eq_(results[0].edgeobj.sink, 2)

        graph = build_graph(session)

        eq_(len(graph.vs), 4)
        eq_(len(graph.es), 4)
        assert(graph.is_directed)

        eq_(set(graph.vs["osm_id"]), set([1, 2, 3, 4]))

        eq_(len(graph.vs.select(osm_id=1)), 1)
        vtx_1 = graph.vs.select(osm_id=1)[0]
        eq_(vtx_1.indegree(), 1)
        eq_(vtx_1.outdegree(), 1)
        eq_(vtx_1.degree(), 2)
        eq_(vtx_1.successors()[0]["osm_id"], 2)
        eq_(vtx_1.predecessors()[0]["osm_id"], 2)

        vtx_2 = graph.vs.select(osm_id=2)[0]
        eq_(vtx_2.indegree(), 1)
        eq_(vtx_2.outdegree(), 3)
        eq_(vtx_2.degree(), 4)


def test_export_nodes():
    with test_db_session() as session:
        g = igraph.Graph(directed=True)
        # two boxes
        g.add_vertices(6)
        g.vs["osm_id"] = range(6)
        # the outer rectange
        g.add_edges([
            (1, 0),
            (0, 5),

            (2, 1),
            (2, 3),

            (4, 3),
            (4, 5),
        ])
        g.es["weight"] = [x + 1 for x in range(6)]

        for i in range(6):
            new_node = OSRMNode(i, 3400000, 11800000, False, False)
            session.add(new_node)
        session.commit()

        export_nodes(g, session)

        results = session.query(OSRMRouteNode).filter_by(osm_id=4).all()
        eq_(gt.output_weights(g, 4), [5, 6])
        eq_(results[0].n_outputs, 2)
        eq_(results[0].sum_out, 5 + 6)
        eq_(results[0].product_out, 5 * 6)
        assert_almost_equal(results[0].log_product_out,
                            math.log(5) * math.log(6))
