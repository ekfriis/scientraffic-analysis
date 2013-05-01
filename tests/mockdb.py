'''

Create a simple PostGIS test DB for unit tests

'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import OSRMEdge, OSRMNode  # flake8: noqa

engine = create_engine('postgresql://osm:osm@localhost/osm', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
