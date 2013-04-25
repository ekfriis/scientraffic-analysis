# If a command fails, don't let HDF5 make a turd file
.DELETE_ON_ERROR:

# Output target template
OUTPUT=CITY/graph.hdf5\
       CITY/routes.hdf5\
       CITY/roads.geojson\
       CITY/intersections.geojson

LA_TARGETS=$(subst CITY,lax,$(OUTPUT))

la: $(LA_TARGETS)

ROAD_DATA=gisdata/ne_10m_roads_north_america.shp
LAND_DATA=gisdata/ne_10m_land.shp 

data: $(ROAD_DATA) $(LAND_DATA)

gisdata/ne_10m_land.shp:
	mkdir -p gisdata
	cd gisdata && wget http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_land.zip
	cd gisdata && unzip ne_10m_land.zip

gisdata/ne_10m_roads_north_america.shp:
	mkdir -p gisdata
	cd gisdata && wget http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_roads_north_america.zip
	cd gisdata && unzip ne_10m_roads_north_america.zip:

# Convert OSRM binary file format into HDF5
%/graph.hdf5: %/graph.osrm osrm2hdf5.py
	./osrm2hdf5.py $< $@

# Run a few toy routes
%/routes.hdf5: %/graph.hdf5 runroutes.py
	./runroutes.py --threads 3 -n 50000 -v -c 10.211.55.3 -p 8080 $< $@

# Apply the bounding box on the roads
%/roads.geojson: %/cfg/boundingbox $(ROAD_DATA) 
	rm -f $@
	ogr2ogr  -clipsrc `echo $<`  -where "'type' != 'Ferry'" -f "GeoJSON" $@ $(ROAD_DATA)

# Find the most common intersections ued in the toy routes
%/intersections.json: %/routes.hdf5 graphroutes.py
	./graphroutes.py -v $< $@

# Delaunuy triangulate the intersections and store them in a GeoJSON
%/triangulated_intersections.json: %/scoredroutes.hdf5 %/graph.hdf5 triangulate.py
	./triangulate.py $*/scoredroutes.hdf5 $*/graph.hdf5 $@ 
