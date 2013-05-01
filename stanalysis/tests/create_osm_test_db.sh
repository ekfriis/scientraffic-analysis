#!/bin/bash
createdb -E UNICODE -O osm osm_test
createlang plpgsql osm_test
psql -d osm_test -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
psql -d osm_test -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql

#Grant permissions to user 'gis' on the new database
echo "ALTER TABLE geometry_columns OWNER TO osm;" | psql -d osm_test
echo "ALTER TABLE spatial_ref_sys OWNER TO osm;" | psql -d osm_test
echo "ALTER USER osm WITH PASSWORD 'osm';" | psql -d osm_test
