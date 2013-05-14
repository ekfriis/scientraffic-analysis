'''

Create a simple PostGIS test DB for unit tests

'''

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy import GeometryDDL

from stanalysis.models import OSRMEdge, OSRMNode, Base  # flake8: noqa

engine = create_engine('postgresql://osm:osm@localhost/osm_test', echo=False)
Session = sessionmaker(bind=engine)

def _create_tables():
    """Create test tables"""
    Base.metadata.create_all(engine)

def _drop_tables():
    """Drop existing test tables"""
    Base.metadata.drop_all(engine)

@contextmanager
def test_db_session():
    """ Context manager to create a temporary DB session

    Cleans up after itself.
    """
    try:
        _drop_tables()
        _create_tables()
        _session = Session()
        yield _session
    finally:
        _session.commit()
        _session.close()
        _drop_tables()
