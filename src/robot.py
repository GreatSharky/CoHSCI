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
        self.gesture_map = {
            "hand" : {
                "Class 1" : "right",
                "Class 3" : "left"
            },
            "gripper" : {
                "Class 2" : "closed",
                "Class 3" : "open"
            }
        }
        
        self.control_reciever.get_blocking_msg(callback=self.message_robot)

    def talker(self, inMsg):
        print(inMsg)
        self.socket.sendall(inMsg.encode())
        data = self.socket.recv(1024)
        time.sleep(1)
        print(data.decode('utf-8'))
        outMsg = data.decode('utf-8')
        return outMsg
    
    def init_robot(self):
        self.robot = {
            "hand" : None,
            # "direction" : None,
            # "amount" : None,
            "gripper" : None,
        }
        return

    def message_robot(self, ch , method, properties, body):
        print("Sending robot message")
        data = MessageQueue.body_parse_util(body)
        msg = self.robot_message()
        status = ""
        response = ""
        if len(msg) == 17:
            print(msg)
            if self.talker_active:
                response = self.talker(msg)
                print(response)
                status = "moved"

        else:
            self.robot[msg] = self.gesture_map[msg][body["msg"]]
            status = "updated"
        data = {
            "status" : status,
            "response" : response
            }
        self.control_sender.add_msg(data)

    def robot_message(self):
        if self.robot["hand"] == None:
            return "hand"
        # elif self.robot["direction"]  == None:
        #     return "direction"
        # elif self.robot["amount"] == None:
        #     return "amount"
        elif self.robot["gripper"] == None:
            return "gripper"
        else:
            # Message build
            msg = "0"*17
            if self.robot["hand"] == "right":
                msg[0] = "1"
            elif self.robot["hand"] == "left":
                msg[0] = "0"
            
            if self.robot["gripper"] == "open":
                msg[3:5] = "20"
            elif self.robot["gripper"] == "closed":
                msg[3:5] = "21"

            msg[1:3] = "80"
            return msg

if __name__ == "__main__":
    HOST = "192.168.125.1"
    PORT = 5000
    robot = Robot(HOST, PORT)