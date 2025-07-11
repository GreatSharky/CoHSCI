from messageq import MessageQueue
import time

ACTION_MAP = {
    # hand
    "left" : "Class 3",
    "right" : "Class 1",
    # action
    "gripper" : "Class 3",
    "move" : "Class 1",
    # gripper
    "open" : "Class 3",
    "closed" : "Class 2",
    # direction
    "forward" : "Class 2",
    "backward" : "Class 3",
}

def test_robot(actions):
    rq = MessageQueue("control-robot")
    sq = MessageQueue("robot-control")
    for action in actions:
        data = {"msg" : ACTION_MAP[action]}
        rq.add_msg(data)


test_robot(["left", "open"])