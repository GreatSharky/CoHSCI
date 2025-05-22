"""This is the segmentation"""
from ultralytics import SAM
import cv2
import numpy as np

from messageq import MessageQueue

def file_index(x):
    x_index = int(x[:x.find("_")])
    return x_index 

class Segmentor():
    def __init__(self, model="sam2.1_b.pt"):
        self.sam = SAM(model)
        def callback(ch, method, properties, body):
            self.segment(ch, method, properties, body)
        self.webcam_reciever = MessageQueue("webcam-segmentor")
        self.classifier_sender = MessageQueue("segmentor-classifier")
        self.webcam_sender = MessageQueue("segmentor-webcam")
        self.webcam_reciever.get_blocking_msg(callback)

    def segment(self, ch, method, properties, body):
        buffer = np.frombuffer(body, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        masks = self.sam(image, points=[[64,80]], labels=[1])
        mask = masks[0].masks.cpu().data
        print(mask)
        h,w = mask.shape[-2:]
        mask = mask.reshape(h,w,1).numpy()
        masked_image = image*mask
        self.webcam_sender.add_msg(masked_image)
        self.classifier_sender.add_msg(masked_image)
        print("masked_image sent")
        return masked_image
    
    
if __name__ == "__main__":
    sam = Segmentor()
    while True:
        sam.segment()
