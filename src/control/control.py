import time
import os
import tomllib
import logging
from messageq import MessageQueue

os.makedirs("/app/log", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(filename)s - %(message)s",
    handlers= [
        logging.FileHandler("/app/log/control.log"),
        logging.StreamHandler()
        ]
)
logger = logging.getLogger(__name__)

# Write control/state machine that tracks program state.
# Roles:
#   1. Trigger capture
#   2. Give updates to webcam
#   3. Process classifictions
#   4. Command robot
#  
# Could rewrite webcam to only do the wecam sequence inside the state machine.
# That way the control would trigger capture, change capture, mask and classification flags.
# It could change box color, it could send messages, it could change text.
# 
# Other option is to send stuff over message queue to webcam like get_gesture which would trigger
# webcam -> segmentor -> classifier -> validator -> control pipeline.
# During pipeline control could update send webcam status updates on message queue.
# Webcam should then be refactored. #

class Control():
    def __init__(self):
        broker = "rabbitmq"
        logging.info(f"Starting message queues")
        self.webcam_reciever = MessageQueue(broker, "webcam-control")
        self.webcam_sender = MessageQueue(broker, "control-webcam")
        self.segmentor = MessageQueue(broker, "control-segmentor")
        self.classifier = MessageQueue(broker, "control-classifier")
        self.validator_sender = MessageQueue(broker, "control-validator")
        self.validator_reciever = MessageQueue(broker, "validator-control")
        self.robot_sender = MessageQueue(broker, "control-robot")
        self.robot_reciever = MessageQueue(broker, "robot-control")

        self.use_validator = False
        logging.info(f"Use validator = {self.use_validator}")

        self.classifier_status = ""
        self.webcam_status = ""
        self.segmentor_status = ""
        self.validator_status = ""
        self.robot_status = ""
        self.webcam_command = ""
        self.robot_command = ""
        self.classification = ""
        self.system_status = "Starting"

    def control_cycle(self):
        wc_method, wc_props, wc_body = self.webcam_reciever.get_msg() 
        self.webcam_callback(None, wc_method, wc_props, wc_body)
        sg_method, sg_props, sg_body = self.segmentor.get_msg()
        self.segmentor_callback(None, sg_method, sg_props, sg_body)
        cl_method, cl_props, cl_body = self.classifier.get_msg()
        self.classifier_callback(None, cl_method, cl_props, cl_body)
        val_method, val_props, val_body = self.validator_reciever.get_msg()
        self.validator_callback(None, val_method, val_props, val_body)
        rob_method, rob_props, rob_body = self.robot_reciever.get_msg()
        self.robot_callback(None, rob_method, rob_props, rob_body)
        self.update_system()
        self.message_segmentor()
        self.message_classifier()
        self.message_validator()
        self.message_robot()
        self.message_weacam()
        return
    
    def update_system(self):
        logging.info("STATUS UPDATE")
        logging.info(self.webcam_command)
        logging.info(self.system_status)
        logging.info(self.webcam_status)
        logging.info(self.segmentor_status)
        logging.info(self.classifier_status)
        logging.info(self.validator_status)
        logging.info()
        return
    
    def reset_status(self):
        self.classifier_status = ""
        self.webcam_status = ""
        self.segmentor_status = ""
        self.robot_status = ""
        self.webcam_command = ""
        self.system_status = ""

    def classifier_callback(self, ch, method, properties, body):
        if method != None:
            # Classifier status changed
            # Possible classifier statuses: image recieved, classifing, waiting for validation,
            # validation failed, validated
            self.classifier_status = body["status"]
            if self.classifier_status == "Classified":
                self.system_status = f"Gesture classified as Class {body["result"]}"
                self.classification = body["result"]
                self.robot_command = "Move"
                if self.use_validator:
                    msg = {
                        "msg" : body["msg"],
                        "img" : body["img"]
                    }
                    self.validator_sender.add_msg(msg)
                else:
                    self.reset_status()
                    self.webcam_command = "Capture"
                    self.classifier_status = "Classified"
                    self.system_status = f"Class {body["result"]}, New Capture started"

            elif self.classifier_status == "Image_recieved":
                self.system_status = "Classifing capture"

            return
        
    def validator_callback(self, ch, method, properties, body):
        if method != None:
            # Validator status changed
            # Possible validator sstatuses: image text recieved, validation failed, 
            # validation success#
            self.validator_status = body["status"]
            if self.validator_status == "Validated" and self.webcam_status == "Capture_made":
                self.reset_status()
                self.webcam_command = "Capture"
                self.system_status = "New Capture started"
                self.validator_status = "Image_validated"
                self.robot_command = "Move"

            return
        
    def robot_callback(self, ch, method, properties, body):
        if method != None:
            # Robot status changed
            # Possible robot status: action recieved, action started, action done#
            self.robot_status = body["status"]
            return
    
    def segmentor_callback(self, ch, method, properties, body):
        if method != None:
            # segmentor status changed
            # Possible segmentor statuses: image recieved, mask ready 
            # Could check if segmentation has smart amount of non black pixels and get the pixel value
            # Dont have to do the analysis in the classifier#
            self.segmentor_status = body["status"]
            return
    
    def webcam_callback(self, ch, method, properties, body):
        if method != None:
            # Webcam status changed
            # Possible webcam status: Capture made, Capture requested, User ready
            msg = body["status"]
            self.webcam_status = msg
            
    def message_classifier(self):
        return 
    
    def message_segmentor(self):
        return
    
    def message_weacam(self):
        # Status changes in the system are relayed to the operator with text added to the webcam screen 
        # #
        print("send message")
        message = {"command" : self.webcam_command,
                   "system" : self.system_status,
                   "webcam" : self.webcam_status,
                   "segmentor" : self.segmentor_status,
                   "classifier" : self.classifier_status,
                   "validator" : self.validator_status,
                   "robot" : self.robot_status}
        self.webcam_sender.add_msg(message)
        self.webcam_command = ""
        return 
    
    def message_robot(self):
        if self.robot_command == "Move":
            data = {"msg" : f"Class {self.classification}"}
            self.robot_sender.add_msg(data)
            self.robot_command = ""
        return
    
    def message_validator(self):
        return

if __name__ == "__main__":
    logging.info("---------------\n---------------\n---------------\n")
    time.sleep(5)
    state_machine = Control()
    logging.info("Start")
    while True:
        state_machine.control_cycle()
        time.sleep(1)
