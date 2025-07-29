from messageq import MessageQueue
import time

ACTION_MAP = {
    # hand
    "hleft" : "Class 3",
    "hright" : "Class 1",
    # mode
    "move" : "Class 1",
    "grip" : "Class 3",
    # direction
    "forward" : "Class 3",
    "backward" : "Class 4",
    "left" : "Class 1",
    "right" : "Class 2",
    "up" : "Class 5",
    "down" : "Class 6",
    "open" : "Class 3",
    "close" : "Class 2"
}

def test_robot(actions):
    rq = MessageQueue("control-robot")
    sq = MessageQueue("robot-control")
    for action in actions:
        data = {"msg" : ACTION_MAP[action]}
        rq.add_msg(data)


test_robot(["hleft", "move","up"])