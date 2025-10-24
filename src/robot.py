import socket
import time
from pathlib import Path
import logging
import json
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
        self.gestures_map = config["commands"]["prompts"]
        self.gestures = list(self.gestures_map.keys())
        logging.debug(self.gestures)
        self.lengths = [3] #config["robot"]["step_size"]

        # System variables
        self.control_reciever = MessageQueue("control-robot")
        self.control_sender = MessageQueue("robot-control")
        self.assembly_mode = True
        self.prev_control_msg = None
        self.step = self.lengths[0]
        self.command_index = 0
        with open("robot_msgs.json", "r") as file:
            robot_commands = json.loads(file.read())
            self.robot_commands = robot_commands["commands"]
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(20)
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
        body = MessageQueue.body_parse_util(body)
        logging.info(f"msg recieved {body}")
        msg, action = self.update_robot_state(int(body["msg"]))
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
        key = "next step" if self.assembly_mode else "previous_action"
        data = {
            "status" : status,
            "mode" : "Assembly" if self.assembly_mode else "Jog",
            key : action
            }
        logging.info(data)
        logging.debug(self.robot)
        self.control_sender.add_msg(data)

    def consume_control_message(self, data):
        msg = ""
        action = ""
        logging.debug(data)
        try:
            if self.gestures[data] in ["left_hand","right_hand"]:
                if self.prev_control_msg == self.gestures[data]:
                    # Switch mode
                    self.assembly_mode = not self.assembly_mode
                    self.robot["action"] = None
                    logging.info(f"Mode switched. Assembly mode {self.assembly_mode}")
                    action = f"Mode switched"
                    msg = action.ljust(20)
                else:
                    self.robot["hand"] = self.gestures[data]
                    self.robot["action"] = None
                    action = f"Robot hand set to {self.robot["hand"]}"
                    msg = action.ljust(20)
            elif self.gestures[data] != "nothing" and self.robot["hand"] != None:
                self.robot["action"] = self.gestures[data]
                action = self.gestures[data]
                msg = action.ljust(20)
            elif self.gestures[data] == "kill":
                self.init_robot()
                msg = f"State reset"
                msg = msg.ljust(20)
            else:
                action = "Nothing done"
                msg = action.ljust(20)
            self.prev_control_msg = self.gestures[data]
        except KeyError:
            msg = f"KeyError, propably error in key"
            msg = msg.ljust(20)
        return msg, action

    def update_robot_state(self, data):
        msg, action= self.consume_control_message(data)

        if None not in self.robot.values() and not self.assembly_mode:
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
        elif None not in self.robot.values() and self.assembly_mode:
            logging.info("Assembly mode")
            logging.debug(self.robot)
            if self.robot["hand"] == "right_hand":
                msg = "1"
            elif self.robot["hand"] == "left_hand":
                msg = "0"
            msg += "80"
            if self.gestures_map["next_step"] in self.gestures_map.keys():
                next_command = self.gestures_map["next_step"]
            else:
                next_command = "next_step"
            logging.debug(next_command)
            if self.robot["action"] == next_command:
                if self.command_index < len(self.robot_commands):
                    msg = self.robot_commands[self.command_index][0]
                    action = self.robot_commands[self.command_index][1]
                    self.command_index += 1
                else:
                    action = "assembly complete"
        return msg, action
    
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
