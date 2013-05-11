# -*- coding: utf-8 -*-
"""

GeoAlchemy PostGIS models

"""

from geoalchemy import GeometryColumn, Point, LineString,\
    WKTSpatialElement, GeometryDDL
from geoalchemy.postgis import PGComparator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, ForeignKey, BigInteger
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
    name_id = Column(Integer, index=True)
    source_node = relationship("OSRMNode", foreign_keys="OSRMEdge.source")
    sink_node = relationship("OSRMNode", foreign_keys="OSRMEdge.sink")
    distance = Column(Integer)
    weight = Column(Integer)
    bidirectional = Column(Boolean)

    def __init__(self, source, sink, distance, weight, bidirectional, name_id):
        self.hash = self.hash_route(source, sink, name_id)
        self.source = source
        self.sink = sink
        self.distance = distance
        self.weight = weight
        self.bidirectional = bool(bidirectional)
        self.name_id = name_id

    @staticmethod
    def hash_route(*xs):
        """Generate a hash of the identifying info"""
        return hash(xs)


class OSRMEdgeGeom(Base):
    """Defines the geometry of the Edge"""
    __tablename__ = "osrmedgegeoms"
    edge_hash = Column(BigInteger, ForeignKey('osrmedges.hash'),
                       primary_key=True)
    edge = relationship("OSRMEdge", backref='geometry')
    geom = GeometryColumn(Point(2), comparator=PGComparator)

    @staticmethod
    def build_geometry(start_lat, start_lon, end_lat, end_lon):
        return WKTSpatialElement(
            "LINESTRING(%0.6f %0.6f, %0.6f %0.6f)" % (
                start_lon/1E5, start_lat/1E5,
                end_lon/1E5, end_lat/1E5,
            ))


class OSRMRoute(Base):
    """Definte a toy, random route, run using the OSRM engine"""
    __tablename__ = "osrmroute"

    route_hash = Column(BigInteger, primary_key=True)
    start_lat = Column(Integer)
    start_lon = Column(Integer)
    end_lat = Column(Integer)
    end_lon = Column(Integer)
    duration = Column(Integer)
    nsteps = Column(Integer)

    @staticmethod
    def hash_route(*xs):
        """Generate an MD5 hash of the route info"""
        return hash(xs)


class OSRMRouteStep(Base):
    __tablename__ = "osrmroutestep"
    route_hash = Column(BigInteger, ForeignKey('osrmroute.route_hash'),
                        primary_key=True)
    route = relationship('OSRMRoute', backref='steps')
    step_idx = Column(Integer, primary_key=True)
    start_node_id = Column(Integer, ForeignKey('osrmnodes.osm_id'))
    end_node_id = Column(Integer, ForeignKey('osrmnodes.osm_id'))
    start_node = relationship(
        "OSRMNode", foreign_keys="OSRMRouteStep.start_node_id")
    end_node = relationship(
        "OSRMNode", foreign_keys="OSRMRouteStep.end_node_id")

    geom = GeometryColumn(LineString(2), comparator=PGComparator)

    @staticmethod
    def build_geometry(start_lat, start_lon, end_lat, end_lon):
        return WKTSpatialElement(
            "LINESTRING(%0.6f %0.6f, %0.6f %0.6f)" % (
                start_lon/1E5, start_lat/1E5,
                end_lon/1E5, end_lat/1E5,
            ))


GeometryDDL(OSRMNode.__table__)
GeometryDDL(OSRMEdge.__table__)
GeometryDDL(OSRMEdgeGeom.__table__)
GeometryDDL(OSRMRouteStep.__table__)
