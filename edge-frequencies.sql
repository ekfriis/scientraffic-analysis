-- run me as: psql osrm osm < edge-frequencies.sql

DROP TABLE edgefrequencies;

SELECT 
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
