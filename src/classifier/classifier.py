"""This one will classify the segmented image"""
import os
import tomllib
import time
import logging

from gemma3_agent import VLM_gemma
from messageq import MessageQueue

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

class Classifier():
    def __init__(self, config):
        self.descriptions = config["classifier"]["emoji_prompts"]
        model = config["classifier"]["model"]
        self.vlm1 = VLM_gemma(model, self.descriptions)
        broker = config["classifier"]["broker"]

        self.segmentor_reciever = MessageQueue(broker, "segmentor-classifier")
        self.webcam_sender = MessageQueue(broker, "classifier-webcam")
        self.control = MessageQueue(broker, "control-classifier")
        self.validator_sender = MessageQueue(broker, "classifier-validator")

        self.segmentor_reciever.get_blocking_msg(self.classify)

    def classify(self, ch, method, properties, body):
        logging.info("Message recieved")
        logging.info("Classifying...")
        data = {"status" : "Image_recieved"}
        self.control.add_msg(data)
        data = MessageQueue.body_parse_util(body)
        image = data["img"]
        self.vlm1.create_user_msg(image)
        result1 = self.vlm1.inference()
        classification = result1.message.content
        if "lass" in classification:
            classification = classification[len("Class "):]
        data = {
            "status" : "Classified",
            "result" : f"{classification}",
            "msg" : self.descriptions[int(classification)],
            "img" : data["img"]
        }
        logging.info(f"Classification: {classification}")
        logging.info(data)
        self.control.add_msg(data)
        return

if __name__ == "__main__":
    time.sleep(5)
    with open("config.toml", "rb") as file:
        config = tomllib.load(file)
    broker = os.getenv("rabbitMQ", "localhost")
    config["classifier"]["broker"] = "rabbitmq"
    logging.info(f"Starting config: {config}")
    classifier = Classifier(config)
