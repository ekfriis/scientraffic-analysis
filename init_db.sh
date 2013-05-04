#!/bin/bash

# Create a PostGIS database.
# Usage: ./init_db.sh <dbname>

if [ "$#" -ne "1" ]
then
  echo "Usage: `basename $0` {dbname}"
  exit 1
fi

DBNAME=$1

createdb -E UNICODE -O osm $DBNAME
createlang plpgsql $DBNAME
psql -d $DBNAME -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
psql -d $DBNAME -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql

#Grant permissions to user 'gis' on the new database
echo "ALTER VIEW geography_columns OWNER TO osm;" | psql -d $DBNAME
echo "ALTER TABLE geometry_columns OWNER TO osm;" | psql -d $DBNAME
echo "ALTER TABLE spatial_ref_sys OWNER TO osm;" | psql -d $DBNAME
echo "ALTER USER osm WITH PASSWORD 'osm';" | psql -d $DBNAME
