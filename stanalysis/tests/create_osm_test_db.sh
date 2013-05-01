#!/bin/bash
createdb -E UNICODE -O osm osm_test
createlang plpgsql osm_test
psql -d osm_test -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
psql -d osm_test -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql

#Grant permissions to user 'gis' on the new database
echo "grant all on database osm_test to osm;" | psql -d osm_test
echo "grant all on spatial_ref_sys to osm;" | psql -d osm_test
echo "grant all on geometry_columns to osm;" | psql -d osm_test
