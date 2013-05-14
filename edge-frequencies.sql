-- Determine the frequency a give edge (road segment) is
-- traveled through in randomly selected routes.

-- run me as: psql osrm osm < edge-frequencies.sql

DROP TABLE edgefrequencies;

CREATE TABLE edgefrequencies (
  edge BIGINT NOT NULL,
  forward BOOLEAN NOT NULL,
  freq BIGINT,
  PRIMARY KEY (edge, forward)
);

INSERT INTO  edgefrequencies (edge, forward, freq)
SELECT 
  step.edge_id AS edge, 
  step.forward AS forward, 
  COUNT(*) AS freq
FROM 
  osrmroutesteps AS step
  GROUP BY step.edge_id, step.forward;

CREATE INDEX "idx_edgefrequences_edge" ON edgefrequencies (edge);

-- Add geometry column for easy QGIS viewing.
SELECT AddGeometryColumn('public', 'edgefrequencies', 'geom', 4326, 'LINESTRING', 2);

-- Populate geometry
EXPLAIN UPDATE edgefrequencies freq SET geom = geoms.geom
FROM osrmedgegeoms geoms WHERE freq.edge = geoms.hash;

UPDATE edgefrequencies freq SET geom = geoms.geom
FROM osrmedgegeoms geoms WHERE freq.edge = geoms.hash;

CREATE INDEX "idx_edgefrequencies_geom" ON "public"."edgefrequencies" USING GIST (geom);
