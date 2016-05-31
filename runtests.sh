#!/bin/bash

export PYTHONPATH=.

if [[ -z $1 ]]; then
find . -name '*_tests.py'
else
    echo $*
fi | xargs py.test 
