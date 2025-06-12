"""This one will classify the segmented image"""
from gemma3_agent import VLM_gemma
import cv2
import numpy as np
from segment import file_index
import json

from messageq import MessageQueue

class Classifier():
    def __init__(self, gestures, descriptions, model):
        self.gestures = gestures
        self.descriptions = descriptions
        self.vlm1 = VLM_gemma(model, gestures, descriptions, 1)
        self.segmentor_reciever = MessageQueue("segmentor-classifier")
        self.webcam_sender = MessageQueue("classifier-webcam")
        self.control = MessageQueue("control-classifier")
        self.validator_sender = MessageQueue("classifier-validator")
        self.segmentor_reciever.get_blocking_msg(self.classify)

    def classify(self, ch, method, properties, body):
        print("Message recieved")
        print("Classifying...")
        self.control.add_msg("Image recieved")
        data = MessageQueue.body_parse_util(body)
        image = data["img"]
        self.vlm1.create_user_msg(image)
        result1 = self.vlm1.inference()
        classification = result1.message.content
        msg = {
            "msg" : self.descriptions[self.gestures[int(classification)]],
            "img" : data["img"]
        }
        print(f"Class {classification}")
        self.validator_sender.add_msg(msg)
        self.webcam_sender.add_msg(f"Class {classification}")
        self.control.add_msg(f"{classification}")
        return

if __name__ == "__main__":
    descriptions = {
        "-1" : "that there is no hand in the image.",
        "ok" : "it resembles the OK sign. The thumb and the index finger create an circle while the three other fingers are extended.",
        "1" : "it has only the index finger pointing upwards and all the other fingers tucked down. The palm is facing the camera.",
        "2" : "it resembles the V sign for victory or for peace. The index and middle finger are extended while the three other fingers are down. The palm is facing the camera.",           
        "3" : "it has the index finger, the middle finger and the ring finger extended while the thumb and the pinky are tucked down. The palm is facing the camera.",
        "4" : "four fingers besides the thumb are extended. The thumb is tucked down into the middle of the palm and the palm is facing the camera.",
        "5" : "all five fingers are extended and separated from each other. The palm is facing the camera."
    }
    gestures = ["-1","ok","1","2","3","4", "5"]
    classifier = Classifier(gestures, descriptions, "gemma3:12b")
