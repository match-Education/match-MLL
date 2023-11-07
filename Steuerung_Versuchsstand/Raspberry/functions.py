"""This file contains helper functions to communicate with the arduido
as well as the interpreter for object detection"""
import time
import cv2
import serial
import requests
import json

import numpy as np
import RPi.GPIO as GPIO
from PIL import Image, ImageTk
from ejector import Ejector
import tkinter


arduino = serial.Serial("/dev/ttyACM0", baudrate=115200, timeout=10000)


def send_value_to_arduino(obj_class, obj_distance, obj_num):
    """
    This function sends the predicted class of the object and the distance
    til the corresponding ejector to the Arduino board via serial communication.
    It is also used for tracking the object position til the take-photo position.

    :param Class: Int: The class of the object (or take-photo flag).
    :param Length: Int: The distance to the ejector (or take-photo position).
    :return: None
    """
    mess = str(obj_class) + "," + str(obj_distance) + "," + str(obj_num) + ","
    arduino.write(mess.encode())


def receive_class():
    """
    This function receives from Arduino via serial communication the class of the object
    or the take-photo flag when it reaches the ejector or the take-photo position.

    :return: The class of the object (=> the ejector to be activated) or the take-photo flag.
    """
    data = arduino.readline().strip()
    data = data.decode("utf-8")
    if data == "":
        data = arduino.readline().strip()
        data = data.decode("utf-8")
    return int(data)


def set_input_tensor(interpreter, image):
    """
    Sets the input tensor.
    """

    tensor_index = interpreter.get_input_details()[0]["index"]
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = np.expand_dims((image), axis=0)


def get_output_tensor(interpreter, index):
    """
    Returns the output tensor at the given index.
    """

    output_details = interpreter.get_output_details()[index]
    tensor = np.squeeze(interpreter.get_tensor(output_details["index"]))
    return tensor


def detect_objects(interpreter, image, threshold):
    """
    Returns a list of detection results, each a dictionary of object info.
    """
    set_input_tensor(interpreter, image)

    interpreter.invoke()

    # Get all output details
    scores = get_output_tensor(interpreter, 0)
    predicted_class = np.argmax(scores)

    if scores[predicted_class] > threshold:
        return predicted_class, scores[predicted_class]
    else:
        return None, None


def get_prediction(threshold, interpreter, image):
    """
    Returns the prdicted class index and the prediction score.
    If the score is lower then the threshold, it returns 999.
    """

    _, input_height, input_width, _ = interpreter.get_input_details()[0]["shape"]

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image = cv2.resize(
        image, (input_width, input_height), interpolation=cv2.INTER_LINEAR
    )
    image = image / 255.0

    prediction_class, prediction_score = detect_objects(interpreter, image, threshold)

    if prediction_score is not None and prediction_score > threshold:
        return prediction_class, prediction_score
    else:
        return 999, prediction_score


def get_prediction_remote(threshold, image, hostname, model):
    # TODO: Implement, test and docstring
    prediction_score = None
    image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_LINEAR)
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image / 255.0
    image = image.tolist()  # ndarry to list, which is JSON serializable
    print(type(image))
    print(len(image))
    print(image[0][0])

    # Create a request
    data = json.dumps({"instances": [image]})
    headers = {"content-type": "application/json"}

    # hostname scheme: server_address = "http://127.0.0.1:8501/v1/models/ResNet:predict"
    serving_address = f"http://{hostname}:8501/v1/models/{model}:predict"
    print(serving_address)
    response = requests.post(serving_address, data=data, headers=headers)
    print(response.text)

    # TODO: Rewrite if possible
    try:
        # load predictions from json
        predictions = json.loads(response.text)["predictions"][0]
        prediction_score = max(predictions)
        prediction_class = predictions.index(prediction_score)
    except KeyError:
        # TODO exception type?
        prediction_score = 0

    # Use same behaviour as local interpreter
    if prediction_score is not None and prediction_score > threshold:
        return prediction_class, prediction_score
    else:
        return 999, prediction_score


def get_remote_models(hostname) -> list:
    api_address = f"http://{hostname}:8505/get_models"
    response = requests.get(api_address)
    models = json.loads(response.text)
    return models


