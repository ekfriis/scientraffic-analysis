-- run me as: psql osrm osm < edge-frequencies

DROP TABLE edgefrequencies;

SELECT 
  step.edge_id AS edge, 
  COUNT(step.edge_id) AS freq,
  geoms.geom AS geom
INTO 
  edgefrequencies
FROM 
  osrmroutestep AS step
INNER JOIN 
  osrmedgegeoms AS geoms ON geoms.hash = step.edge_id
GROUP BY step.edge_id, geoms.geom;
