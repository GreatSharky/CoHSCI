from messageq import MessageQueue
import time

ACTION_MAP = {
    # hand
    "left" : "Class 3",
    "right" : "Class 1",
    # action
    "open" : "Class 3",
    "closed" : "Class 2",
    # direction
    "forward" : "Class 1",
    "backward" : "Class 4",
}

def test_robot(actions):
    rq = MessageQueue("control-robot")
    sq = MessageQueue("robot-control")
    for action in actions:
        data = {"msg" : ACTION_MAP[action]}
        rq.add_msg(data)


test_robot(["left", "open"])