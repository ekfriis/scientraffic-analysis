-- Make polygons out of the most frequently traveled edges

-- run me as: psql osrm osm < polygonize-edge-frequencies.sql

DROP TABLE edgefreqpolys;

SELECT (ST_Dump(foo.polycoll)).geom 
  INTO edgefreqpolys
FROM (
  SELECT ST_Polygonize(ST_LineMerge(ST_Multi(geom))) AS polycoll
  FROM edgefrequencies_bothways WHERE freq > 1
) AS foo;
