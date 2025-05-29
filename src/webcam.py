"""This is the webcam part"""
import cv2
import os
import numpy as np
from messageq import MessageQueue

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
        self.control_queue = MessageQueue("control-webcam")

    def start(self):
        text = ""
        for i in range(20000):
            ret, self.frame = self.__cap.read()
            # Do capture, add box, add latest mask
            if self.cap_time and 99 == i %200:
                capture = self.capture()
                self.webcam_sender.add_msg(capture)
                self.control_queue.add_msg("Capture made")
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
                

            self.frame = self.__add_red_rectangle()
            self.frame = cv2.flip(self.frame, 1) # Flip for more inuitivness
            # Add text
            method, header, body = self.classifier_reciever.get_msg()
            if method:
                print("classificaion done")
                self.cap_time = True
                self.control_queue.add_msg("Ready for capture")
                classification = body.decode("utf-8")
                text = f"Classified as {classification}"

            self.frame = self.__add_text(self.frame, text)
            cv2.imshow("win", self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def __add_image(self, x, y, img):
        self.frame[y:y+img.shape[1], x:x+img.shape[0],:] = img

    def capture(self):
        box = self.__bb
        return self.frame[box[1]:box[1]+box[2], box[0]:box[0]+box[3],:]
    
    def __add_red_rectangle(self, l=1):
        x = self.__bb[0]
        y = self.__bb[1]
        w = self.__bb[2]
        h = self.__bb[3]
        self.frame[y:y+h, x:x+l, :] = [0,0,255]
        self.frame[y:y+l, x:x+w, :] = [0,0,255]
        self.frame[y:y+h+l, x+w:x+w+l, :] = [0,0,255]
        self.frame[y+h:y+h+l, x:x+w+l, :] = [0,0,255]
        return self.frame
    
    def __add_text(self, frame, text, corner=(300,250)):
        font                   = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = corner
        fontScale              = 1
        fontColor              = (0,0,0)
        thickness              = 2
        lineType               = 1
        cv2.putText(frame, text, 
            bottomLeftCornerOfText, 
            font, 
            fontScale,
            fontColor,
            thickness,
            lineType)
        return frame


if __name__ == "__main__":
    cam_ip = os.getenv("CAM_IP")
    cam = Webcam(cam_ip)
    cam.start()
