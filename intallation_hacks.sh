#!/bin/bash

# Various workarounds for pip problems.  
# Run me before pip install -r requirements.txt

# http://gis.stackexchange.com/questions/28966/python-gdal-package-missing-header-file-when-installing-via-pip
if [ ! -d "venv/lib/python2.7/site-packages/osgeo" ]; then
  echo "Installing GDAL"
  pip install --no-install GDAL
  pushd venv/build/GDAL/
  python setup.py build_ext --include-dirs=/usr/include/gdal/
  popd
  pip install --no-download GDAL
fi

if [ ! -L  venv/lib/python2.7/site-packages/igraph ]; then
  echo "symlinking igraph from apt installation"
  pushd venv/lib/python2.7/site-packages/
  ln -s /usr/lib/python2.7/dist-packages/igraph igraph
  popd
fi

echo "installing numpy & friends"
pip install numpy==1.7.0 numexpr==2.0.1 Cython==0.18

echo "installing scipy"
pip install git+http://github.com/scipy/scipy/@v0.12.0b1
