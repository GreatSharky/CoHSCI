import ollama
import base64
import cv2
import numpy as np
import time
from vlm_agent import VLM
import os

class VLM_gemma(VLM):
    def __init__(self, model: str, descriptions: list):
        super().__init__(model)
        self.descriptions = descriptions
        self.system_msgs = self.__system_prompt()
    
    def create_user_msg(self,img_file):
        img = self.get_image(img_file)
        msg = {
            "role" : "user",
            "content" : "What is in this image?",
            "images" : [img]
        }
        self.user_msgs = [msg]

    def __create_system_msg(self, index, description):
        msg = {
            "role" : "system",
            "content" : f"This image belongs to class {index}. Its' charasteristics: {description}"
        }
        return msg
    
    def __system_prompt(self):
        start = {
            "role" : "system",
            "content" : "You are an state of the art hand gesture classifier. You are given images of different hand gestures wtih a short description of their characteristics for training and then you need to respond to the user requests with only what class the user image belongs to"
        }
        msgs = [start]
        for index, desc in enumerate(self.descriptions):
            msg = self.__create_system_msg(index, desc)
            msgs.append(msg)
        return msgs
