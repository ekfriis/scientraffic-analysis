-- Make polygons out of the most frequently traveled edges

-- run me as: psql osrm osm < polygonize-edge-frequencies.sql

DROP TABLE edgefreqpolys;

SELECT (ST_Dump(foo.polycoll)).geom 
  INTO edgefreqpolys
FROM (
  SELECT ST_Polygonize(ST_LineMerge(ST_Multi(geom))) AS polycoll
  FROM edgefrequencies_bothways WHERE freq > 1
) AS foo;

-- select ST_AsText(ST_Polygonize(ST_LineMerge(ST_Multi(geom)))) from edgefrequencies_bothways where freq > 1;

--SELECT ST_AsEWKT((ST_Dump(foofoo.polycoll)).geom) As geomtextrep
--FROM (SELECT ST_Polygonize(the_geom_4269) As polycoll
        --FROM (SELECT the_geom_4269 FROM ma.suffolk_edges
                        --ORDER BY tlid LIMIT 45) As foo) As foofoo;
