import cv2
import time
import logging
from pathlib import Path
from messageq import MessageQueue
from settings import config

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

class Control():
    def __init__(self):
        logging.info("----\n----\n----\nStart control")
        logging.info(f"Config: {config["control"]}")
        self.webcam_reciever = MessageQueue("webcam-control")
        self.webcam_sender = MessageQueue("control-webcam")
        self.segmentor_sender = MessageQueue("control-segmentor")
        self.segmentor_reciever = MessageQueue("segmentor-control")
        self.classifier_sender = MessageQueue("control-classifier")
        self.classifier_reciever = MessageQueue("classifier-control")
        self.validator_sender = MessageQueue("control-validator")
        self.validator_reciever = MessageQueue("validator-control")
        self.robot_sender = MessageQueue("control-robot")
        self.robot_reciever = MessageQueue("robot-control")

        self.use_validator = config["control"]["validate"] # Add to config
        logging.info(f"Use validation: {self.use_validator}")
        self.use_segmentation = config["control"]["segment"] # Add to config
        logging.info(f"Use segmentation: {self.use_segmentation}")
        self.save_captures = True
        self.img_name = 1

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
        sg_method, sg_props, sg_body = self.segmentor_reciever.get_msg()
        self.segmentor_callback(None, sg_method, sg_props, sg_body)
        cl_method, cl_props, cl_body = self.classifier_reciever.get_msg()
        self.classifier_callback(None, cl_method, cl_props, cl_body)
        val_method, val_props, val_body = self.validator_reciever.get_msg()
        self.validator_callback(None, val_method, val_props, val_body)
        rob_method, rob_props, rob_body = self.robot_reciever.get_msg()
        self.robot_callback(None, rob_method, rob_props, rob_body)
        self.message_segmentor()
        self.message_classifier()
        self.message_validator()
        self.message_robot()
        self.message_weacam()
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
            logging.info(f"Classifier msg recieved: {body}")
            # Classifier status changed
            # Possible classifier statuses: image recieved, classifing, waiting for validation,
            # validation failed, validated
            self.classifier_status = body["status"]
            if self.classifier_status == "Classified":
                self.system_status = f"Gesture classified as Class {body["result"]}"
                self.classification = body["result"]
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
                    self.robot_command = "Move"

            elif self.classifier_status == "Image_recieved":
                self.system_status = "Classifing capture"

            return
        
    def validator_callback(self, ch, method, properties, body):
        if method != None:
            logging.info(f"Validator msg recieved: {body}")
            # Validator status changed
            # Possible validator sstatuses: image text recieved, validation failed, 
            # validation success#
            self.validator_status = body["status"]
            if self.validator_status == "Validated" and self.webcam_status == "Capture_made":
                if body["result"].isnumeric() and int(body["result"]) > 95: # Add barrier value to config
                    self.reset_status()
                    self.webcam_command = "Capture"
                    self.system_status = "New Capture started"
                    self.validator_status = "Image_validated"
                    self.robot_command = "Move"
                else:
                    self.reset_status()
                    self.webcam_command = "Capture"
                    self.system_status = "New Capture started"
                    self.validator_status = "Validation_failed"

            return
        
    def robot_callback(self, ch, method, properties, body):
        if method != None:
            logging.info(f"Robot msg recieved: {body}")
            # Robot status changed
            # Possible robot status: action recieved, action started, action done#
            self.robot_status = body["status"]
            return
    
    def segmentor_callback(self, ch, method, properties, body):
        if method != None:
            logging.info(f"Segmentor msg recieved: {body}")
            # segmentor status changed
            # Possible segmentor statuses: image recieved, mask ready 
            # Could check if segmentation has smart amount of non black pixels and get the pixel value
            # Dont have to do the analysis in the classifier#
            self.segmentor_status = body["status"]
            if self.segmentor_status == "Segment_done":
                data = {"img" : body["img"]}
                if self.save_captures:
                    cap_path = log_path / "segment"
                    cap_path.mkdir(exist_ok=True)
                    cap_file = cap_path / f"{self.img_name}.jpg"
                    logging.info(f"Storing segmentation {cap_file}")
                    cv2.imwrite(cap_file, body["img"])
                    self.img_name += 1
                self.classifier_sender.add_msg(data.copy())
                self.webcam_sender.add_msg(data.copy())
            return
    
    def webcam_callback(self, ch, method, properties, body):
        if method != None:
            logging.info(f"Webcam msg recieved: {body}")
            # Webcam status changed
            # Possible webcam status: Capture made, Capture requested, User ready
            msg = body["status"]
            self.webcam_status = msg
            if msg == "Capture_made":
                data = {"img" : body["img"]}
                if self.save_captures:
                    cap_path = log_path / "capture"
                    cap_path.mkdir(exist_ok=True)
                    cap_file = cap_path / f"{self.img_name}.jpg"
                    logging.info(f"Storing capture {cap_file}")
                    cv2.imwrite(cap_file, body["img"])
                if self.use_segmentation == True:
                    self.segmentor_sender.add_msg(data)
                else:
                    self.img_name += 1
                    self.classifier_sender.add_msg(data)
            
    def message_classifier(self):
        return 
    
    def message_segmentor(self):
        return
    
    def message_weacam(self):
        # Status changes in the system are relayed to the operator with text added to the webcam screen 
        # #
        message = {
            "command" : self.webcam_command,
            "system" : self.system_status,
            "webcam" : self.webcam_status,
            "segmentor" : self.segmentor_status,
            "classifier" : self.classifier_status,
            "validator" : self.validator_status,
            "robot" : self.robot_status
            }
        self.webcam_sender.add_msg(message)
        self.webcam_command = ""
        return 
    
    def message_robot(self):
        if self.robot_command == "Move":
            data = {"msg" : self.classification}
            logging.info(f"Sending robot command: {data}")
            self.robot_sender.add_msg(data)
            self.robot_command = ""
        return
    
    def message_validator(self):
        return

if __name__ == "__main__":
    state_machine = Control()
    while True:
        state_machine.control_cycle()
        time.sleep(config["control"]["poll_rate"])
