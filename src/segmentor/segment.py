"""This is the segmentation"""
import os
import tomllib
from ultralytics import SAM
from messageq import MessageQueue

class Segmentor():
    def __init__(self, config):
        # Configurable
        self.model = config["segmentor"]["model"]
        self.segment_points = config["segmentor"]["segment_points"]
        self.point_labels = config["segmentor"]["point_labels"]
        broker = config["segmentor"]["broker"]

        # System variables
        self.sam = SAM(self.model)
        def callback(ch, method, properties, body):
            self.segment(ch, method, properties, body)
        self.webcam_reciever = MessageQueue(broker, "webcam-segmentor")
        self.classifier_sender = MessageQueue(broker, "segmentor-classifier")
        self.webcam_sender = MessageQueue(broker, "segmentor-webcam")
        self.control = MessageQueue(broker, "control-segmentor")

        self.webcam_reciever.get_blocking_msg(callback)

    def segment(self, ch, method, properties, body):
        data = {"status" : "Segment_started"}
        self.control.add_msg(data)
        data = MessageQueue.body_parse_util(body)
        image = data["img"]
        masks = self.sam(image, points=self.segment_points, labels=self.point_labels)
        mask = masks[0].masks.cpu().data
        print(masks)
        h,w = mask.shape[-2:]
        mask = mask.reshape(h,w,1).numpy()
        masked_image = image*mask
        data = {"img": masked_image}
        self.webcam_sender.add_msg(data.copy())
        self.classifier_sender.add_msg(data.copy())
        data = {"status" : "Segment_done"}
        self.control.add_msg(data)
        print("masked_image sent")
        return masked_image
    
    
if __name__ == "__main__":
    with open("config.toml", "rb") as file:
        config = tomllib.load(file)
    broker = os.getenv("rabbitMQ", "localhost")
    config["segementor"]["broker"] = broker
    sam = Segmentor(config)
