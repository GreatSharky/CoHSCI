"""This is the segmentation"""
import os
import tomllib
from ultralytics import SAM
from messageq import MessageQueue
import logging
import time

os.makedirs("/app/log", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(filename)s - %(message)s",
    handlers= [
        logging.FileHandler("/app/log/segment.log"),
        logging.StreamHandler()
        ]
)
logger = logging.getLogger(__name__)


class Segmentor():
    def __init__(self, config):
        # Configurable
        logging.debug("Setting config variables")
        self.model = config["segmentor"]["model"]
        self.segment_points = config["segmentor"]["segment_points"]
        self.point_labels = config["segmentor"]["point_labels"]
        broker = config["segmentor"]["broker"]

        # System variables
        logging.debug("Starting SAM")
        self.sam = SAM(self.model)
        def callback(ch, method, properties, body):
            self.segment(ch, method, properties, body)
        logging.debug(f"Starting message queues broker: {broker}")
        self.webcam_reciever = MessageQueue(broker, "webcam-segmentor")
        self.classifier_sender = MessageQueue(broker, "segmentor-classifier")
        self.webcam_sender = MessageQueue(broker, "segmentor-webcam")
        self.control = MessageQueue(broker, "control-segmentor")

        logging.info("Wait for message")
        self.webcam_reciever.get_blocking_msg(callback)

    def segment(self, ch, method, properties, body):
        logging.debug("Message recieved")
        logging.info(body)
        data = {"status" : "Segment_started"}
        self.control.add_msg(data)
        data = MessageQueue.body_parse_util(body)
        image = data["img"]
        masks = self.sam(image, points=self.segment_points, labels=self.point_labels)
        mask = masks[0].masks.cpu().data
        logging.info(mask)
        h,w = mask.shape[-2:]
        mask = mask.reshape(h,w,1).numpy()
        masked_image = image*mask
        data = {"img": masked_image}
        self.webcam_sender.add_msg(data.copy())
        self.classifier_sender.add_msg(data.copy())
        data = {"status" : "Segment_done"}
        self.control.add_msg(data)
        logging.info("Masked image sent")
        logging.info(masked_image)
        return masked_image
    
    
if __name__ == "__main__":
    logging.info("---------------\n---------------\n---------------\n")
    time.sleep(5)
    logging.debug("Started")
    with open("config.toml", "rb") as file:
        config = tomllib.load(file)
    broker = os.getenv("rabbitMQ", "localhost")
    config["segmentor"]["broker"] = "rabbitmq"
    logging.info(f"Starting SAM \n{config}")
    sam = Segmentor(config)
