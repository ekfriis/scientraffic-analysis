import logging

import igraph
from nose.tools import eq_

import stanalysis.graphtools as gt

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)


def test_delete_degree_1_vtxs():
    g = igraph.Graph(directed=True)
    # a square with a tail
    g.add_vertices(5)
    g.add_edges([
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (2, 4)  # the tail
    ])
    eq_(len(g.vs), 5)
    eq_(len(g.es), 5)
    eq_(len(g.vs.select(_degree_eq=1)), 1)
    eq_(len(g.vs.select(_degree_eq=2)), 3)
    eq_(len(g.vs.select(_degree_eq=3)), 1)
    ret = gt.delete_degree_1_vtxs(g)
    eq_(ret, 1)
    # Now it is clean
    eq_(len(g.vs), 4)
    eq_(len(g.es), 4)
    eq_(len(g.vs.select(_degree_eq=1)), 0)
    eq_(len(g.vs.select(_degree_eq=2)), 4)
    eq_(len(g.vs.select(_degree_eq=3)), 0)


def test_collapse_degree_2_vtxs():
    g = igraph.Graph(directed=True)
    # a square with a diagonal + tail
    g.add_vertices(5)
    # the square
    g.add_edges([
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
    ])
    # the diagonal
    g.add_edges([(0, 2)])
    # the tail
    g.add_edges([(1, 4)])
    # so now vertex 3 is just a thru-node
    eq_(len(g.vs), 5)
    eq_(len(g.es), 6)

    eq_(len(g.vs.select(_degree_eq=1)), 1)
    eq_(len(g.vs.select(_degree_eq=2)), 1)
    eq_(len(g.vs.select(_degree_eq=3)), 3)

    ret = gt.collapse_degree_2_vtxs(g)
    eq_(ret, 1)
    # Now it is clean
    eq_(len(g.vs), 4)
    eq_(len(g.es), 5)
    eq_(len(g.vs.select(_degree_eq=1)), 1)
    eq_(len(g.vs.select(_degree_eq=2)), 0)
    eq_(len(g.vs.select(_degree_eq=3)), 3)


def test_collapse_degree_2_vtxs_complex():
    g = igraph.Graph(directed=True)
    # two boxes
    g.add_vertices(6)
    # the outer rectange
    g.add_edges([
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 0),
    ])
    # the center line
    g.add_edges([(1, 4)])

    # so now vertex 5-0 and 2-3 are thru-ways
    eq_(len(g.vs), 6)
    eq_(len(g.es), 7)

    ret = gt.collapse_degree_2_vtxs(g)
    # deleted 4
    eq_(ret, 4)

    # Now it is clean
    eq_(len(g.vs), 2)
    eq_(len(g.es), 3)
    eq_(len(g.vs.select(_degree_eq=2)), 0)


def test_collapse_degree_2_vtxs_bollard():
    # We should not remove nodes are source/sink only.
    g = igraph.Graph(directed=True)
    # two boxes
    g.add_vertices(6)
    # the outer rectange
    g.add_edges([
        (1, 0),
        (2, 1),
        (2, 3),
        (3, 4),
        (4, 5),
        (0, 5),
    ])
    # the center line
    g.add_edges([(1, 4)])

    # so now vertex 0 and 3 are thru-ways
    # vertex 5 and 2 are bollards
    eq_(len(g.vs), 6)
    eq_(len(g.es), 7)

    ret = gt.collapse_degree_2_vtxs(g)
    # deleted 4
    eq_(ret, 2)

    # Now it is clean
    eq_(len(g.vs), 4)
    eq_(len(g.es), 5)
    eq_(len(g.vs.select(_degree_eq=2)), 0)

if __name__ == "__main__":
    test_collapse_degree_2_vtxs()
