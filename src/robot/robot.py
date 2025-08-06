import socket
import time
import os
import tomllib
from messageq import MessageQueue
import logging

os.makedirs("/app/log", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(filename)s - %(message)s",
    handlers= [
        logging.FileHandler("/app/log/robot.log"),
        logging.StreamHandler()
        ]
)
logger = logging.getLogger(__name__)

class Robot():
    def __init__(self, config):
        # Configurable
        self.host = config["robot"]["ip"]
        self.port = config["robot"]["port"]
        self.gesture_map = config["robot"]["gesture_map"]
        broker = config["robot"]["broker"]

        # System variables
        logging.info(f"Start message queues: {broker}")
        self.control_reciever = MessageQueue(broker, "control-robot")
        self.control_sender = MessageQueue(broker, "robot-control")
        try:            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            print('TCP client initialized!')
            self.talker_active = True
        except socket.error as e:
            print(f"Error initializing socket: {e}")
            self.talker_active = False

        self.init_robot()        
        self.control_reciever.get_blocking_msg(callback=self.message_robot)

    def talker(self, inMsg):
        logging.info("Sending socket msg")
        self.socket.sendall(inMsg.encode())
        data = self.socket.recv(1024)
        time.sleep(1)
        outMsg = data.decode('utf-8')
        logging.info(f"Response {outMsg}")
        return outMsg
    
    def init_robot(self):
        self.robot = {
            "hand" : None,
            "action" : None,
        }
        return

    def message_robot(self, ch , method, properties, body):
        logging.info("Sending robot message")
        body = MessageQueue.body_parse_util(body)
        msg = self.update_robot_state(body["msg"])
        logging.info(msg)
        status = ""
        response = ""
        if len(msg) == 17:
            if self.talker_active:
                response = self.talker(msg)
                print(response)
            status = "moved"
            # self.init_robot()
            self.robot["action"] = None
        else:
            response = msg
            status = "updated"
        data = {
            "status" : status,
            "response" : response
            }
        logging.info(f"Data: {data}")
        logging.info(f"Robot: {self.robot}")
        self.control_sender.add_msg(data)

    def update_robot_state(self, data):
        msg = ""
        try:
            if self.gesture_map[data] in ["left_hand","right_hand"]:
                self.robot["hand"] = self.gesture_map[data]
                self.robot["action"] = None
                msg = f"Robot hand set to {self.robot["hand"]}"
                msg = msg.ljust(20)
            elif self.gesture_map[data] != "kill" and self.robot["hand"] != None:
                self.robot["action"] = self.gesture_map[data]
                msg = f"Robot action set to {self.robot["action"]}"
                msg = msg.ljust(20)
            elif self.gesture_map[data] == "kill":
                self.init_robot()
                msg = f"State reset"
                msg = msg.ljust(20)
            else:
                msg = "Nothing done"
                msg = msg.ljust(20)
        except KeyError:
            msg = f"Nothing done"
            msg = msg.ljust(20)
        if None not in self.robot.values():
            logging.info(self.robot)
            if self.robot["hand"] == "right_hand":
                msg = "1"
            elif self.robot["hand"] == "left_hand":
                msg = "0"
            msg += "80"

            if self.robot["action"] == "open":
                msg += "20"
            elif self.robot["action"] == "close":
                msg += "21"
            if self.robot["action"] == "forward":
                msg += "100100"
            elif self.robot["action"] == "backward":
                msg += "101100"
            elif self.robot["action"] == "left":
                msg += "1112340100"
            elif self.robot["action"] == "right":
                msg += "1112341100"
            elif self.robot["action"] == "up":
                msg += "12123412340100"
            elif self.robot["action"] == "down":
                msg += "12123412341100"

            msg = msg.ljust(17,"0")
        logging.info(msg)
        return msg

if __name__ == "__main__":
    logging.info("---------------\n---------------\n---------------\n")
    time.sleep(5)
    with open("config.toml", "rb") as file:
        config = tomllib.load(file)
    broker = os.getenv("rabbitMQ", "localhost")
    config["robot"]["broker"] = "rabbitmq"
    logging.info(f"Starting robot config: {config}")
    robot = Robot(config)
