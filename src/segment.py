"""This is the segmentation"""
from ultralytics import SAM
import cv2
import numpy as np

from messageq import MessageQueue, BlockingMessageQueue

def file_index(x):
    x_index = int(x[:x.find("_")])
    return x_index 

class Segmentor():
    def __init__(self, model="sam2.1_b.pt"):
        self.sam = SAM(model)
        def callback(ch, method, properties, body):
            return cv2.imdecode(np.frombuffer(body, dtype=np.uint8), cv2.IMREAD_COLOR)
        self.webcam_sender = BlockingMessageQueue("segmentor-webcam", callback=callback)
        self.classifier_sender = MessageQueue("segmentor-classifier")
        self.reciever = MessageQueue("webcam-segmentor")

    def segment(self):
        image = self.webcam_sender.get_msg()
        print(image)
        masks = self.sam(image, points=[[64,80]], labels=[1])
        mask = masks[0].masks.cpu().data
        print(mask)
        h,w = mask.shape[-2:]
        mask = mask.reshape(h,w,1).numpy()
        masked_image = image*mask
        self.webcam_sender.add_msg(masked_image)
        self.classifier_sender.add_msg(masked_image)
        return masked_image
    
    
if __name__ == "__main__":
    sam = Segmentor()
    while True:
        sam.segment()
