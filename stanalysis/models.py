# -*- coding: utf-8 -*-
"""

GeoAlchemy PostGIS models

"""

from geoalchemy import GeometryColumn, Point, WKTSpatialElement, GeometryDDL
from geoalchemy.postgis import PGComparator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class OSRMNode(Base):
    __tablename__ = "osrmnodes"

    osm_id = Column(Integer, primary_key=True)
    lat = Column(Integer)
    lon = Column(Integer)
    bollard = Column(Boolean)
    traffic_light = Column(Boolean)
    geom = GeometryColumn(Point(2), comparator=PGComparator)
    # Edges associated to this node
    #in_edges = relationship("OSRMEdge", foreign_keys=['osrmedges.sink'])
    #out_edges = relationship("OSRMEdge", foreign_keys=['osrmedges.source'])

    def __init__(self, osm_id, lat, lon, bollard, traffic_light):
        self.osm_id = osm_id
        self.lat = lat
        self.lon = lon
        self.bollard = bollard
        self.traffic_light = traffic_light
        self.geom = WKTSpatialElement(
            "POINT(%0.2f %0.2f)" % (lon/1E5, lat/1E5))


class OSRMEdge(Base):
    __tablename__ = "osrmedges"

    id = Column(Integer, primary_key=True)
    source = Column(Integer, ForeignKey('osrmnodes.osm_id'))
    sink = Column(Integer, ForeignKey('osrmnodes.osm_id'))
    source_node = relationship(
        "OSRMNode", primaryjoin="OSRMNode.osm_id==OSRMEdge.source")
    sink_node = relationship(
        "OSRMNode", primaryjoin="OSRMNode.osm_id==OSRMEdge.sink")
    distance = Column(Integer)
    weight = Column(Integer)
    bidirectional = Column(Boolean)

    def __init__(self, id, source, sink, distance, weight, bidirectional):
        self.id = id
        self.source = source
        self.sink = sink
        self.distance = distance
        self.weight = weight
        self.bidirectional = bidirectional

GeometryDDL(OSRMNode.__table__)
GeometryDDL(OSRMEdge.__table__)
