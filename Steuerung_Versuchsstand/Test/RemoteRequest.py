import requests
import cv2
import json

# MLL EXAMPLE
server_address = "http://147.189.198.238:8501/v1/models/ResNet:predict"

image = cv2.imread("TestKronkorken.jpg")
image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_LINEAR)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
print(type(image))
image = image / 255.0
image = image.tolist()  # ndarry to list, which is JSON serializable
print(type(image))
print(len(image))
print(image[0][0])

# Create a request
data = json.dumps({"instances": [image]})
headers = {"content-type": "application/json"}
response = requests.post(server_address, data=data, headers=headers)

predictions = json.loads(response.text)["predictions"]
print(f"predictions: {predictions}")
