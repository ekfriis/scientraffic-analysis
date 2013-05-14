'''

Create a simple PostGIS test DB for unit tests

'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy import GeometryDDL

from stanalysis.models import OSRMEdge, OSRMNode, Base  # flake8: noqa

engine = create_engine('postgresql://osm:osm@localhost/osm_test', echo=True)
Session = sessionmaker(bind=engine)
#session = Session()

def create_tables():
    """Create test tables"""
    Base.metadata.create_all(engine)

def drop_tables():
    """Drop existing test tables"""
    Base.metadata.drop_all(engine)
