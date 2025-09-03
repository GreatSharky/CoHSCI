import cv2
import numpy as np
import json
import logging
from pathlib import Path

from messageq import MessageQueue
from vlm_agent import VLM
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

class Validator(VLM):
    def __init__(self, config):
        # Config
        logging.info("----\n----\n----\nStart validator")
        logging.info(f"Validator config: {config}")
        super().__init__(config["model"])
        self.create_system_prompt(config["system_prompt"])

        self.control_reciever = MessageQueue("control-validator")
        self.control_sender = MessageQueue("validator-control")
        self.control_reciever.get_blocking_msg(callback=self.classifier_callback)

    def create_system_prompt(self, description):
        msg = {
            "role" : "system",
            "content" : description
        }
        self.system_msgs = [msg]

    def create_user_prompt(self, description: str, image: np.ndarray):
        img = self.get_image(image)
        msg = {
            "role" : "user",
            "content" : f"{description}",
            "images" : [img]
        }
        self.user_msgs = [msg]

    def classifier_callback(self, ch, method, properties, body):
        logging.info("Classification recieved")
        data = {"status" : "Validation_started"}
        self.control_sender.add_msg(data)
        body = MessageQueue.body_parse_util(body)
        logging.info(f"{body["msg"]}")
        description, img = self.parse_body(body)
        logging.debug("Body parsed")
        logging.debug(description)
        self.create_user_prompt(description, img)
        result = self.inference()
        logging.debug(result)
        data = {"status" : "Validated",
                "result" : result.message.content}
        logging.info(f"Validation result {data}")
        self.control_sender.add_msg(data)
        return

    def parse_body(self, body):
        img = body["img"]
        description = body["msg"]
        return description, img

if __name__ == "__main__":
    val = Validator(config["validator"])
