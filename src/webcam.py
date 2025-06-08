"""This is the webcam part"""
import cv2
import os
import numpy as np
import json
from messageq import MessageQueue
from dataclasses import dataclass

@dataclass
class TextOptions():
    font: int = 3
    textSize: float = .8
    textThickness: int = 2
    lineType: int = 1
    textColor: tuple = (0,0,0)
    textLocation: tuple = (10,40)

class Webcam():
    def __init__(self, cam: str):
        self.__cap = cv2.VideoCapture(cam)
        self.to = TextOptions
        self.__bb = [90,200,128,128]
        self.cap_time = True
        self.show_mask = False
        self.show_class = False
        self.webcam_sender = MessageQueue("webcam-segmentor")
        self.segment_reciever = MessageQueue("segmentor-webcam")
        self.classifier_reciever = MessageQueue("classifier-webcam")
        self.control_sender = MessageQueue("webcam-control")
        self.control_reciever = MessageQueue("control-webcam")

    def start(self):
        text = ""
        img = None
        for i in range(20000):
            ret, self.frame = self.__cap.read()
            if not ret:
                print("no image")
            # Do capture, add box, add latest mask
            if self.cap_time and 99 == i %200:
                capture = self.capture()
                self.webcam_sender.add_msg(capture)
                self.control_sender.add_msg("Capture made")
                self.cap_time = False
                print("Capture made")
                data = {"img" : capture}
                self.webcam_sender.add_msg(data)
                self.control_sender.add_msg("Capture made")
                self.cap_time = False
            method, header, body = self.segment_reciever.get_msg()
            if method:
                self.show_mask = True
                img = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)

            method, header, body = self.control_reciever.get_msg()
            if method:
                text = json.loads(body)
            self.set_frame(text, [0,0,255], img)

            cv2.imshow("webcam", self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def set_frame(self, text, box_color, mask):
        if self.show_mask:
            self.__add_image(300, 400,mask)
        self.__add_rectangle(1,box_color)
        self.__flip()
        self.__add_text(text)
        return
    
    def __flip(self):
        self.frame = cv2.flip(self.frame, 1)

    def __add_image(self, x, y, img):
        self.frame[y:y+img.shape[1], x:x+img.shape[0],:] = img

    def capture(self):
        box = self.__bb
        return self.frame[box[1]:box[1]+box[2], box[0]:box[0]+box[3],:]
    
    def __add_rectangle(self, l=1, color=[0,0,255]):
        x = self.__bb[0]
        y = self.__bb[1]
        w = self.__bb[2]
        h = self.__bb[3]
        self.frame[y:y+h, x:x+l, :] = color
        self.frame[y:y+l, x:x+w, :] = color
        self.frame[y:y+h+l, x+w:x+w+l, :] = color
        self.frame[y+h:y+h+l, x:x+w+l, :] = color
        return self.frame
    
    def __add_text(self, information: dict):
        for index, title in enumerate(information):
            textoptions = TextOptions()
            textoptions.textLocation = (10, 40 + index*22)
            text = f"{title}: {information[title]}" 
            self.frame = cv2.putText(self.frame, text, 
                textoptions.textLocation, 
                textoptions.font, 
                textoptions.textSize,
                textoptions.textColor,
                textoptions.textThickness,
                textoptions.lineType)


if __name__ == "__main__" or __name__ == "__debug__":
    cam_ip = os.getenv("CAM_IP")
    if cam_ip == "" or cam_ip == None:
        cam_ip = "/dev/video0"
    print(cam_ip)
    cam = Webcam(cam_ip)

    cam.start()
