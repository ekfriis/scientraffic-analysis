# If a command fails, don't let HDF5 make a turd file
.DELETE_ON_ERROR:

# Output target template
OUTPUT=CITY/graph.hdf5\
       CITY/routes.hdf5\
       CITY/scoredroutes.hdf5

LA_TARGETS=$(subst CITY,lax,$(OUTPUT))

la: $(LA_TARGETS)

# Convert OSRM binary file format into HDF5
%/graph.hdf5: %/graph.osrm osrm2hdf5.py
	./osrm2hdf5.py $< $@

# Run a few toy routes
%/routes.hdf5: %/graph.hdf5 runroutes.py
	./runroutes.py --threads 3 -n 50000 -v -c 10.211.55.3 -p 8080 $< $@

# Find the most common intersections ued in the toy routes
%/scoredroutes.hdf5: %/routes.hdf5 graphroutes.py
	./graphroutes.py $< $@

# Delaunuy triangulate the intersections and store them in a GeoJSON
%/triangulated_intersections.json: %/scoredroutes.hdf5 %/graph.hdf5 triangulate.py
	./triangulate.py $*/scoredroutes.hdf5 $*/graph.hdf5 $@ 
