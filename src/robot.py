import socket
import time
from pathlib import Path
import logging
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

class Robot():
    def __init__(self):
        # Configurable
        logging.info("----\n----\n----\nStart robot")
        logging.info(f"Robot config: {config["robot"]}")
        self.host = config["robot"]["ip"]
        self.port = config["robot"]["port"]
        self.gesture_map = config["robot"]["gesture_map"]
        self.lengths = [100,40,5,1] #config["robot"]["step_size"]

        # System variables
        self.control_reciever = MessageQueue("control-robot")
        self.control_sender = MessageQueue("robot-control")
        self.control_mode = False
        self.prev_control_msg = None
        self.step = self.lengths[0]
        self.rotations = [3, 3, 3]
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            logging.info('TCP client initialized!')
            self.talker_active = True
        except socket.error as e:
            logging.error(f"Error initializing socket: {e}")
            self.talker_active = False

        self.init_robot()        
        self.control_reciever.get_blocking_msg(callback=self.message_robot)

    def talker(self, inMsg):
        self.socket.sendall(inMsg.encode())
        data = self.socket.recv(1024)
        time.sleep(1)
        outMsg = data.decode('utf-8')
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
                logging.info(response)
            status = "moved"
            # self.init_robot()
            self.robot["action"] = None
        else:
            response = msg
            status = "updated"
        data = {
            "response" : status,
            "status" : response
            }
        logging.info(data)
        logging.debug(self.robot)
        self.control_sender.add_msg(data)

    def consume_control_message(self, data):
        msg = ""
        try:
            if self.gesture_map[data] in ["left_hand","right_hand"]:
                if self.prev_control_msg == self.gesture_map[data]:
                    # Switch mode
                    self.control_mode = not self.control_mode
                    self.robot["action"] = None
                    logging.info(f"Mode switched. Control mode {self.control_mode}")
                    msg = f"Mode switched"
                    msg = msg.ljust(20)
                else:
                    self.robot["hand"] = self.gesture_map[data]
                    self.robot["action"] = None
                    msg = f"Robot hand set to {self.robot["hand"]}"
                    msg = msg.ljust(20)
            elif self.gesture_map[data] != "kill" and self.robot["hand"] != None:
                self.robot["action"] = self.gesture_map[data]
                msg = msg.ljust(20)
            elif self.gesture_map[data] == "kill":
                self.init_robot()
                msg = f"State reset"
                msg = msg.ljust(20)
            else:
                msg = "Nothing done"
                msg = msg.ljust(20)
            self.prev_control_msg = self.gesture_map[data]
        except KeyError:
            msg = f"Nothing done"
            msg = msg.ljust(20)
        return msg

    def update_robot_state(self, data):
        msg = self.consume_control_message(data)

        if None not in self.robot.values() and not self.control_mode:
            logging.info("Jog mode")
            logging.debug(self.robot)
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
                msg += "100" + str(self.step).rjust(3,"0")
            elif self.robot["action"] == "backward":
                msg += "101" + str(self.step).rjust(3,"0")
            elif self.robot["action"] == "left":
                msg += "1112340" + str(self.step).rjust(3,"0")
            elif self.robot["action"] == "right":
                msg += "1112341" + str(self.step).rjust(3,"0")
            elif self.robot["action"] == "up":
                msg += "12123412340" + str(self.step).rjust(3,"0")
            elif self.robot["action"] == "down":
                msg += "12123412341" + str(self.step).rjust(3,"0")

            msg = msg.ljust(17,"0")
        elif None not in self.robot.values() and self.control_mode:
            logging.info("Control mode")
            logging.debug(self.robot)
            if self.robot["hand"] == "right_hand":
                msg = "1"
            elif self.robot["hand"] == "left_hand":
                msg = "0"
            msg += "80"
            if self.robot["action"] == "close":
                self.step = self.change_step_size("up")
                logging.info(f"Step size {self.step}")
            elif self.robot["action"] == "open":
                self.step = self.change_step_size("down")
                logging.info(f"Step size {self.step}")
            elif self.robot["action"] == "right":
                if self.rotations[1] < 5:
                    logging.info(f"Rotate clockwise {self.rotations[1]}")
                    self.rotations[1] += 1
                    msg += "4010000001"
            elif self.robot["action"] == "left":
                if self.rotations[1] < 7:
                    logging.info(f"Rotate around -x {self.rotations[1]}")
                    self.rotations[1] += 1
                    msg += "4010001001"
            elif self.robot["action"] == "up":
                if self.rotations[0] > 0:
                    logging.info(f"Rotate counter clockwise {self.rotations[0]}")
                    self.rotations[0] -= 1
                    msg += "40100010001001"
            elif self.robot["action"] == "down":
                if self.rotations[0] < 7:
                    logging.info(f"Rotate clockwise {self.rotations[0]}")
                    self.rotations[0] += 1
                    msg += "40100010000001"
            elif self.robot["action"] == "forward":
                if self.rotations[0] < 7:
                    logging.info(f"Rotate clockwise {self.rotations[0]}")
                    self.rotations[0] += 1
                    msg += "400001"
            elif self.robot["action"] == "backward":
                if self.rotations[0] < 7:
                    logging.info(f"Rotate clockwise {self.rotations[0]}")
                    self.rotations[0] += 1
                    msg += "401001"
            msg = msg.ljust(17,"0")
        return msg
    
    def change_step_size(self, direction):
        idx = self.lengths.index(self.step)

        if direction.lower() == "up":
            if idx < len(self.lengths) - 1:
                return self.lengths[idx + 1]
            return self.step  # already at max
        elif direction.lower() == "down":
            if idx > 0:
                return self.lengths[idx - 1]
            return self.step  # already at min

if __name__ == "__main__":
    robot = Robot()
