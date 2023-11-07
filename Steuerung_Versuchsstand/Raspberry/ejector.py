"""Module controlling the ejector via raspberry pi GPIO."""
import time
import RPi.GPIO as GPIO


class Ejector:
    """Class containing functions to eject objects"""

    def __init__(self, pin_1):
        """Initialize the Ejector with a GPIO pin."""
        self.pin_1 = pin_1

    def _set_output(self, value):
        """Set the GPIO pin to the given value (1 or 0)."""
        GPIO.output(self.pin_1, value)

    def extend(self):
        """Extend the ejector."""
        self._set_output(1)

    def retract(self):
        """Retract the ejector."""
        self._set_output(0)

    def eject_object(self):
        """Extend the ejector for 0.5 seconds and then retract it."""
        self.extend()
        time.sleep(0.5)
        self.retract()
