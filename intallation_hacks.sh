#!/bin/bash
# http://gis.stackexchange.com/questions/28966/python-gdal-package-missing-header-file-when-installing-via-pip
pip install --no-install GDAL
pushd venv/build/GDAL/
python setup.py build_ext --include-dirs=/usr/include/gdal/
popd
pip install --no-download GDAL
