import cv2
import numpy as np
import json

from messageq import MessageQueue
from vlm_agent import VLM


class Validator(VLM):
    def __init__(self, model):
        super().__init__(model)
        self.control_reciever = MessageQueue("control-validator")
        self.control_sender = MessageQueue("validator-control")
        #self.create_system_prompt()
        self.control_reciever.get_blocking_msg(callback=self.classifier_callback)

    def create_system_prompt(self):
        msg = {
            "role" : "user",
            "content" : "Give a score between 0 and 100 how well the description matches the image. Give only numerical answer."
        }
        self.system_msgs = [msg]

    def create_user_prompt(self, description: str, image: np.ndarray):
        img = self.get_image(image)
        msg = {
            "role" : "user",
            "content" : f"How well does {description} match the image? Give aswer only in percentage points.",
            "images" : [img]
        }
        self.user_msgs = [msg]

    def classifier_callback(self, ch, method, properties, body):
        print("Classification recieved")
        data = {"status" : "Validation_started"}
        self.control_sender.add_msg(data)
        body = MessageQueue.body_parse_util(body)
        description, img = self.parse_body(body)
        print("Body parsed")
        print(description)
        self.create_user_prompt(description, img)
        result = self.inference()
        print(result)
        data = {"status" : "Validated",
                "result" : result.message.content}
        self.control_sender.add_msg(data)
        return

    def parse_body(self, body):
        img = body["img"]
        description = body["msg"]
        return description, img

if __name__ == "__main__":
    val = Validator("llama3.2-vision")
