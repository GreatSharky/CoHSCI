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
        self.initialized = False
        self.webcam_sender = MessageQueue("webcam-segmentor")
        self.segment_reciever = MessageQueue("segmentor-webcam")
        self.classifier_reciever = MessageQueue("classifier-webcam")
        self.control_sender = MessageQueue("webcam-control")
        self.control_reciever = MessageQueue("control-webcam")

    def start(self):
        text = {}
        img = None
        baseline = []
        init_size = 200
        self.baseline = 0
        self.divider = 1
        self.index_storage = []
        self.color = [0,0,255]
        for i in range(20000):
            ret, self.frame = self.__cap.read()
            if not ret:
                print("no image")
            if i < init_size:
                cap = self.bb_capture()
                baseline.append(cap)
            elif i == init_size:
                self.baseline = np.mean(np.array(baseline), axis=0).astype(np.uint8)
                self.divider = np.sum((self.baseline-self.bb_capture())**2)
                cv2.imwrite("baseline.jpg", self.baseline)
                self.baseline = np.where(self.baseline == 0, 1, self.baseline)
                self.cap_time = True
            elif self.cap_time:
                self.capture(i)

            method, header, body = self.segment_reciever.get_msg()
            if method:
                self.show_mask = True
                img = body["img"]

            method, header, body = self.control_reciever.get_msg()
            if method:
                text = body
            self.set_frame(text, img)

            cv2.imshow("webcam", self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def capture(self, index):
        capture = self.bb_capture()
        diff = self.image_differnece(capture)
        print(index, diff)
        if diff > 11:
            if len(self.index_storage) == 10:
                data = {"img" : capture}
                self.webcam_sender.add_msg(data)
                print("Capture made")
                data = {"status" : "Capture_made"}
                self.control_sender.add_msg(data)
                self.cap_time = False
                self.index_storage = []
                self.color = [0,0,255]
            elif self.index_storage and self.index_storage[-1] == index-1:
                self.index_storage.append(index)
                self.color = [0,255,0]
            else:
                self.index_storage = []
                self.index_storage = [255,255,0]

    def image_differnece(self, capture):
        red_diff = np.abs(self.baseline[:,:,0] - capture[:,:,0])/self.baseline[:,:,0]
        green_diff = np.abs(self.baseline[:,:,1] - capture[:,:,1])/self.baseline[:,:,1]
        blue_diff = np.abs(self.baseline[:,:,2] - capture[:,:,2])/self.baseline[:,:,2]
        barrier = .1
        red_sum = np.sum(np.where(red_diff > barrier, 1, 0))
        green_sum = np.sum(np.where(green_diff > barrier, 1, 0))
        blue_sum = np.sum(np.where(blue_diff > barrier, 1, 0))
        return (red_sum + green_sum + blue_sum)/(capture.shape[0] * capture.shape[1] * capture.shape[2])

    def bb_capture(self):
        box = self.__bb
        cap = self.frame[box[1]:box[1]+box[2], box[0]:box[0]+box[3],:]
        return cap

    def set_frame(self, text, mask):
        if text and text["command"] == "Capture":
            self.cap_time = True
        self.__add_rectangle(1)
        self.__add_image(90, 20,mask)
        self.__flip()
        self.__add_text(text)
        return
    
    def __flip(self):
        self.frame = cv2.flip(self.frame, 1)

    def __add_image(self, x, y, img):
        if self.show_mask:
            self.frame[y:y+img.shape[1], x:x+img.shape[0],:] = img
    
    def __add_rectangle(self, l=1):
        x = self.__bb[0]
        y = self.__bb[1]
        w = self.__bb[2]
        h = self.__bb[3]
        self.frame[y:y+h, x:x+l, :] = self.color
        self.frame[y:y+l, x:x+w, :] = self.color
        self.frame[y:y+h+l, x+w:x+w+l, :] = self.color
        self.frame[y+h:y+h+l, x:x+w+l, :] = self.color
        return self.frame
    
    def __add_text(self, information: dict):
        for index, title in enumerate(information):
            if title != "command":
                textoptions = TextOptions()
                textoptions.textColor = [0,255,0]
                textoptions.textLocation = (10, 20 + index*22)
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
