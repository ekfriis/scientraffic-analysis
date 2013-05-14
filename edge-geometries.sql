-- run me as: psql osrm osm < edge-geometries.sql

DROP TABLE osrmedgegeoms;
SELECT osrmedges.hash, ST_MakeLine(source.geom, sink.geom) AS geom INTO osrmedgegeoms
  FROM osrmedges
  INNER JOIN osrmnodes AS source ON osrmedges.source = source.osm_id
  INNER JOIN osrmnodes AS sink ON osrmedges.sink = sink.osm_id
;

ALTER TABLE osrmedgegeoms ADD PRIMARY KEY (hash);