def predict(app) -> None:
    """
    This function runs in another process.
    It captures the image and runs the inference.
    """
    app.state = "busy"

    if not (app.getnetze_ready() and app.getlabels_ready()):
        # Create preview image with crop frame, but dont run inference if no model is loaded

        app.capture = app.camera.capture_array()

        if app.grayscale_variable:
            # If grayscale toggle is active, the image array should be converted to grayscale
            app.capture = cv2.cvtColor(app.capture, cv2.COLOR_BGR2GRAY)

        # Add rectangle for crop frame
        app.capture = cv2.rectangle(
            app.capture,
            (app.x_offset, app.y_offset),
            (app.x_offset + app.crop_size, app.y_offset + app.crop_size),
            (211, 0, 0),
            3,
        )

        # Resize image to fit preview screen
        app.capture = cv2.resize(
            app.capture,  # cv2.cvtColor(app.capture, cv2.COLOR_BGR2RGB),
            (
                int(app.img_width * app.widget_scaling),
                int(app.img_height * app.widget_scaling),
            ),
            interpolation=cv2.INTER_AREA,
        )

        # create image from captures numpy array
        image = Image.fromarray(app.capture)

        app.preview_image = ImageTk.PhotoImage(image=image)
        app.image_preview_canvas.create_image(
            app.img_width / 2 * app.widget_scaling,
            app.img_height / 2 * app.widget_scaling,
            image=app.preview_image,
            anchor=tkinter.CENTER,
        )

        app.state = "idle"
        return

    # Model is loaded -> capture image and run inference
    auswurf_positionen = [230, 390, 565, 725]

    app.capture = app.camera.capture_array()

    crop = app.capture[
        app.y_offset : app.y_offset + app.crop_size,
        app.x_offset : app.x_offset + app.crop_size,
    ]

    if app.grayscale_variable:
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # DONE: If remote serving is true, send the image to the server and wait for the prediction
    # DONE: Ther is no proper way to load labels, as the model does not contain information for this

    if app.remote_serving_variable:
        predicted_class_index, confidence = get_prediction_remote(
            app.threshold.get() / 100,
            crop,
            app.hostname_var.get(),
            app.netz_choice.get(),
        )

    else:
        predicted_class_index, confidence = get_prediction(
            app.threshold.get() / 100, app.interpreter, crop
        )

    app.obj_num += 1

    if predicted_class_index in range(len(app.labels)):
        send_value_to_arduino(
            predicted_class_index,
            auswurf_positionen[predicted_class_index] - app.pos_offset.get(),
            app.obj_num,
        )

        confidence = round(confidence, 3)
        app.prediction = (
            app.labels[predicted_class_index] + f" (Confidence: {confidence*100:.0f}%)"
        )

        app.counters[app.labels[predicted_class_index]] += 1

        app.classes[predicted_class_index].set(
            f"{app.labels[predicted_class_index]}:\n\n{app.counters[app.labels[predicted_class_index]]}"
        )

        app.capture = cv2.rectangle(
            app.capture,
            (app.x_offset, app.y_offset),
            (app.x_offset + app.crop_size, app.y_offset + app.crop_size),
            (211, 0, 0),
            3,
        )

        app.capture = cv2.resize(
            app.capture,
            (
                int(app.img_width * app.widget_scaling),
                int(app.img_height * app.widget_scaling),
            ),
            interpolation=cv2.INTER_AREA,
        )

        app.info_text.set(
            f"Object N°: {app.obj_num} Prediction: {app.prediction} \tCrop-Parameters: ({app.x_offset}, {app.y_offset}); {app.crop_size}"
        )

    else:
        app.capture = cv2.rectangle(
            app.capture,
            (app.x_offset, app.y_offset),
            (app.x_offset + app.crop_size, app.y_offset + app.crop_size),
            (211, 0, 0),
            3,
        )
        app.capture = cv2.resize(
            app.capture,
            (
                int(app.img_width * app.widget_scaling),
                int(app.img_height * app.widget_scaling),
            ),
            interpolation=cv2.INTER_AREA,
        )

        app.info_text.set(
            f"Object N°: {app.obj_num} Prediction: Unknown!"
            f"\tCrop-Parameters: ({app.x_offset}, {app.y_offset}); {app.crop_size}"
        )

    app.preview_image = ImageTk.PhotoImage(image=Image.fromarray(app.capture))
    app.image_preview_canvas.create_image(
        app.img_width / 2 * app.widget_scaling,
        app.img_height / 2 * app.widget_scaling,
        image=app.preview_image,
        anchor=tkinter.CENTER,
    )

    app.state = "idle"


def eject_or_photo(
    event, PIN_Arduino, PIN_Ejector_1, PIN_Ejector_2, PIN_Ejector_3, PIN_Ejector_4
) -> None:
    """
    This functions runs in another process.
    It listens to the arduino signal via threaded event detection.
    """

    Ejector_1 = Ejector(PIN_Ejector_1)
    Ejector_2 = Ejector(PIN_Ejector_2)
    Ejector_3 = Ejector(PIN_Ejector_3)
    Ejector_4 = Ejector(PIN_Ejector_4)

    def eject_or_photo(self):
        """
        Callback function for the event of Arduino sending back the signal, that the object reached the ejector or the
        take-photo position.
        """

        time.sleep(0.002)
        received_class_index = receive_class()

        if received_class_index == 0:
            Ejector_1.eject_object()
        elif received_class_index == 1:
            Ejector_2.eject_object()
        elif received_class_index == 2:
            Ejector_3.eject_object()
        elif received_class_index == 3:
            Ejector_4.eject_object()
        elif received_class_index == 777:
            event.set()

    GPIO.add_event_detect(PIN_Arduino, GPIO.BOTH, callback=eject_or_photo)

    while True:
        # TODO: is this neccessary?
        continue


def wait_to_predict(app, event) -> None:
    """
    This function runs in another process.
    It waits for the event to be set and then calls the predict function.
    """
    while True:
        event.wait()
        event.clear()
        predict(app)


def light_barrier(app, PIN_Light_Barrier) -> None:
    """
    This function runs in another process.
    It listens to the light barrier signal via threaded event detection.
    """

    def send_value_to_arduino_callback(self):
        if app.state == "idle":
            send_value_to_arduino(777, app.pos_offset.get(), 1 + app.obj_num)
        else:
            pass

    GPIO.add_event_detect(
        PIN_Light_Barrier,
        GPIO.RISING,
        callback=send_value_to_arduino_callback,
        bouncetime=2000,
    )
