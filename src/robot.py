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
        except socket.error as e:
            print(f"Error initializing socket: {e}")
        self.control_reciever.get_blocking_msg(callback=self.message_robot)

    def talker(self, inMsg):
        print(inMsg)
        self.socket.sendall(inMsg.encode())
        data = self.socket.recv(1024)
        time.sleep(1)
        print(data.decode('utf-8'))
        outMsg = data.decode('utf-8')
        return outMsg

    def message_robot(self, ch , method, properties, body):
        print("Sending robot message")
        data = MessageQueue.body_parse_util(body)
        msg = {"status" : "moving"}
        self.control_sender.add_msg(msg)
        if "msg" in data:
            if data["msg"] == "Class 3":
                response = self.talker("18020000000000000")
            elif data["msg"] == "Class 2":
                response = self.talker("18021000000000000")
            else:
                response = "Not specced"
        print(response)
        data = {
            "status" : "moved",
            "response" : response
            }
        self.control_sender.add_msg(data)

if __name__ == "__main__":
    HOST = "192.168.125.1"
    PORT = 5000
    robot = Robot(HOST, PORT)