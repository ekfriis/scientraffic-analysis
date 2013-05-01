# -*- coding: utf-8 -*-
'''

Tests for reading OSRM binary data

'''

from StringIO import StringIO
import struct


#from nose.tools import eq_
def eq_(a, b):
    if a != b:
        raise AssertionError("%s != %s" % (a, b))

from stanalysis.osrmbinary import unpack_osrm_nodes, unpack_osrm_edges
from stanalysis.osrmbinary import OSRMEdge, OSRMNode, read_uint32


def make_dummy_data(n_nodes, n_edges):
    """Make a StringIO which simulates an OSRM data file"""
    output_nodes = []
    output_edges = []
    for i in range(n_nodes):
        output_nodes.append(OSRMNode(
            i, i, i, i, i, i, i))
    for i in range(n_edges):
        output_edges.append(OSRMEdge(
            i, i, i, i, i, i, i, i, i, i, i
        ))
    output = StringIO()
    output.write(struct.pack('<I', n_nodes))
    for node in output_nodes:
        output.write(struct.pack(node.PACKING.format, *node))
    output.write(struct.pack('<I', n_edges))
    for edge in output_edges:
        output.write(struct.pack(edge.PACKING.format, *edge))
    return output_nodes, output_edges, output


def test_read_uint32():
    my_io = StringIO()
    my_io.write(struct.pack('<I', 99))
    my_io.write(struct.pack('<I', 42))
    eq_(read_uint32(my_io, 0), 99)
    eq_(read_uint32(my_io, 4), 42)
    eq_(read_uint32(my_io, 0), 99)


def test_unpack_nodes():
    # Test node unpacking
    dummy_nodes, dummy_edges, dummy_binary = make_dummy_data(100, 20)
    new_nodes = list(unpack_osrm_nodes(dummy_binary))
    eq_(len(new_nodes), 100)
    eq_(dummy_nodes[0], new_nodes[0])
    #eq_(dummy_nodes, new_nodes)


def test_unpack_edges():
    # Test node unpacking
    dummy_nodes, dummy_edges, dummy_binary = make_dummy_data(100, 20)
    new_edges = list(unpack_osrm_edges(dummy_binary))
    eq_(len(new_edges), 20)
    eq_(dummy_edges[1], new_edges[1])
    eq_(dummy_edges[0], new_edges[0])
    #eq_(dummy_edges, new_edges)


if __name__ == "__main__":
    test_read_uint32()
    test_unpack_nodes()
    test_unpack_edges()
