#!/bin/bash

# Check if the .credentials file exists
credentials_file=".credentials"
if [ ! -f "$credentials_file" ]; then
  echo "Error: The .credentials file does not exist."
  exit 1
fi

# Source the .credentials file to load the variables
source "$credentials_file"

# Append Netze Folder mount_point to get path for models to serve
MODELPATH="$mount_point/Netze/"

# start serving
docker run -t --rm -p 8501:8501 -v "$MODELPATH:/models/" tensorflow/serving:latest-gpu --model_config_file=/models/models.config --model_config_file_poll_wait_seconds=60 -d
