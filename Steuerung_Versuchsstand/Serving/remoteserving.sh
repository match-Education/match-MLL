#!/bin/bash

# Step 1: Execute the existing script "mountshare.sh" if it exists
echo "Step 1: Running 'mountshare.sh'"
./mountshare.sh

# Step 2: Launch the Python program "mllapi.py" in the background
echo "Step 2: Launching 'mllapi.py' in the background"
python mllapi.py &

# Wait for a short delay (adjust the sleep duration as needed)
sleep 5

# Step 3: Execute a curl GET request to http://localhost:8505/copy_models
echo "Step 3: Executing a GET request to http://localhost:8505/copy_models"
curl http://localhost:8505/copy_models

# Step 4: Execute another curl GET request to http://localhost:8505/create_config
echo "Step 4: Executing a GET request to http://localhost:8505/create_config"
curl http://localhost:8505/create_config

# Step 5: Execute the script "runserving.sh"
echo "Step 5: Executing 'launchcontainer.sh'"
./launchcontainer.sh

# Informative message for script completion
echo "All steps have been completed."
