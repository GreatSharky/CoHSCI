import socket
import time
from messageq import MessageQueue

class Robot():
    def __init__(self, host, port):
        self.control_reciever = MessageQueue("control-robot")
        self.control_sender = MessageQueue("robot-control")
        try:            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            print('TCP client initialized!')
            self.talker_active = True
        except socket.error as e:
            print(f"Error initializing socket: {e}")
            self.talker_active = True
        self.gesture_map = {
            "hand" : {
                "Class 1" : "right",
                "Class 3" : "left"
            },
            "mode" : {
                "Class 1" : "move",
                "Class 3" : "grip"
            },
            "action" : {
                "Class 1" : "left",
                "Class 2" : "right",
                "Class 3" : "forward",
                "Class 4" : "backward",
                "Class 5" : "up",
                "Class 6" : "down",
            }
        }
        self.init_robot()
        
        self.control_reciever.get_blocking_msg(callback=self.message_robot)

    def talker(self, inMsg):
        #self.socket.sendall(inMsg.encode())
        #data = self.socket.recv(1024)
        time.sleep(1)
        #outMsg = data.decode('utf-8')
        #return outMsg
    
    def init_robot(self):
        self.robot = {
            "hand" : None,
            "mode" : None,
            "action" : None,
        }
        return

    def message_robot(self, ch , method, properties, body):
        print("Sending robot message")
        body = MessageQueue.body_parse_util(body)
        msg = self.robot_message(body["msg"])
        print(msg)
        status = ""
        response = ""
        if len(msg) == 17:
            if self.talker_active:
                response = self.talker(msg)
                print(response)
            status = "moved"
            self.init_robot()

        else:
            response = msg
            status = "updated"
        data = {
            "status" : status,
            "response" : response
            }
        print(data)
        print(self.robot)
        self.control_sender.add_msg(data)

    def robot_message(self, request_data):
        msg = ""
        try:
            for key in self.robot:
                if self.robot[key] == None:
                    self.robot[key] = self.gesture_map[key][request_data]
                    msg = f"{key} set to {self.robot[key]}"
                    msg = msg.ljust(20)
                    break
        except KeyError:
            msg = f"{key} not set"
            msg = msg.ljust(20)
        if None not in self.robot.values():
            print(self.robot)
            if self.robot["hand"] == "right":
                msg = "1"
            elif self.robot["hand"] == "left":
                msg = "0"
            msg += "80"
            if self.robot["mode"] == "grip":
                if self.robot["action"] == "right":
                    msg += "20"
                elif self.robot["action"] == "forward":
                    msg += "21"
            elif self.robot["mode"] == "move":
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
        return msg

if __name__ == "__main__":
    HOST = "192.168.125.1"
    PORT = 5000
    robot = Robot(HOST, PORT)