# -*- coding: utf-8 -*-
"""

GeoAlchemy PostGIS models

"""

from geoalchemy import \
    GeometryColumn, Point, LineString, WKTSpatialElement, GeometryDDL
from geoalchemy.postgis import PGComparator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Boolean, BigInteger, Float, String
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class OSRMNode(Base):
    """Define a node in the routing network"""
    __tablename__ = "osrmnodes"

    osm_id = Column(Integer, primary_key=True)
    lat = Column(Integer)
    lon = Column(Integer)
    bollard = Column(Boolean)
    traffic_light = Column(Boolean)
    geom = GeometryColumn(Point(2), comparator=PGComparator)
    # Edges associated to this node
    in_edges = relationship("OSRMEdge", foreign_keys='OSRMEdge.sink')
    out_edges = relationship("OSRMEdge", foreign_keys='OSRMEdge.source')

    def __init__(self, osm_id, lat, lon, bollard, traffic_light):
        self.osm_id = osm_id
        self.lat = lat
        self.lon = lon
        self.bollard = bool(bollard)
        self.traffic_light = bool(traffic_light)
        self.geom = WKTSpatialElement(
            "POINT(%0.6f %0.6f)" % (lon/1E5, lat/1E5))


class OSRMEdge(Base):
    """Define a edge between 2 nodes in the routing network"""
    __tablename__ = "osrmedges"

    hash = Column(BigInteger, primary_key=True)
    source = Column(Integer, ForeignKey('osrmnodes.osm_id'), index=True)
    sink = Column(Integer, ForeignKey('osrmnodes.osm_id'), index=True)
    source_node = relationship("OSRMNode", foreign_keys="OSRMEdge.source")
    sink_node = relationship("OSRMNode", foreign_keys="OSRMEdge.sink")
    distance = Column(Integer)
    weight = Column(Integer)
    bidirectional = Column(Boolean)

    def __init__(self, source, sink, distance, weight, bidirectional):
        self.hash = self.hash_edge(source, sink)
        self.source = source
        self.sink = sink
        self.distance = distance
        self.weight = weight
        self.bidirectional = bool(bidirectional)

    @staticmethod
    def hash_edge(source, sink):
        """Generate a hash of the identifying info"""
        return hash(tuple(sorted((source, sink))))

    @staticmethod
    def is_forward(source, sink):
        """Determine if we are transversing edge forward or backward

        The distinction is arbitrary - if source has a lower ID
        than the sink ID, it is conisidered forward.
        """
        return bool(source < sink)


class OSRMEdgeGeom(Base):
    """Define a edge geometry between 2 nodes in the routing network"""
    __tablename__ = "osrmedgegeoms"
    hash = Column(BigInteger, ForeignKey("osrmedges.hash"),
                  primary_key=True)
    geom = GeometryColumn(LineString(2), comparator=PGComparator)
    edge = relationship("OSRMEdge")


class OSRMRoute(Base):
    """Definte a toy, random route, run using the OSRM engine"""
    __tablename__ = "osrmroutes"

    route_hash = Column(BigInteger, primary_key=True)
    start_lat = Column(Integer)
    start_lon = Column(Integer)
    end_lat = Column(Integer)
    end_lon = Column(Integer)
    duration = Column(Integer)
    nsteps = Column(Integer)
    query = Column(String(200))

    @staticmethod
    def hash_route(*xs):
        """Generate an MD5 hash of the route info"""
        return hash(xs)


class OSRMRouteStep(Base):
    __tablename__ = "osrmroutesteps"
    route_hash = Column(BigInteger, primary_key=True)
    step_idx = Column(Integer, primary_key=True)
    edge_id = Column(BigInteger)
    # Whether we traverse the edge high-low or low-high.
    forward = Column(Boolean)
    # We specify the joins manually, as we want to insert
    # into this table very quicly.
    edge = relationship(
        "OSRMEdge",
        primaryjoin="OSRMRouteStep.edge_id == OSRMEdge.hash",
        foreign_keys="OSRMEdge.hash",
        uselist=False
    )


class OSRMEdgeFrequencies(Base):
    __tablename__ = "edgefrequencies"
    edge = Column(BigInteger,  ForeignKey('osrmedges.hash'), primary_key=True)
    forward = Column(Boolean, primary_key=True)
    freq = Column(BigInteger)
    geom = GeometryColumn(LineString(2), comparator=PGComparator)
    edgeobj = relationship("OSRMEdge")


class OSRMRouteNode(Base):
    __tablename__ = "routenodes"
    osm_id = Column(Integer, ForeignKey('osrmnodes.osm_id'), primary_key=True)
    n_outputs = Column(Integer)
    n_inputs = Column(Integer)
    sum_out = Column(Integer)
    product_out = Column(BigInteger)
    log_sum_out = Column(Float)
    node = relationship("OSRMNode")


GeometryDDL(OSRMNode.__table__)
GeometryDDL(OSRMEdge.__table__)
GeometryDDL(OSRMEdgeGeom.__table__)
GeometryDDL(OSRMEdgeFrequencies.__table__)
