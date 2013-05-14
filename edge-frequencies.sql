-- Determine the frequency a give edge (road segment) is
-- traveled through in randomly selected routes.

-- run me as: psql osrm osm < edge-frequencies.sql

DROP TABLE edgefrequencies;

EXPLAIN SELECT 
  step.edge_id AS edge, 
  step.forward AS forward, 
  COUNT(*) AS freq,
  geoms.geom AS geom
INTO 
  edgefrequencies
FROM 
  osrmroutesteps AS step
INNER JOIN 
  osrmedgegeoms AS geoms ON geoms.hash = step.edge_id
GROUP BY step.edge_id, step.forward, geoms.geom;

EXPLAIN SELECT 
  step.edge_id AS edge, 
  step.forward AS forward, 
  COUNT(*) AS freq
INTO 
  edgefrequencies
FROM 
  osrmroutesteps AS step
GROUP BY step.edge_id, step.forward;
