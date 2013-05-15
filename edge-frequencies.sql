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

-- Now do a version with merged forward-backwards and 
-- populated geometry for easy QGIS viewing.
DROP TABLE edgefrequencies_bothways;
CREATE TABLE edgefrequencies_bothways (
  edge BIGINT NOT NULL,
  freq BIGINT,
  logfreq FLOAT,
  PRIMARY KEY (edge)
);

SELECT AddGeometryColumn('public', 'edgefrequencies_bothways', 'geom', 4326, 'LINESTRING', 2);

INSERT INTO edgefrequencies_bothways (edge, freq, logfreq, geom)
SELECT 
  edges.edge,
  SUM(edges.freq),
  LOG(SUM(edges.freq)),
  geoms.geom
FROM edgefrequencies AS edges
INNER JOIN osrmedgegeoms AS geoms ON geoms.hash = edges.edge
GROUP BY edges.edge, geoms.geom;

CREATE INDEX "idx_edgefrequencies_bothways_geom" ON "public"."edgefrequencies_bothways" USING GIST (geom);
