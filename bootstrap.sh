#!/bin/bash

set -o allexport
source prod.env
set +o allexport

python -m eventbot.application.drop_database
python -m eventbot.application.bootstrap