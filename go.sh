#! /bin/sh
python hypercube.py $@
for f in $@*.tex; do tectonic $f; done
