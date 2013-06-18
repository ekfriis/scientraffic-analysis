-- Given the dissolved census tract table, and the polygonized routes,
-- associate census tracts -> edgefreq polys by their overlapping area.

DROP TABLE census_tract_overlaps;

CREATE TABLE census_tract_overlaps (
  censusid INT,
  routepolyid INT,
  overlap FLOAT,
  PRIMARY KEY(censusid, routepolyid)
);

INSERT INTO census_tract_overlaps (censusid, routepolyid, overlap)
SELECT 
   census.ogc_fid AS censusid,
   route.id AS routepolyid,
   ST_Area(ST_Intersection(census.geom, route.geom))
 FROM 
      tl_2011_06_tract_buffered AS census,
      edgefreqpolys AS route
 WHERE ST_Intersects(route.geom, census.geom);

-- each tract gets associated to a route id by highest area
-- then tracts are merged together into blocks
DROP TABLE associated_census_tracts;

CREATE TABLE associated_census_tracts (
   routepolyid INT,
   censusid INT
);

INSERT INTO associated_census_tracts (routepolyid, censusid)
SELECT ass.routepolyid, ass.censusid
FROM census_tract_overlaps AS ass
INNER JOIN (
  SELECT 
  max(overlap) AS overlap, 
  censusid AS censusid
  FROM census_tract_overlaps 
  GROUP BY censusid
) best ON ass.censusid = best.censusid AND best.overlap = ass.overlap;

-- now associate all the geometries.

DROP TABLE route_blocks;
CREATE TABLE route_blocks (
   blockid SERIAL
);

SELECT AddGeometryColumn('public', 'route_blocks', 'geom', 4326, 'MULTIPOLYGON', 2);

INSERT INTO route_blocks (geom)
SELECT
   ST_Transform(ST_Multi(ST_Union(census.wkb_geometry)), 4326)
FROM associated_census_tracts ass
JOIN tl_2011_06_tract AS census ON census.ogc_fid = ass.censusid
GROUP BY ass.routepolyid;

CREATE INDEX "idx_route_blocks" ON "public"."route_blocks" USING GIST (geom);
