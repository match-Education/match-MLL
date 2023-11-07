import json
import requests

hostname = "147.189.198.238"

api_address = f"http://{hostname}:8505/get_models"
response = requests.get(api_address)
models = json.loads(response.text)

print(models)