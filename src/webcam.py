"""This is the webcam part"""
import cv2
import os
import numpy as np
from dataclasses import dataclass
from messageq import MessageQueue
from settings import config

@dataclass
class TextOptions():
    font: int = 3
    textSize: float = .8
    textThickness: int = 2
    lineType: int = 1
    textColor: tuple = (0,0,0)
    textLocation: tuple = (10,40)

class Webcam():
    def __init__(self, cam_ip=""):
        # Config
        if cam_ip:
            self.cam_ip = cam_ip
        else:
            self.cam_ip = config["webcam"]["camera_output"]
        self.__bb = config["webcam"]["bounding_box"]
        self.barrier = config["webcam"]["barrier"]
        self.init_size = config["webcam"]["init_size"]
        self.show_preview = config["webcam"]["preview"]
        self.time_to_cap = config["webcam"]["time_to_cap"]
        self.text_color = config["webcam"]["text_color"]

        # Program variables
        self.__cap = cv2.VideoCapture(self.cam_ip)
        self.take_cap = True
        self.show_mask = False
        self.show_class = False
        self.initialized = False
        self.webcam_sender = MessageQueue("webcam-segmentor")
        self.segment_reciever = MessageQueue("segmentor-webcam")
        self.classifier_reciever = MessageQueue("classifier-webcam")
        self.control_sender = MessageQueue("webcam-control")
        self.control_reciever = MessageQueue("control-webcam")
        self.index_storage = []


    def start(self):
        text = {}
        img = None
        baseline = []
        init_size = self.init_size
        self.baseline = 0
        self.color = [0,0,255]
        for i in range(200000):
            ret, self.frame = self.__cap.read()
            if not ret:
                print("no image")
            if i == init_size:
                baseline = np.array(baseline)
                cap = np.mean(baseline, axis=0)
                cap = cap.astype(np.uint8)
                print(cap)
                hasher = cv2.img_hash.AverageHash_create()
                self.baseline = hasher.compute(cap)
                self.take_cap = True
                msg = {"status" : "Webcam initialized"}
                self.control_sender.add_msg(msg)
            elif i > init_size/2 and i < init_size:
                cap = self.bb_capture()
                baseline.append(cap)
            elif self.take_cap and i > init_size:
                self.capture(i)

            method, header, body = self.segment_reciever.get_msg()
            if method and self.show_preview:
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
        caphash = cv2.img_hash.averageHash(capture)
        diff = np.abs(caphash-self.baseline)
        diff = np.average(diff)

        if diff > self.barrier:
            if len(self.index_storage) == self.time_to_cap:
                data = {"img" : capture}
                self.webcam_sender.add_msg(data)
                print("Capture made")
                data = {"status" : "Capture_made"}
                self.control_sender.add_msg(data)
                self.take_cap = False
                self.index_storage = []
                self.color = [0,0,255]
            elif self.index_storage and self.index_storage[-1] == index-1:
                self.index_storage.append(index)
                self.color = [0,255,int(251-len(self.index_storage)*250/self.time_to_cap)]
            elif not self.index_storage:
                self.index_storage.append(index)
        else:

            self.index_storage = []
            self.color = [0,255,255]

    def bb_capture(self):
        box = self.__bb
        cap = self.frame[box[1]:box[1]+box[2], box[0]:box[0]+box[3],:]
        return cap.copy()

    def set_frame(self, text, mask):
        if text and text["command"] == "Capture":
            self.take_cap = True
        self.__add_rectangle(1)
        self.__add_image(100, 320,mask)
        self.__flip()
        self.__add_text(text)
        return
    
    def __flip(self):
        self.frame = cv2.flip(self.frame, 1)
        return

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
                textoptions.textColor = self.text_color
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
    cam = Webcam(cam_ip)
    cam.start()
