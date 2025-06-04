import cv2
import numpy as np
import json

from messageq import MessageQueue
from vlm_agent import VLM


class Validator(VLM):
    def __init__(self, model, gestures, samples):
        super().__init__(model, gestures, samples)
        self.control_sender = MessageQueue("validator-control")
        self.control_reciever = MessageQueue("control-validator")
        self.classifier = MessageQueue("classifier-validator")
        self.create_system_prompt()
        self.classifier.get_blocking_msg(callback=self.classifier_callback)

    def create_system_prompt(self):
        msg = {
            "role" : "system",
            "content" : "How well the given description matches the given image. Give the output as a score between 0 and 100 where 0 means the description does not match the image at all and 100 means the description matches the image perfectly"
        }
        self.system_msgs = [msg]

    def create_user_prompt(self, description: str, image: np.ndarray):
        img = self.get_image(image)
        msg = {
            "role" : "user",
            "content" : description,
            "images" : [img]
        }
        self.user_msgs = [msg]

    def classifier_callback(self, ch, method, properties, body):
        self.control_sender.add_msg("Classfication recieved")
        description, img = self.parse_body(body)
        self.create_user_prompt(description, img)
        result = self.inference()
        print(result)
        self.control_sender.add_msg(result.message.content)
        return

    def parse_body(self, body):
        img = cv2.imload("99_cap.jpg")
        description = "Horse on top of a rainbow"
        return description, img
