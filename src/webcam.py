"""This is the webcam part"""
import cv2
import os
import numpy as np
from dataclasses import dataclass

from messageq import MessageQueue

@dataclass
class TextOptions():
    font: int = 1
    textSize: float = 1.0
    textThickness: int = 2
    lineType: int = 1
    textColor: tuple = (0,0,0)
    textLocation: tuple = (300, 250)

class Webcam():
    def __init__(self, cam: str):
        self.__cap = cv2.VideoCapture(cam)
        self.__bb = [90,200,128,128]
        self.cap_time = True
        self.show_mask = False
        self.show_class = False
        self.webcam_sender = MessageQueue("webcam-segmentor")
        self.segment_reciever = MessageQueue("segmentor-webcam")
        self.classifier_reciever = MessageQueue("classifier-webcam")

    def start(self):
        text = ""
        for i in range(20000):
            ret, self.frame = self.__cap.read()
            # Do capture, add box, add latest mask
            if self.cap_time and 99 == i %100:
                capture = self.capture()
                self.webcam_sender.add_msg(capture)
                self.cap_time = False
                print("Capture made")
            method, header, body = self.segment_reciever.get_msg()
            if method:
                print("segmentation done")
                img = cv2.imdecode(np.frombuffer(body, dtype=np.uint8), cv2.IMREAD_ANYCOLOR)
                self.__add_image(1,1,img)
                self.show_mask = True
            elif self.show_mask:
                self.__add_image(1,1,img)
                

            self.frame = self.__add_rectangle()
            self.frame = cv2.flip(self.frame, 1) # Flip for more inuitivness
            # Add text
            method, header, body = self.classifier_reciever.get_msg()
            if method:
                print("classificaion done")
                self.cap_time = True
                classification = body.decode("utf-8")
                text = f"Classified as {classification}"

            self.frame = self.__add_text(self.frame, text)
            cv2.imshow("win", self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def set_frame(self, text, text_options, box_color, mask):
        if self.show_mask:
            self.__add_image(mask)
        self.__add_rectangle(1,box_color)
        self.__flip()
        self.__add_text(text, text_options)
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
    
    def __add_text(self, text: str, textoptions: TextOptions):
        font                   = textoptions.font
        bottomLeftCornerOfText = textoptions.textLocation
        fontScale              = textoptions.textSize
        fontColor              = textoptions.textColor
        thickness              = textoptions.textThickness
        lineType               = textoptions.lineType
        cv2.putText(self.frame, text, 
            bottomLeftCornerOfText, 
            font, 
            fontScale,
            fontColor,
            thickness,
            lineType)


if __name__ == "__main__":
    cam_ip = os.getenv("CAM_IP")
    cam = Webcam(cam_ip)
    cam.start()
