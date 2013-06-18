#!/bin/bash

# Downloads (if necessary) and imports census tract data into PostGIS

if [ ! -f tl_2011_06_tract.zip ];
then
  wget http://www2.census.gov/geo/tiger/TIGER2011/TRACT/tl_2011_06_tract.zip
fi

unzip -o tl_2011_06_tract.zip

# Note: I don't undertand the -nlt option, but see:
# http://trac.osgeo.org/gdal/ticket/4939

ogr2ogr -overwrite -nlt MULTIPOLYGON -f "PostgreSQL" \
  PG:"host=localhost user=osm dbname=osrm password=osm" \
  tl_2011_06_tract.shp \
  -clipdst -119.44628 33.13301 -116.96712 34.42179 \
  -clipdstsql "WHERE ALAND > 0"  # ignore water only tracts


ls tl_2011_06_tract.* | grep -v zip | xargs rm

# Buffer 
echo "Creating dissolved census tracts"
echo "DROP TABLE tl_2011_06_tract_buffered;" | psql osrm osm
echo "select aland, ogc_fid, ST_Buffer(wkb_geometry, -1E-3) AS geom INTO tl_2011_06_tract_buffered from tl_2011_06_tract where aland > 0;" | psql osrm osm
echo "CREATE INDEX idx_tl_2011_06_tract_buffered  ON tl_2011_06_tract_buffered USING GIST (geom);" | psql osrm osm
