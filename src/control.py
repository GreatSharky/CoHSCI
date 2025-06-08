import time
from messageq import MessageQueue

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
        self.webcam = MessageQueue("control-webcam")
        self.segmentor = MessageQueue("control-segmentor")
        self.classifier = MessageQueue("control-classifier")
        self.validator = MessageQueue("control-validator")
        self.robot = MessageQueue("control-robot")
        
        self.classifier_status = ""
        self.webcam_status = ""
        self.segmentor_status = ""
        self.validator_status = ""
        self.robot_status = ""
        self.system_status = ""
        self.do_capture = False

    def control_cycle(self):
        wc_method, wc_props, wc_body = self.webcam.get_msg() 
        self.webcam_callback(None, wc_method, wc_props, wc_body)
        sg_method, sg_props, sg_body = self.segmentor.get_msg()
        self.segmentor_callback(None, sg_method, sg_props, sg_body)
        cl_method, cl_props, cl_body = self.classifier.get_msg()
        self.classifier_callback(None, cl_method, cl_props, cl_body)
        val_method, val_props, val_body = self.validator.get_msg()
        self.validator_callback(None, val_method, val_props, val_body)
        rob_method, rob_props, rob_body = self.robot.get_msg()
        self.robot_callback(None, rob_method, rob_props, rob_body)
        self.update_system()
        self.message_segmentor()
        self.message_classifier()
        self.message_validator()
        self.message_robot()
        self.message_weacam()
        return
    
    def update_system(self):
        return

    def classifier_callback(self, ch, method, properties, body):
        if method != None:
            # Classifier status changed
            # Possible classifier statuses: image recieved, classifing, waiting for validation,
            # validation failed, validated
            self.segmentor_status = body.decode("utf-8")
            return
        
    def validator_callback(self, ch, method, properties, body):
        if method != None:
            # Validator status changed
            # Possible validator sstatuses: image text recieved, validation failed, 
            # validation success#
            return
        
    def robot_callback(self, ch, method, properties, body):
        if method != None:
            # Robot status changed
            # Possible robot status: action recieved, action started, action done#
            return
    
    def segmentor_callback(self, ch, method, properties, body):
        if method != None:
            # segmentor status changed
            # Possible segmentor statuses: image recieved, mask ready 
            # Could check if segmentation has smart amount of non black pixels and get the pixel value
            # Dont have to do the analysis in the classifier#
            self.segmentor_status = body.decode("utf-8")
            return
    
    def webcam_callback(self, ch, method, properties, body):
        if method != None:
            # Webcam status changed
            # Possible webcam status: Capture made, Capture requested, User ready
            msg = body.decode("utf-8")
            self.webcam_status = msg
            
    def message_classifier(self):
        return 
    
    def message_segmentor(self):
        return
    
    def message_weacam(self):
        # Status changes in the system are relayed to the operator with text added to the webcam screen 
        # #
        print("send message")
        message = {"state" : self.system_status,
                   "webcam" : self.webcam_status,
                   "segmentor" : self.segmentor_status,
                   "classifier" : self.classifier_status,
                   "validator" : self.validator_status,
                   "robot" : self.robot_status}
        self.webcam.add_msg(message)
        return 
    
    def message_robot(self):
        return
    
    def message_validator(self):
        return

if __name__ == "__main__":
    state_machine = Control()
    while True:
        x = state_machine.control_cycle()
        time.sleep(1)
        

