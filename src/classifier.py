"""This one will classify the segmented image"""
from gemma3_agent import VLM_gemma
import os
import cv2
import numpy as np
from segment import file_index
import socket

from messageq import BlockingMessageQueue


if __name__ == "__main__":
    descriptions = {
        "ok" : "it resembles the OK sign. The thumb and the index finger create an circle while the three other fingers are extended.",
        "1" : "it has only the index finger pointing upwards and all the other fingers tucked down. The palm is facing the camera.",
        "2" : "it resembles the V sign for victory or for peace. The index and middle finger are extended while the three other fingers are down. The palm is facing the camera.",           
        "3" : "it has the index finger, the middle finger and the ring finger extended while the thumb and the pinky are tucked down. The palm is facing the camera.",
        "4" : "four fingers besides the thumb are extended. The thumb is tucked down into the middle of the palm and the palm is facing the camera.",
        "5" : "all five fingers are extended and separated from each other. The palm is facing the camera."
    }
    vlm1 = VLM_gemma("gemma3:12b", ["ok","1","2","3","4", "5"], descriptions, 1)
    vlm2 = VLM_gemma("gemma3:12b", ["ok","1","2","3","4", "5"], descriptions, 1)
    def callback_1(ch, method, header, body):
        return cv2.imdecode(np.frombuffer(body, dtype=np.uint8), cv2.IMREAD_COLOR)
    reciever = BlockingMessageQueue("segmentor-classifier", callback=callback_1)
    sender = BlockingMessageQueue("classifier-webcam", callback=None)
    file = ""
    HOST="192.168.125.1"
    PORT = 5000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect((HOST,PORT))
    print("TCP client initialized")
    while True:
        segmented_image = reciever.get_msg()
        vlm1.create_user_msg(segmented_image)
        result1 = vlm1.inference()
        vlm2.create_user_msg(segmented_image)
        result2 = vlm2.inference()
        if result1.message.content == result2.message.content:
            response = f"Class {result1.message.content}"
        else:
            response = f"Unclear: res {result1.message.content} and {result2.message.content}"
        print(response)
        sender.add_msg(response)
        #s.sendall(response.encode())
