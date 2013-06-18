-- Make polygons out of the most frequently traveled edges

-- run me as: psql osrm osm < polygonize-edge-frequencies.sql

-- Inspired by:

-- http://www.spatialdbadvisor.com/postgis_tips_tricks/120/building-polygons-from-overlapping-linestrings-requiring-intersection/


DROP TABLE exploded_lines_tmp;
select e.edge AS edge, (ST_Dump(e.geom)).geom AS geom
INTO exploded_lines_tmp
from (SELECT /* This query is the set of each line with each and every line that intersects it */
  c.edge AS edge, ST_Intersection(c.orig_geom, ST_SymDifference((select a.geom from edgefrequencies_bothways a where a.edge = c.edge),c.geom)) as geom
  FROM (select a.edge as edge, a.geom as orig_geom, ST_Collect(b.geom) as geom
    from edgefrequencies_bothways a, 
    edgefrequencies_bothways b
    where a.freq > 1 
    and a.edge <> b.edge
    and ST_Intersects(a.geom,b.geom)
    group by a.edge
  ) as c
) e;

INSERT INTO exploded_lines_tmp
SELECT edge.edge, edge.geom FROM edgefrequencies_bothways AS edge 
WHERE NOT EXISTS (SELECT * FROM exploded_lines_tmp AS sploded WHERE sploded.edge = edge.edge);

CREATE INDEX "idx_exploded_lines_tmp_geom" ON "public"."exploded_lines_tmp" USING GIST (geom);

DROP TABLE edgefreqpolys;

select (ST_Dump(p.geom)).geom as geom
into edgefreqpolys 
from (select ST_Polygonize(ST_LineMerge(ST_Multi(f.geom))) as geom
    --from edgefrequencies_bothways f
    from (select e.geom AS geom from exploded_lines_tmp e) AS f
  ) AS p;
