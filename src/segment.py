"""This is the segmentation"""
from ultralytics import SAM
from messageq import MessageQueue
from settings import config
import cv2

class Segmentor():
    def __init__(self):
        # Configurable
        self.model = config["segmentor"]["model"]
        self.segment_points = config["segmentor"]["segment_points"]
        self.point_labels = config["segmentor"]["point_labels"]

        # System variables
        self.sam = SAM(self.model)
        def callback(ch, method, properties, body):
            self.segment(ch, method, properties, body)
        self.control_reciever = MessageQueue("control-segmentor")
        self.control_sender = MessageQueue("segmentor-control")

        self.control_reciever.get_blocking_msg(callback)

    def segment(self, ch, method, properties, body):
        data = {"status" : "Segment_started"}
        self.control_sender.add_msg(data)
        data = MessageQueue.body_parse_util(body)
        image = data["img"]
        masks = self.sam(image, points=self.segment_points, labels=self.point_labels)
        mask = masks[0].masks.cpu().data
        print(masks)
        h,w = mask.shape[-2:]
        mask = mask.reshape(h,w,1).numpy()
        masked_image = image*mask
        data = {
            "status" : "Segment_done",
            "img": masked_image
            }
        self.control_sender.add_msg(data.copy())
        print("masked_image sent")
        return masked_image
    
    
if __name__ == "__main__":
    sam = Segmentor()
