#!/bin/bash

set -o allexport
source prod.env
set +o allexport

python -m eventbot