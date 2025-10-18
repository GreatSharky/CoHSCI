"""This is the segmentation"""
from ultralytics import SAM
from pathlib import Path
import logging
import cv2
from messageq import MessageQueue
from settings import config

log_path = Path(__file__).parent.parent / "log"
log_path.mkdir(exist_ok=True)
log_file = log_path / (Path(__file__).stem + ".log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(filename)s - %(message)s",
    handlers= [
        logging.FileHandler(log_file),
        logging.StreamHandler()
        ]
)
logger = logging.getLogger(__name__)

class Segmentor():
    def __init__(self):
        # Configurable
        logging.info("----\n----\n----\nStart segmentor")
        logging.info(f"Segmentor config: {config["segmentor"]}")
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
        logging.info("Msg recieved")
        self.control_sender.add_msg(data)
        data = MessageQueue.body_parse_util(body)
        logging.info(body)
        image = data["img"]
        results = self.sam(image, points=self.segment_points, labels=self.point_labels)
        logging.info("Results ready")
        for mask_object in results[0].masks:
            # mask = masks[0].masks.cpu().data
            mask = mask_object.cpu().data
            logging.debug(mask)
            h,w = mask.shape[-2:]
            mask = mask.reshape(h,w,1).numpy()
            maksed_img = image*mask
            image = image - maksed_img
        logging.info("Mask ready")
        data = {
            "status" : "Segment_done",
            "img": image
            }
        self.control_sender.add_msg(data.copy())
        logging.info(f"Masked_image sent: {data}")
        return image
    
    
if __name__ == "__main__":
    sam = Segmentor()
