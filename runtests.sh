#!/bin/bash

export PYTHONPATH=.
find . -name '*_tests.py' | xargs py.test 
