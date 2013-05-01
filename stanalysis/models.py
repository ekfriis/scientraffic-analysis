# -*- coding: utf-8 -*-
"""

GeoAlchemy PostGIS models

"""

from geoalchemy import GeometryColumn, Point
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
    edges = relationship("OSRMEdge")

    def __init__(self, osm_id, lat, lon, bollard, traffic_light):
        self.osm_id = osm_id
        self.lat = lat
        self.lon = lon
        self.bolalrd = bollard
        self.traffic_light = traffic_light
        self.geom = Point(lon/1E5, lat/1E5)


class OSRMEdge(Base):
    __tablename__ = "osrmedges"

    id = Column(Integer, primary_key=True)
    node_a = Column(Integer, ForeignKey('osrmnodes.osm_id'))
    node_b = Column(Integer, ForeignKey('osrmnodes.osm_id'))
    distance = Column(Integer)
    weight = Column(Integer)
    bidirectional = Column(Boolean)

    def __init__(self, id, node_a, node_b, distance, weight, bidirectional):
        self.id = id
        self.node_a = node_a
        self.node_b = node_b
        self.distance = distance
        self.weight = weight
        self.bidirectional = bidirectional
