import json
import socket
import time

ip = "192.168.125.1"
port = 5000

robot_commands = [
    "18069000100000000",
    "08069000200000000",
    "08069000300000000",
    "18069000400000000",
    "08069000500000000",
    "18069000600000000",
    "08069000700000000",
    "18069000800000000",
    "08069000900000000",
    "18069001000000000",
    "08069001100000000",
    "18069001200000000",
    "18069001300000000",
    "08069001400000000"
    ]

try:
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.settimeout(20)
    socket.connect((ip, port))
    print("Connected")
    talker_active = True
except socket.error as e:
    print("Not connected")
    talker_active = False

for command in robot_commands:
    s = input()
    socket.sendall(command.encode())
    data = socket.recv(1024)
    time.sleep(1)
    outMsg = data.decode('utf-8')
    print(outMsg)
