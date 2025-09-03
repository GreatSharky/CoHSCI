from messageq import MessageQueue
import time

ACTION_MAP = {
    # hand
    "hleft" : "Class 2",
    "hright" : "Class 1",
    # direction
    "forward" : "Class 5",
    "backward" : "Class 6",
    "left" : "Class 3",
    "right" : "Class 4",
    "up" : "Class 7",
    "down" : "Class 8",
    "open" : "Class 10",
    "close" : "Class 9"
}

def test_robot(actions):
    rq = MessageQueue("control-robot")
    sq = MessageQueue("robot-control")
    for action in actions:
        data = {"msg" : ACTION_MAP[action]}
        rq.add_msg(data)


test_robot(["hleft", "up"])