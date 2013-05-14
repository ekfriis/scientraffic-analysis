# -*- coding: utf-8 -*-
'''

Functions for reading the OSRM binary files.

This script converts node and edge binary data in `OSRM`_ format
into a PostGIS database.

.. _OSRM: https://github.com/DennisOSRM/
    Project-OSRM/wiki/OSRM-normalized-file-format

'''

import collections
import logging
import struct

log = logging.getLogger(__name__)

# Node datum and its packing
OSRMNode = collections.namedtuple(
    'OSRMNode', ['lat', 'lon', 'id', 'bollard', 'traffic_light',
                 'dunno', 'dunno2'])
OSRMNode.PACKING = struct.Struct('<iiIbbbb')

# Edge datum and its packing
OSRMEdge = collections.namedtuple(
    'OSRMEdge',
    ['node_a',
     'node_b',
     'distance',
     'bidirectional',
     'weight',
     'edge_type',
     'name_id',
     'roundabout',
     'ignore',
     'restricted',
     'dunno']
)
OSRMEdge.PACKING = struct.Struct('<IIihihIbbbb')


def read_uint32(inputfd, offset):
    """Read a 32bit integer at the given location"""
    inputfd.seek(offset, 0)
    return int(struct.unpack_from('<I', inputfd.read(4))[0])


def unpack_osrm_data(DataType, inputfd, offset=0):
    """Unpack a OSRM data from an input stream

    Yields each data object.

    :param: :class:`DataType` - the class used to create
    each object.
    :param: inputfd - input data stream. Must be seek-able.
    :param: offset - integer offset for the start of the data
    """
    num_objects = read_uint32(inputfd, offset)
    log.info("Detected %i %s objects", num_objects, DataType)
    inputfd.seek(offset + 4, 0)
    datum_size = DataType.PACKING.size
    for i in range(num_objects):
        data = inputfd.read(datum_size)
        if not data:  # pragma: nocover
            # EOF
            break
        if len(data) < datum_size:  # pragma: nocover
            raise IOError(
                "datum #%i, expected length %i, got %i, (%s)" %
                (i, datum_size, len(data), data))
        yield DataType(*DataType.PACKING.unpack(data))


def unpack_osrm_nodes(inputfd):
    """Read OSRM nodes from an OSRM binary data file

    Yields each node as a :class:`OSRMNode`.

    :param: inputfd - input file descriptor.
    """
    for node in unpack_osrm_data(OSRMNode, inputfd, 0):
        yield node


def unpack_osrm_edges(inputfd):
    """Read OSRM edges from an OSRM binary data file

    Yields each edge as a :class:`OSRMEdge`.

    :param: inputfd - input file descriptor
    """
    # find offset where edge data starts
    num_nodes = read_uint32(inputfd, 0)
    log.info("Skipping over %i nodes to read edges", num_nodes)
    # NB the + 4 is for the "num_nodes" bytes
    for edge in unpack_osrm_data(OSRMEdge, inputfd,
                                 num_nodes * OSRMNode.PACKING.size + 4):
        yield edge
