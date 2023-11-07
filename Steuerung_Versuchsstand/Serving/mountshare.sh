#!/bin/bash

# Check if the .credentials file exists
credentials_file=".credentials"
if [ ! -f "$credentials_file" ]; then
  echo "Error: The .credentials file does not exist."
  exit 1
fi

# Source the .credentials file to load the variables
source "$credentials_file"

# Create the mount point directory if it doesn't exist
if [ ! -d "$mount_point" ]; then
  sudo mkdir -p "$mount_point"
fi

# Mount the CIFS share
sudo mount.cifs //"$server"/"$share" "$mount_point" -o username="$username",password="$password"

# Check if the mount was successful
if [ $? -eq 0 ]; then
  echo "CIFS share mounted successfully."
else
  echo "Failed to mount the CIFS share."
fi
