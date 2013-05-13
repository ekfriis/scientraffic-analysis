-- run me as: psql osrm osm < build-views.sql

CREATE OR REPLACE VIEW routed_edges AS
  SELECT 
    step.edge_id AS edge, 
    COUNT(step.edge_id) AS freq,
    geoms.geom AS geom
  FROM osrmroutestep AS step
  INNER JOIN osrmedgegeoms AS geoms ON geoms.hash = step.edge_id
  GROUP BY step.edge_id, geoms.geom;
