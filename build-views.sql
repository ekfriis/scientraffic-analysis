-- run me as: psql osrm osm < build-views.sql

--CREATE OR REPLACE VIEW routed_edges AS
  --SELECT 
    --step.edge_id AS edge, 
    --COUNT(step.edge_id) AS freq,
    --geoms.geom AS geom
  --FROM osrmroutestep AS step
  --INNER JOIN osrmedgegeoms AS geoms ON geoms.hash = step.edge_id
  --GROUP BY step.edge_id, geoms.geom;

CREATE OR REPLACE VIEW routenodesgeom AS
  SELECT 
    routenode.osm_id AS id, 
    routenode.n_outputs AS n_outputs,
    routenode.sum_out AS sum_out,
    routenode.product_out AS product_out,
    routenode.log_sum_out AS log_sum_out,
    routenode.redundant AS redundant,
    node.geom AS geom
  FROM routenodes AS routenode
  INNER JOIN osrmnodes AS node ON node.osm_id = routenode.osm_id;
