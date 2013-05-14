-- Determine the frequency a give edge (road segment) is
-- traveled through in randomly selected routes.

-- run me as: psql osrm osm < edge-frequencies.sql

DROP TABLE edgefrequencies_tmp;

CREATE TABLE edgefrequencies_tmp (
  edge BIGINT NOT NULL,
  forward BOOLEAN NOT NULL,
  freq BIGINT,
  PRIMARY KEY (edge, forward)
);

INSERT INTO  edgefrequencies_tmp (edge, forward, freq)
SELECT 
  step.edge_id AS edge, 
  step.forward AS forward, 
  COUNT(*) AS freq
FROM 
  osrmroutesteps AS step
  GROUP BY step.edge_id, step.forward;

CREATE INDEX "idx_edgefrequences_edge" ON edgefrequencies_tmp (edge);

-- Now do a version with populated geometry for easy QGIS viewing.
DROP TABLE edgefrequencies;
CREATE TABLE edgefrequencies (
  edge BIGINT NOT NULL,
  forward BOOLEAN NOT NULL,
  freq BIGINT,
  PRIMARY KEY (edge, forward)
);

SELECT AddGeometryColumn('public', 'edgefrequencies', 'geom', 4326, 'LINESTRING', 2);

INSERT INTO edgefrequencies (edge, forward, freq, geom)
SELECT 
  edges.edge,
  edges.forward,
  edges.freq,
  geoms.geom
FROM edgefrequencies_tmp AS edges
INNER JOIN osrmedgegeoms AS geoms ON geoms.hash = edges.edge;

CREATE INDEX "idx_edgefrequencies_geom" ON "public"."edgefrequencies" USING GIST (geom);
DROP TABLE edgefrequencies_tmp;
