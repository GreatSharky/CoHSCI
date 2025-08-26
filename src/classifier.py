"""This one will classify the segmented image"""
from gemma3_agent import VLM_gemma
import numpy as np
# import logging
# import os
# from pathlib import Path

from messageq import MessageQueue
from settings import config

# os.makedirs("../log", exist_ok=True)

# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s: %(filename)s - %(message)s",
#     handlers= [
#         logging.FileHandler("../log/classifier.log"),
#         logging.StreamHandler()
#         ]
# )
# logger = logging.getLogger(__name__)


class Classifier():
    def __init__(self, descriptions, model):
        self.descriptions = descriptions
        self.vlm1 = VLM_gemma(model, descriptions)
        self.control_reciever = MessageQueue("control-classifier")
        self.control_sender = MessageQueue("classifier-control")
        self.control_reciever.get_blocking_msg(self.classify)

    def classify(self, ch, method, properties, body):
        print("Message recieved")
        print("Classifying...")
        data = {"status" : "Image_recieved"}
        self.control_sender.add_msg(data)
        data = MessageQueue.body_parse_util(body)
        image = data["img"]
        self.vlm1.create_user_msg(image)
        result1 = self.vlm1.inference()
        classification = result1.message.content
        if "lass" in classification:
            classification = classification[len("Class "):]
        data = {
            "status" : "Classified",
            "result" : f"{classification}",
            "msg" : self.descriptions[int(classification)],
            "img" : data["img"]
        }
        self.control_sender.add_msg(data)
        return

if __name__ == "__main__":

    descriptions = config["classifier"]["emoji_prompts"]
    classifier = Classifier(descriptions, "gemma3:12b")
