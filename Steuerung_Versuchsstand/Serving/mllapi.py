"""This module provides a REST API for the TensorFlow Serving models.
The API is based on the Flask framework.
"""
from flask import Flask, jsonify
import os
import shutil

app = Flask(__name__)

credentials_file = ".credentials"

# Create a dictionary to store the variables
credentials = {}

try:
    # Open and read the .credentials file
    with open(credentials_file, "r") as file:
        for line in file:
            # Remove leading and trailing whitespace
            line = line.strip()
            # Ignore lines starting with #
            if not line.startswith("#"):
                # Split the line into key and value if it contains an equal sign
                if "=" in line:
                    key, value = line.split("=", 1)
                    credentials[key] = value.strip(' "')
except FileNotFoundError:
    print(f"Error: The {credentials_file} file does not exist.")
    exit(1)


def create_model_config_entry(name, base_path, model_platform):
    """Creates a model config entry for the models.config file.
    Args:
        name (str): The name of the model.
        base_path (str): The base path of the model.
        model_platform (str): The model platform.
    Returns:
        str: The model config entry.
    """
    entry = f"  config {{\n    name: '{name}'\n    base_path: '{base_path}'\n    model_platform: '{model_platform}'\n  }}"
    return entry


@app.route("/get_models", methods=["GET"])
def get_models():
    """Returns a list of all models.
    Returns:
        list: A list of all models.
    """
    try:
        # TODO: make base_path variable
        base_path = credentials.get("mount_point") + "/Netze"
        models_list = [
            d
            for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d))
        ]
        return jsonify(models_list)
    except FileNotFoundError:
        return "No models found", 404


@app.route("/create_config", methods=["GET"])
def create_config():
    """Creates a models.config file.
    Returns:
        str: The models.config file.
    """
    try:
        # TODO: make base_path variable
        base_path = credentials.get("mount_point") + "/Netze"
        output_file = os.path.join(base_path, "models.config")

        model_configs = []

        for model_dir in os.listdir(base_path):
            model_path = os.path.join(base_path, model_dir)
            if os.path.isdir(model_path):
                model_config = create_model_config_entry(
                    model_dir, "/models/" + model_dir, "tensorflow"
                )
                model_configs.append(model_config)

        with open(output_file, "w") as f:
            f.write("model_config_list {\n")
            for model_config in model_configs:
                f.write(model_config + "\n")
            f.write("}")
        return jsonify(model_configs)

    except FileNotFoundError:
        return "No models found", 404


# TODO: Create endpoint to copy models from network drive to local drive
@app.route("/copy_models", methods=["GET"])
def copy_models():
    try:
        # Source and destination folders
        source_folder = credentials.get("mount_point") + "/Netze"
        home_dir = os.path.expanduser("~")
        destination_folder = os.path.join(home_dir, "models")

        if not source_folder or not destination_folder:
            return (
                jsonify(
                    {"error": "Both source_folder and destination_folder are required"}
                ),
                400,
            )

        # Check if the source folder exists
        if not os.path.exists(source_folder):
            return jsonify({"error": "Source folder does not exist"}), 400

        # Create the destination folder if it doesn't exist
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Copy the contents of the source folder to the destination folder
        for item in os.listdir(source_folder):
            source_item = os.path.join(source_folder, item)
            destination_item = os.path.join(destination_folder, item)
            if os.path.isdir(source_item):
                shutil.copytree(source_item, destination_item)
            else:
                shutil.copy2(source_item, destination_item)

        return jsonify({"message": "Folders copied successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
